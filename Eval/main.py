# Bon à savoir :
# Une requête GET = quelqu’un demande des données à ton API (= moyen pour deux programmes de communiquer entre eux.) via une URL


from typing import List, Optional, Dict
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, Session, create_engine, select, Relationship
from sqlalchemy import Column, DateTime

# Base de données

DATABASE_URL = "sqlite:///./chat.db"
engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session


# Modèles de liaison (Many-to-Many)

class ConversationParticipant(SQLModel, table=True):
    conversation_id: Optional[int] = Field(
        default=None, foreign_key="conversation.id", primary_key=True
    )
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )

# Modèles User

class UserBase(SQLModel):
    name: str
    email: str
    is_active: bool = True


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversations: List["Conversation"] = Relationship(
        back_populates="participants", link_model=ConversationParticipant
    )
    messages: List["Message"] = Relationship(back_populates="sender")


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int


class UserUpdate(SQLModel):
    name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None

# Modèles Conversation


class ConversationBase(SQLModel):
    name: Optional[str] = None   # Nom du groupe (None si conversation privée)
    is_group: bool = False


class Conversation(ConversationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow)
    )
    participants: List["User"] = Relationship(
        back_populates="conversations", link_model=ConversationParticipant
    )
    messages: List["Message"] = Relationship(back_populates="conversation")


class ConversationCreate(ConversationBase):
    participant_ids: List[int]


class ConversationRead(ConversationBase):
    id: int
    created_at: datetime
    participants: List[UserRead] = []


# Modèles Message

class MessageBase(SQLModel):
    content: str


class Message(MessageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    sender_id: int = Field(foreign_key="user.id")
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow)
    )
    is_read: bool = False

    conversation: Optional[Conversation] = Relationship(back_populates="messages")
    sender: Optional[User] = Relationship(back_populates="messages")


class MessageCreate(MessageBase):
    conversation_id: int
    sender_id: int


class MessageRead(MessageBase):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: Optional[str] = None
    timestamp: datetime
    is_read: bool


# Gestionnaire WebSocket (temps réel)

class ConnectionManager:
    def __init__(self):
        # { conversation_id: { user_id: WebSocket } }
        self.active: Dict[int, Dict[int, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conv_id: int, user_id: int):
        await websocket.accept()
        self.active.setdefault(conv_id, {})[user_id] = websocket

    def disconnect(self, conv_id: int, user_id: int):
        if conv_id in self.active:
            self.active[conv_id].pop(user_id, None)

    async def broadcast(self, conv_id: int, data: dict, exclude_user: int = None):
        for uid, ws in list(self.active.get(conv_id, {}).items()):
            if uid != exclude_user:
                try:
                    await ws.send_json(data)
                except Exception:
                    pass


manager = ConnectionManager()

# Application

app = FastAPI(title="WhatsApp-like API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# Routes — Utilisateurs

@app.get("/", tags=["health"])
def root():
    return {"message": "API WhatsApp-like v2 🚀"}


@app.post("/users", response_model=UserRead, tags=["users"])
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # Vérifier l'unicité de l'email
    existing = session.exec(select(User).where(User.email == user.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    db_user = User.from_orm(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.get("/users", response_model=List[UserRead], tags=["users"])
def list_users(session: Session = Depends(get_session)):
    return session.exec(select(User)).all()


@app.get("/users/{user_id}", response_model=UserRead, tags=["users"])
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


@app.patch("/users/{user_id}", response_model=UserRead, tags=["users"])
def update_user(user_id: int, updates: UserUpdate, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    for field, val in updates.dict(exclude_unset=True).items():
        setattr(user, field, val)
    session.commit()
    session.refresh(user)
    return user

# Routes — Conversations

@app.post("/conversations", response_model=ConversationRead, tags=["conversations"])
def create_conversation(conv: ConversationCreate, session: Session = Depends(get_session)):
    if len(conv.participant_ids) < 2:
        raise HTTPException(status_code=400, detail="Au moins 2 participants requis")

    # Récupérer les users
    users = [session.get(User, uid) for uid in conv.participant_ids]
    if any(u is None for u in users):
        raise HTTPException(status_code=404, detail="Un ou plusieurs utilisateurs introuvables")

    db_conv = Conversation(name=conv.name, is_group=conv.is_group)
    db_conv.participants = users
    session.add(db_conv)
    session.commit()
    session.refresh(db_conv)
    return db_conv


@app.get("/conversations", response_model=List[ConversationRead], tags=["conversations"])
def list_conversations(session: Session = Depends(get_session)):
    return session.exec(select(Conversation)).all()


@app.get("/conversations/{conv_id}", response_model=ConversationRead, tags=["conversations"])
def get_conversation(conv_id: int, session: Session = Depends(get_session)):
    conv = session.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    return conv


@app.get("/users/{user_id}/conversations", response_model=List[ConversationRead], tags=["conversations"])
def user_conversations(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user.conversations


@app.post("/conversations/{conv_id}/participants/{user_id}", tags=["conversations"])
def add_participant(conv_id: int, user_id: int, session: Session = Depends(get_session)):
    conv = session.get(Conversation, conv_id)
    user = session.get(User, user_id)
    if not conv or not user:
        raise HTTPException(status_code=404, detail="Conversation ou utilisateur introuvable")
    if user in conv.participants:
        raise HTTPException(status_code=400, detail="Déjà participant")
    conv.participants.append(user)
    session.commit()
    return {"message": f"{user.name} ajouté à la conversation"}


@app.delete("/conversations/{conv_id}/participants/{user_id}", tags=["conversations"])
def remove_participant(conv_id: int, user_id: int, session: Session = Depends(get_session)):
    conv = session.get(Conversation, conv_id)
    user = session.get(User, user_id)
    if not conv or not user:
        raise HTTPException(status_code=404, detail="Introuvable")
    if user not in conv.participants:
        raise HTTPException(status_code=400, detail="Pas participant")
    conv.participants.remove(user)
    session.commit()
    return {"message": f"{user.name} retiré de la conversation"}


# Routes — Messages

@app.post("/messages", response_model=MessageRead, tags=["messages"])
async def send_message(msg: MessageCreate, session: Session = Depends(get_session)):
    # Vérifier que la conversation et l'expéditeur existent
    conv = session.get(Conversation, msg.conversation_id)
    sender = session.get(User, msg.sender_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    if not sender:
        raise HTTPException(status_code=404, detail="Expéditeur introuvable")

    # Vérifier que l'expéditeur est participant
    if sender not in conv.participants:
        raise HTTPException(status_code=403, detail="L'expéditeur n'est pas dans cette conversation")

    db_msg = Message(
        content=msg.content,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
    )
    session.add(db_msg)
    session.commit()
    session.refresh(db_msg)

    result = MessageRead(
        id=db_msg.id,
        content=db_msg.content,
        conversation_id=db_msg.conversation_id,
        sender_id=db_msg.sender_id,
        sender_name=sender.name,
        timestamp=db_msg.timestamp,
        is_read=db_msg.is_read,
    )

    # Diffuser via WebSocket
    await manager.broadcast(
        msg.conversation_id,
        result.dict(),
        exclude_user=msg.sender_id,
    )

    return result


@app.get("/conversations/{conv_id}/messages", response_model=List[MessageRead], tags=["messages"])
def get_messages(
    conv_id: int,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    conv = session.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")

    messages = session.exec(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.timestamp)
        .offset(offset)
        .limit(limit)
    ).all()

    result = []
    for m in messages:
        sender = session.get(User, m.sender_id)
        result.append(MessageRead(
            id=m.id,
            content=m.content,
            conversation_id=m.conversation_id,
            sender_id=m.sender_id,
            sender_name=sender.name if sender else None,
            timestamp=m.timestamp,
            is_read=m.is_read,
        ))
    return result


@app.patch("/messages/{msg_id}/read", tags=["messages"])
def mark_as_read(msg_id: int, session: Session = Depends(get_session)):
    msg = session.get(Message, msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message introuvable")
    msg.is_read = True
    session.commit()
    return {"message": "Marqué comme lu"}


@app.delete("/messages/{msg_id}", tags=["messages"])
def delete_message(msg_id: int, session: Session = Depends(get_session)):
    msg = session.get(Message, msg_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message introuvable")
    session.delete(msg)
    session.commit()
    return {"message": "Message supprimé"}

# WebSocket — Temps réel

@app.websocket("/ws/{conv_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, conv_id: int, user_id: int):
    """
    Connexion : ws://localhost:8000/ws/{conversation_id}/{user_id}
    Les messages envoyés ici sont broadcast à tous les autres participants.
    """
    await manager.connect(websocket, conv_id, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            # On attend { "content": "..." }
            content = data.get("content", "").strip()
            if not content:
                continue

            with Session(engine) as session:
                sender = session.get(User, user_id)
                db_msg = Message(
                    content=content,
                    conversation_id=conv_id,
                    sender_id=user_id,
                )
                session.add(db_msg)
                session.commit()
                session.refresh(db_msg)

                payload = {
                    "id": db_msg.id,
                    "content": db_msg.content,
                    "conversation_id": conv_id,
                    "sender_id": user_id,
                    "sender_name": sender.name if sender else "Inconnu",
                    "timestamp": db_msg.timestamp.isoformat(),
                    "is_read": False,
                }

            # Envoyer à l'expéditeur en confirmation
            await websocket.send_json({**payload, "type": "sent"})
            # Diffuser aux autres
            await manager.broadcast(conv_id, {**payload, "type": "received"}, exclude_user=user_id)

    except WebSocketDisconnect:
        manager.disconnect(conv_id, user_id)
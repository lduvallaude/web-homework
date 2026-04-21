# Bon à savoir :
# Une requête GET = quelqu’un demande des données à ton API (= moyen pour deux programmes de communiquer entre eux.) via une URL

from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI
from sqlmodel import SQLModel, Field


app = FastAPI()

# User

class UserBase(SQLModel):
    name: str
    email: str
    is_active: bool = True


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: int

# Conversation

class ConversationBase(SQLModel):
    is_group: bool = False


class Conversation(ConversationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ConversationCreate(ConversationBase):
    participant_ids: List[int]


class ConversationRead(ConversationBase):
    id: int
    participant_ids: List[int]

# Message

class MessageBase(SQLModel):
    content: str


class Message(MessageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int
    sender_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MessageCreate(MessageBase):
    conversation_id: int
    sender_id: int


class MessageRead(MessageBase):
    id: int
    conversation_id: int
    sender_id: int
    timestamp: datetime


@app.get("/")
def root():
    return {"message": "API WhatsApp-like en cours 🚀"}


@app.post("/users", response_model=UserRead)
def create_user(user: UserCreate):
    return {**user.dict(), "id": 1}


@app.post("/conversations", response_model=ConversationRead)
def create_conversation(conv: ConversationCreate):
    return {**conv.dict(), "id": 1}


@app.post("/messages", response_model=MessageRead)
def create_message(msg: MessageCreate):
    return {
        **msg.dict(),
        "id": 1,
        "timestamp": datetime.utcnow()
    }
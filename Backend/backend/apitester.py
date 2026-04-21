from pathlib import Path

import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# -----------------
# CORS setup (it's black magic - keep as-is)
# -----------------
origins = [
    "*"  # allow all origins for simplicity (not recommended for production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],  # allow all HTTP methods
    allow_headers=["*"],  # allow all headers
)

# -----------------
# CSV data
# -----------------
# spot the data folder
data = Path(__file__).parent.absolute() / 'data'

# load the CSV data into pandas dataframes
associations_df = pd.read_csv(data / 'associations_etudiantes.csv')
evenements_df = pd.read_csv(data / 'evenements_associations.csv')

# -----------------
# API Routes
# -----------------

@app.get("/api/alive")
def read_root():
    return {"message": "Alive"}

@app.get("/api/associations")
def get_associations():
    return associations_df.id.tolist()

@app.get("/api/association/{association_id}")
def get_association(association_id: int):
    association = associations_df[associations_df['id'] == association_id]
    if association.empty:
        raise HTTPException(status_code=404, detail="Association not found")
    return association.iloc[0].to_dict()



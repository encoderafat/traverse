# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import paths, challenges, progress
from models import Base
from db import engine


app = FastAPI(title="Traverse API")

Base.metadata.create_all(bind=engine)  # or use Alembic instead

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(paths.router)
app.include_router(challenges.router)
app.include_router(progress.router)

@app.get("/")
def root():
    return {"status": "ok", "service": "traverse-backend"}
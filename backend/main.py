# main.py
from fastapi import FastAPI
from routes import paths, challenges, progress
from models import Base
from db import engine


app = FastAPI(title="Traverse API")

Base.metadata.create_all(bind=engine)  # or use Alembic instead

app.include_router(paths.router)
app.include_router(challenges.router)
app.include_router(progress.router)
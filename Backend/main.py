# backend/main.py

from fastapi import FastAPI
from database import engine, Base

# This one line creates all tables in Postgres based on our models
# It's smart: if a table already exists, it skips it
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="LeadMind API",
    description="Autonomous AI outbound sales agent",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "LeadMind API"}


# Root endpoint
@app.get("/")
def root():
    return {"message": "LeadMind is running"}
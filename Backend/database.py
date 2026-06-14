# backend/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os


load_dotenv()

# Read the database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the "engine" — this is the actual connection to Postgres
# pool_pre_ping=True means: test connection before using it (handles dropped connections)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal is a factory — every time you call SessionLocal() 
# you get a fresh database session (like a fresh conversation with the DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class all our database models will inherit from
# It's what makes SQLAlchemy aware of our tables
Base = declarative_base()


# This is a "dependency" — FastAPI will call this for every request
# that needs DB access. It opens a session, runs the request, then
# always closes the session (even if an error occurs — that's what
# try/finally guarantees)
def get_db():
    db = SessionLocal()
    try:
        yield db        # "yield" makes this a generator — FastAPI handles the lifecycle
    finally:
        db.close()
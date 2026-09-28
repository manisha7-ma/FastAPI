# `create_engine` creates the connection interface between SQLAlchemy and the  database. 
#`DeclarativeBase` is the base class for defining ORM model classes,
# while `sessionmaker` creates database sessions used to query and modify data.
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"  # SQLite database URL

engine= create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# Creates the SQLAlchemy connection interface for the SQLite database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Creates a local database session for each request.
    
# Shared declarative base for ORM models; inheriting from it lets SQLAlchemy
# register each model's table and metadata.
class Base(DeclarativeBase):
    pass

def get_db():
    # Create a SessionLocal session for this request, yield it for use, and
    # close it when the request ends.
    db = SessionLocal()  # Create a new database session
    try:
        yield db  # Yield the session to be used in the request
    finally:
        db.close()  # Close the session after the request is completed

        
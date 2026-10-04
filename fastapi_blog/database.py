# `create_engine` creates the connection interface between SQLAlchemy and the  database. 
#`DeclarativeBase` is the base class for defining ORM model classes,
# while `sessionmaker` creates database sessions used to query and modify data.

#The below import were used in synchronous database operations, but we are using asynchronous operations in our FastAPI application.

#from sqlalchemy import create_engine
#from sqlalchemy.orm import DeclarativeBase, sessionmaker


#Async Allows us to use asynchronous database operations in FastAPI, 
#enabling better performance and scalability for web applications
#that handle many concurrent requests.





#The below imports are used for asynchronous database operations in FastAPI, allowing for better performance and scalability in handling concurrent requests.
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession,aync_sessionmaker
from sqlalchemy.orm import DeclarativeBase


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./blog.db"  # SQLite database URL

engine= create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# Creates the SQLAlchemy connection interface for the SQLite database.
AsyncSessionLocal = aync_sessionmaker(
    #autocommit=False, autoflush=False, bind=engine)
    engine,class_=AsyncSession, expire_on_commit=False
)
# Creates a local database session for each request.
    
# Shared declarative base for ORM models; inheriting from it lets SQLAlchemy
# register each model's table and metadata.
class Base(DeclarativeBase):
    pass

async def get_db():
    # Create an AsyncSessionLocal session for this request, yield it for use, and
    # close it when the request ends.
    db = AsyncSessionLocal()  # Create a new database session
    try:
        yield db  # Yield the session to be used in the request
    finally:
        await db.close()  # Close the session after the request is completed

        
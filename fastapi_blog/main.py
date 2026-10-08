from fastapi import FastAPI, HTTPException, Request, status,Depends
from fastapi.staticfiles import StaticFiles
# for HTML and JSON responses
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import PostResponse,PostCreate,UserCreate, UserResponse,PostUpdate,UserUpdate

from  typing import Annotated
from sqlalchemy import select 
from sqlalchemy.orm import Session
from database import get_db,Base,engine
import models

#Async Pacage for Asynchronous programming in Python, allowing for concurrent execution of tasks.
#for the lifespan event handler to create the database tables when the application starts up.
from contextlib import asynccontextmanager

from fastapi.exception_handlers import request_validation_exception_handler, http_exception_handler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
#selectinload is a loading strategy in SQLAlchemy that allows for efficient retrieval
#of related objects in a single query, reducing the number of database round-trips and improving
#performance when accessing related data.




#creating Database Table 
#Base.metadata.create_all(bind=engine)
# looks into all of the model and creates the tables in the database if they don't exist already.
#it is idempotent, meaning that it can be called multiple times without causing any issues or duplicating tables.

#lifespan event handler to create the database tables when the application starts up.


@asynccontextmanager
async def lifespan(app: FastAPI):
    #Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    #Shutdown 
    await engine.dispose()
 
app=FastAPI(lifespan=lifespan)
    


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")


templates=Jinja2Templates(directory="templates")

#Lazy loading is not allowed in asynchronous context, so we need to use selectinload to load the related objects in a single query.
#For example getting author of the post, we can use selectinload to load the author of the post in a single query instead of making multiple queries to the database.




#This was the temporary creation of the API using static data, but now we will be using the database to store the data and retrieve it from the database.



# posts: list[dict] = [
#     {
#         "id": 1,
#         "author": "Corey Schafer",
#         "title": "FastAPI is Awesome",
#         "content": "This framework is really easy to use.",
#         "date_posted": "April 20, 2025",
#     },
#     {
#         "id": 2,
#         "author": "Jane Doe",
#         "title": "Python is Great for Web Development",
#         "content": "Python is a great language for web development.",
#         "date_posted": "April 21, 2025",
#     },
# ]

# #calling API response with HTML response

# @app.get("/htmlresponse", response_class=HTMLResponse, include_in_schema=False)
# @app.get("/sameroute", response_class=HTMLResponse, include_in_schema=False)
# def home():
#     return f"<h1>{posts[0]['title']}</h1>"

# #calling API response using Jinja2 template
# @app.get("/", include_in_schema=False)
# def home(request: Request):
#     return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home Page"})


# @app.get("/posts/{post_id}", include_in_schema=False)
# def get_post_page(request: Request, post_id: int):
#     for post in posts:
#         title = post["title"][0:50]  # Get the first 10 characters of the title
#         if post["id"] == post_id:
#             return templates.TemplateResponse(request, "post.html", {"post": post, "title": title})
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


# @app.get("/api/posts", response_model=list[PostResponse], include_in_schema=True)
# def get_posts():
#     return posts    


# # `post_id` is a path parameter, and the `int` annotation type-casts it from the URL string.
# @app.get("/api/posts/{post_id}", response_model=PostResponse, include_in_schema=True)
# def get_post(post_id: int):
#     for post in posts:
#         if post["id"]==post_id:
#             return post
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


#  #creating a Post reponse to create a new Post
# @app.post("/api/createposts", response_model=PostResponse, include_in_schema=True,status_code=status.HTTP_201_CREATED)
# def create_post(post: PostCreate):    
#     new_post = post.dict()
#     new_post["id"] = len(posts) + 1
#     new_post["date_posted"] = "April 22, 2025"  # You can set the current date here 
#     new_post["title"] = post.title
#     new_post["content"] = post.content
#     new_post["author"] = post.author
#     posts.append(new_post)
#     return new_post






#Creating API endpoints to create and retrieve posts from the database.
@app.get("/api/getposts",response_model=list[PostResponse],include_in_schema=True)
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)))    
    postList = result.scalars().all()
    if not postList:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts found")
    return postList

#Creating an API endpoint to create a new post and store it in the database.
@app.post("/api/posts",response_model=PostResponse,include_in_schema=True,status_code=status.HTTP_201_CREATED   )
async def create_posts(post:PostCreate,db:Annotated[AsyncSession, Depends(get_db)]):
    user_result = await db.execute(select(models.User).where(models.User.id==post.user_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    post_result = await db.execute(select(models.Post).where(models.Post.title==post.title))
    if post_result.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post with this title already exists")
    new_post=models.Post(**post.model_dump())
    db.add(new_post)
    await db.commit()
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == new_post.id)
        .options(selectinload(models.Post.author))
    )
    #we can also do  result=await (new_post,attribute_names=["author"]) to get the author of the post,
    #but this is not recommended as it will make multiple queries to the database.
    return result.scalars().one()



#Creating an API endpoint to retrieve a specific post by ID from the database.
@app.get("/api/posts/{post_id}",response_model=PostResponse,include_in_schema=True)
async def get_post(post_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id==post_id).options(selectinload(models.Post.author)))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post

#The Patch method is used to update a post in the database. 
#It takes the post ID and the updated post data as input, 
#and updates the corresponding post in the database.
# If the post is not found, it raises a 404 error. After updating, it commits the changes to the database and returns the updated post.


@app.patch("/api/posts/{post_id}", response_model=PostResponse, include_in_schema=True)
#sending PostUpdate schema to update the post in the database. Cause the PostUpdate schema has optional fields,
#it allows for partial updates of the post.
async def update_post(post_id: int, post_update: PostUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == post_id)
        .options(selectinload(models.Post.author))
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # Update the post with the new values 
    # the Exclude_unset=True option ensures that only the fields that are provided in the request will be updated,
    # leaving the other fields unchanged.
    for key, value in post_update.model_dump(exclude_unset=True).items():
        setattr(post, key, value)

    await db.commit()
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == post_id)
        .options(selectinload(models.Post.author))
    )
    return result.scalars().one()

@app.put("/api/posts/{post_id}",response_model=PostResponse, include_in_schema=True)
async def replace_post(post_id:int,post_update:PostCreate,db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id==post_id).options(selectinload(models.Post.author)))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    user_result = await db.execute(select(models.User).where(models.User.id == post_update.user_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {post_update.user_id} not found; create that user before assigning the post",
        )
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.title==post_update.title,models.Post.id!=post_id))
    duplicate_post = result.scalars().first()
    if duplicate_post:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A post with this title already exists")
    for key, value in post_update.model_dump().items():
        setattr(post, key, value)
    await db.commit()
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == post_id)
        .options(selectinload(models.Post.author))
    )
    return result.scalars().one()

#Delete API endpoint to delete a post by ID from the database.
@app.delete("/api/posts/{post_id}",status_code=status.HTTP_204_NO_CONTENT,include_in_schema=True)
async def delete_post(post_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id==post_id).options(selectinload(models.Post.author)))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    await db.delete(post)
    await db.commit()
    return {"detail": "Post deleted successfully"}    

#API to get Post Created by user_id 
@app.get("/api/users/{user_id}/posts",response_model=list[PostResponse],include_in_schema=True)
async def get_posts_by_user(user_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
        .options(
            selectinload(models.User.posts).selectinload(models.Post.author)
        )
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    posts_by_user = user.posts
    if not posts_by_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts found for this user")
    return posts_by_user





#Creating in the Jinja2 template to display the posts and users in the HTML page with the help of the database.
@app.get("/", include_in_schema=False,name="home")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post).options(selectinload(models.Post.author))
    )
    posts = result.scalars().all()
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home Page"})



# API for it to return per Post 
@app.get("/posts/{post_id}",include_in_schema=False)
async def get_post_page(request:Request,post_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post).where(models.Post.id == post_id).options(selectinload(models.Post.author))
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return templates.TemplateResponse(request, "post.html", {"post": post, "title": post.title})        
   


@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )



   
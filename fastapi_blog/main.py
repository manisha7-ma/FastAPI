from fastapi import FastAPI, HTTPException, Request, status,Depends
from fastapi.staticfiles import StaticFiles
# for HTML and JSON responses
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import PostResponse,PostCreate,UserCreate, UserResponse

from  typing import Annotated
from sqlalchemy import select 
from sqlalchemy.orm import Session
from database import get_db,Base,engine
import models

app=FastAPI()

#creatting Database Table 
Base.metadata.create_all(bind=engine)
# looks into all of the model and creates the tables in the database if they don't exist already.
#it is idempotent, meaning that it can be called multiple times without causing any issues or duplicating tables.
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")


templates=Jinja2Templates(directory="templates")






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




# Creating API endpoints that are using the Database to store and retrieve the data instead of using static data.
#API endpoint to create a new user and store it in the database.
@app.post("/api/users", response_model=UserResponse, include_in_schema=True,status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

#API endpoint to retrieve all users from the database.
@app.get("/api/getusers", response_model=list[UserCreate], include_in_schema=True)
def get_users(db:Session=Depends(get_db)):
    userlist=db.execute(select(models.User)).scalars().all()

    if not userlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")
    return userlist

#API endpoint to retrieve a specific user by ID from the database.
@app.get("/api/users/{user_id}",response_model=UserCreate,include_in_schema=True)
def get_user(user_id:int,db:Session=Depends(get_db)):
    user=db.execute(select (models.User).where (models.User.id==user_id)).scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


#Creating API endpoints to create and retrieve posts from the database.
@app.get("/api/getposts",response_model=list[PostResponse],include_in_schema=True)
def get_posts(db:Session=Depends(get_db)):
    postList=db.execute(select(models.Post)).scalars().all()
    if not postList:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts found")
    return postList

#Creating an API endpoint to create a new post and store it in the database.
@app.post("/api/posts",response_model=PostResponse,include_in_schema=True,status_code=status.HTTP_201_CREATED   )
def create_posts(post:PostCreate,db:Session=Depends(get_db)):
    new_post=models.Post(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

#Creating an API endpoint to retrieve a specific post by ID from the database.
@app.get("/api/posts/{post_id}",response_model=PostResponse,include_in_schema=True)
def get_post(post_id:int,db:Session=Depends(get_db)):
    post=db.execute(select(models.Post).where(models.Post.id==post_id)).scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post

#API to get Post Created by user_id 
@app.get("/api/users/{user_id}/posts",response_model=list[PostResponse],include_in_schema=True)
def get_posts_by_user(user_id:int,db:Session=Depends(get_db)):
    user=db.execute(select(models.User).where(models.User.id==user_id)).scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    posts_by_user=user.posts
    if not posts_by_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No posts found for this user")
    return posts_by_user





#Creating in the Jinja2 template to display the posts and users in the HTML page with the help of the database.
@app.get("/", include_in_schema=False)
def home(request: Request, db: Session = Depends(get_db)):
    posts = db.execute(select(models.Post)).scalars().all()
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home Page"})



# API for it to return per Post 
@app.get("/posts/{post_id}",include_in_schema=False)
def get_post_page(request:Request,post_id:int,db:Session=Depends(get_db)):
    post=db.execute(select(models.Post).where(models.Post.id==post_id)).scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return templates.TemplateResponse(request, "post.html", {"post": post, "title": post.title})



@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )

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
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )

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

   
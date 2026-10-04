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

#Aync Pacage for Asynchronous programming in Python, allowing for concurrent execution of tasks.
from contextlib import asynccontextmanager
from fastapi.exceptions_handlers import request_validation_exception_handler, http_exception_handler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker


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
    if_user_exists = db.execute(select(models.User).where(models.User.username == user.username)).scalars().first()
    if if_user_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username already exists")
    if_email_exists = db.execute(select(models.User).where(models.User.email == user.email)).scalars().first()
    if if_email_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists") 
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

#API endpoint to update a specific user by ID from the database. It takes the user ID and the updated user data as input, and updates the corresponding user in the database. If the user is not found, it raises a 404 error. After updating, it commits the changes to the database and returns the updated user.
@app.patch("/api/users/{user_id}",response_model=UserResponse,include_in_schema=True)
def update_user(user_id:int,user_update:UserUpdate,db:Session=Depends(get_db)):
    user=db.execute(select(models.User).where(models.User.id==user_id)).scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_fields = user_update.dict(exclude_unset=True)
    if "username" in updated_fields:
        username_exists = db.execute(
            select(models.User).where(
                models.User.username == updated_fields["username"],
                models.User.id != user_id,
            )
        ).scalars().first()
        if username_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username already exists")
    if "email" in updated_fields:
        email_exists = db.execute(
            select(models.User).where(
                models.User.email == updated_fields["email"],
                models.User.id != user_id,
            )
        ).scalars().first()
        if email_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    for key, value in updated_fields.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user



#API endpoint to replace a specific user by ID from the database. It takes the user ID and the updated user data as input, and replaces the corresponding user in the database. If the user is not found, it raises a 404 error. After replacing, it commits the changes to the database and returns the updated user.
@app.put("/api/users/{user_id}",response_model=UserResponse,include_in_schema=True)
def replace_user(user_id:int,user_update:UserCreate,db:Session=Depends(get_db)):
    user=db.execute(select(models.User).where(models.User.id==user_id)).scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    updated_fields = user_update.dict(exclude_unset=True)
    if "username" in updated_fields:
        username_exists = db.execute(
            select(models.User).where(
                models.User.username == updated_fields["username"],
                models.User.id != user_id,
            )
        ).scalars().first()
        if username_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username already exists")
    if "email" in updated_fields:
        email_exists = db.execute(
            select(models.User).where(
                models.User.email == updated_fields["email"],
                models.User.id != user_id,
            )
        ).scalars().first()
        if email_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    for key, value in updated_fields.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user




#API endpoint to delete a specific user by ID from the database.
@app.delete("/api/users/{user_id}",status_code=status.HTTP_204_NO_CONTENT,include_in_schema=True)
def delete_user(user_id:int,db:Session=Depends(get_db)):
    user=db.execute(select(models.User).where(models.User.id==user_id)).scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    posts_by_user=db.execute(select(models.Post).where(models.Post.user_id==user_id)).scalars().all()
    db.delete(user)
    db.commit()
    return {"detail": "User deleted successfully"}   



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
    if_user_exists=db.execute(select(models.User).where(models.User.id==post.user_id)).scalars().first()
    if not if_user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if_post_exists=db.execute(select(models.Post).where(models.Post.title==post.title)).scalars().first()
    if if_post_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post with this title already exists")
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

#The Patch method is used to update a post in the database. 
#It takes the post ID and the updated post data as input, 
#and updates the corresponding post in the database.
# If the post is not found, it raises a 404 error. After updating, it commits the changes to the database and returns the updated post.


@app.patch("/api/posts/{post_id}", response_model=PostResponse, include_in_schema=True)
#sending PostUpdate schema to update the post in the database. Cause the PostUpdate schema has optional fields,
#it allows for partial updates of the post.
def update_post(post_id: int, post_update: PostUpdate, db: Session = Depends(get_db)):
    post = db.execute(select(models.Post).where(models.Post.id == post_id)).scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # Update the post with the new values 
    # the Exclude_unset=True option ensures that only the fields that are provided in the request will be updated,
    # leaving the other fields unchanged.
    for key, value in post_update.dict(exclude_unset=True).items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)
    return post

@app.put("/api/posts/{post_id}",response_model=PostResponse, include_in_schema=True)
def replace_post(post_id:int,post_update:PostCreate,db:Session=Depends(get_db)):
    post=db.execute(select(models.Post).where(models.Post.id==post_id)).scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    user=db.execute(select(models.User).where(models.User.id==post_update.user_id)).scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    for key, value in post_update.dict().items():
        setattr(post, key, value)
    db.commit()
    db.refresh(post)
    return post

#Delete API endpoint to delete a post by ID from the database.
@app.delete("/api/posts/{post_id}",status_code=status.HTTP_204_NO_CONTENT,include_in_schema=True)
def delete_post(post_id:int,db:Session=Depends(get_db)):
    post=db.execute(select(models.Post).where(models.Post.id==post_id)).scalars().first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    db.delete(post)
    db.commit()
    return {"detail": "Post deleted successfully"}    

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



   
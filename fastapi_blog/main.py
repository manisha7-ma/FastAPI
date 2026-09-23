from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
#for HTML response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates=Jinja2Templates(directory="templates")
posts: list[dict] = [
    {
        "id": 1,
        "author": "Corey Schafer",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use.",
        "date_posted": "April 20, 2025",
    },
    {
        "id": 2,
        "author": "Jane Doe",
        "title": "Python is Great for Web Development",
        "content": "Python is a great language for web development.",
        "date_posted": "April 21, 2025",
    },
]

#calling API response with HTML response

@app.get("/htmlresponse", response_class=HTMLResponse, include_in_schema=False)
@app.get("/sameroute", response_class=HTMLResponse, include_in_schema=False)
def home():
    return f"<h1>{posts[0]['title']}</h1>"

#calling API response using Jinja2 template
@app.get("/", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home Page"})


@app.get("/posts/{post_id}", include_in_schema=False)
def get_post_page(request: Request, post_id: int):
    for post in posts:
        title = post["title"][0:50]  # Get the first 10 characters of the title
        if post["id"] == post_id:
            return templates.TemplateResponse(request, "post.html", {"post": post, "title": title})
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get("/api/posts")
def get_posts():
    return posts    


# `post_id` is a path parameter, and the `int` annotation type-casts it from the URL string.
@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    for post in posts:
        if post["id"]==post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

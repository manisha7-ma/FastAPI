from fastapi import FastAPI
app=FastAPI()


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


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/api/posts")
def get_posts():
    return posts    
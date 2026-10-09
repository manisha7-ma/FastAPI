
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

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

# Creating API endpoints that are using the Database to store and retrieve the data instead of using static data.
#API endpoint to create a new user and store it in the database.
@app.post("/api/users", response_model=UserResponse, include_in_schema=True,status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.username == user.username))
    if result.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username already exists")
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    if result.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists") 
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

#API endpoint to retrieve all users from the database.
@app.get("/api/getusers", response_model=list[UserCreate], include_in_schema=True)
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User))
    userlist = result.scalars().all()
    if not userlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found")
    return userlist

#API endpoint to retrieve a specific user by ID from the database.
@app.get("/api/users/{user_id}",response_model=UserCreate,include_in_schema=True)
async def get_user(user_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id==user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

#API endpoint to update a specific user by ID from the database. It takes the user ID and the updated user data as input, and updates the corresponding user in the database. If the user is not found, it raises a 404 error. After updating, it commits the changes to the database and returns the updated user.
@app.patch("/api/users/{user_id}",response_model=UserResponse,include_in_schema=True)
async def update_user(user_id:int,user_update:UserUpdate,db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id==user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
   
    updated_fields = user_update.model_dump(exclude_unset=True)
    if "username" in updated_fields:
        username_result = await db.execute(
            select(models.User).where(
                models.User.username == updated_fields["username"],
                models.User.id != user_id,
            )
        )
        username_exists = username_result.scalars().first()
        if username_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username already exists")
    if "email" in updated_fields:
        email_result = await db.execute(
            select(models.User).where(
                models.User.email == updated_fields["email"],
                models.User.id != user_id,
            )
        )
        email_exists = email_result.scalars().first()
        if email_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    for key, value in updated_fields.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user



#API endpoint to replace a specific user by ID from the database. It takes the user ID and the updated user data as input, and replaces the corresponding user in the database. If the user is not found, it raises a 404 error. After replacing, it commits the changes to the database and returns the updated user.
@app.put("/api/users/{user_id}",response_model=UserResponse,include_in_schema=True)
async def replace_user(user_id:int,user_update:UserCreate,db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id==user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    updated_fields = user_update.model_dump(exclude_unset=True)
    if "username" in updated_fields:
        result = await db.execute(
            select(models.User).where(
                models.User.username == updated_fields["username"],
                models.User.id != user_id,
            )
        )
        username_exists = result.scalars().first() 
            
        if username_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username already exists")
    if "email" in updated_fields:
        result = await db.execute(
            select(models.User).where(
                models.User.email == updated_fields["email"],
                models.User.id != user_id,
            )
        )
        email_exists = result.scalars().first()
        if email_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    for key, value in updated_fields.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


#API endpoint to delete a specific user by ID from the database.
@app.delete("/api/users/{user_id}",status_code=status.HTTP_204_NO_CONTENT,include_in_schema=True)
async def delete_user(user_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id==user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    result = await db.execute(select(models.Post).where(models.Post.user_id==user_id))
    posts_by_user = result.scalars().all()
    if posts_by_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete user with existing posts")
    await db.delete(user)
    await db.commit()
    return {"detail": "User deleted successfully"}   



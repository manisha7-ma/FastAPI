from pydantic import BaseModel, ConfigDict, Field,EmailStr
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="The username of the user")
    email: EmailStr = Field(..., description="The email address of the user")
  

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    image_file: str | None
    image_path:str

class UserUpdate(UserBase):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None)
    image_file: str | None = Field(default=None)
    image_path:str | None = Field(default=None)




class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="The title of the post")
    content: str = Field(..., min_length=1, description="The content of the post")
    

class PostCreate(PostBase):
    user_id:int #Temporary field to associate the post with a user; in a real application, this would be derived from the authenticated user.

class PostUpdate(PostBase):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    content: str | None = Field(default=None, min_length=1)


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int  # The ID of the user who created the post; author contains the full nested user object.
    date_posted: datetime
    author: UserResponse  # Full nested user object for the user who created the post.

    
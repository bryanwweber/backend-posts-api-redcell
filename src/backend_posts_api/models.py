from sqlmodel import Field, Relationship, SQLModel


class UserBase(SQLModel):
    name: str
    email: str


class User(UserBase, table=True):
    id: int | None = Field(default=None, nullable=False, primary_key=True)
    posts: list["Post"] = Relationship(back_populates="user")


class UserCreate(UserBase):
    pass


class UserUpdate(SQLModel):
    name: str | None = Field(default=None)
    email: str | None = Field(default=None)


class UserPublic(UserBase):
    id: int


class PostBase(SQLModel):
    title: str
    content: str
    user_id: int = Field(foreign_key="user.id")


class Post(PostBase, table=True):
    id: int | None = Field(default=None, nullable=False, primary_key=True)
    user: User = Relationship(back_populates="posts")


class PostCreate(PostBase):
    pass


class PostPublic(PostBase):
    id: int


class PostUpdate(SQLModel):
    title: str | None = Field(default=None)
    content: str | None = Field(default=None)

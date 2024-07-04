from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    id: int | None = Field(default=None, nullable=False, primary_key=True)
    name: str
    email: str
    posts: list["Post"] = Relationship(back_populates="user")


class UserUpdate(SQLModel):
    name: str | None = Field(default=None)
    email: str | None = Field(default=None)


class Post(SQLModel, table=True):
    id: int | None = Field(default=None, nullable=False, primary_key=True)
    title: str
    content: str
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="posts")


class PostUpdate(SQLModel):
    title: str | None = Field(default=None)
    content: str | None = Field(default=None)

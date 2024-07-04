from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

import bcrypt
import jwt
import markdown
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from loguru import logger
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError

from .database import get_session, init_db
from .models import (
    Post,
    PostUpdate,
    User,
    UserUpdate,
)

SECRET_KEY = "46ca66a8beec13eb9a8b0e830e6bde0dabe1e351ab9cd716823827fdb3901ae8"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


@asynccontextmanager
async def _lifespan(_: FastAPI):
    await init_db(create_data=True)
    yield


class Token(BaseModel):
    access_token: str
    token_type: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        password=plain_password.encode("utf-8"), hashed_password=hashed_password
    )


tags_metadata = [
    {
        "name": "User Operations",
        "description": "Create, view, update, and delete users.",
    },
    {
        "name": "Post Operations",
        "description": "Create, view, update, and delete posts.",
    },
]


async def _verify_jwt(token: Annotated[str, Depends(oauth2_scheme)]) -> None:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    logger.info("Verifying user...")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.error("Could not validate token")
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception


app = FastAPI(
    lifespan=_lifespan,
    openapi_tags=tags_metadata,
    title="Backend Posts API",
    version="2024.1",
)


def _create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def _could_not_find_post_exception(id: int):
    return HTTPException(status_code=404, detail=f"Could not find post with id: '{id}'")


def _could_not_find_user_exception(id: int):
    return HTTPException(status_code=404, detail=f"Could not find user with id: '{id}'")


def _authenticate_user(username, password) -> bool:
    if username != "testuser":
        return False
    hashed_password = b"$2b$12$Kt9Ae4rT5vH2IZOmq8/K7urHZIkRQhSVs2zo5yXqkcBBhP24i2AO6"
    if not verify_password(password, hashed_password):
        return False
    return True


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = _authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.error("Could not validate user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info("Validated user/pass")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = _create_access_token(
        data={"sub": "testuser"}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/", response_class=HTMLResponse)
async def hello_world():
    """Return the rendered README file, if present."""
    pth = Path("/app/README.md")
    if not pth.exists():
        return HTMLResponse("")
    return markdown.markdown(pth.read_text())


@app.get("/users/", tags=["User Operations"])
async def get_users(*, session: AsyncSession = Depends(get_session)) -> list[User]:
    """
    Retrieve all users from the database.

    **Returns:**

    A list of `User` objects representing all users in the database.
    """
    result = await session.exec(select(User))
    return result.all()


@app.get(
    "/users/{id}",
    tags=["User Operations"],
    responses={
        404: {"description": "The item was not found"},
    },
)
async def get_user(id: int, *, session: AsyncSession = Depends(get_session)) -> User:
    """
    Retrieve a user by its ID from the database.

    **Path Items:**

    * `id`: The integer ID of the user to retrieve.

    **Returns:**

    A `User` object representing the retrieved user, or raises a 404 error if the user
    is not found.
    """
    result = await session.get(User, id)
    if result is None:
        raise _could_not_find_user_exception(id)
    return result


@app.put(
    "/users/{id}",
    tags=["User Operations"],
    responses={
        404: {"description": "The item was not found"},
    },
    dependencies=[Depends(_verify_jwt)],
)
async def update_user(
    id: int, *, session: AsyncSession = Depends(get_session), user: UserUpdate
) -> User:
    """
    Update a user by its ID in the database.

    **Path Items:**

    * `id`: The integer ID of the user to update.

    **Request Body:**

    * `name`: Optional, will be updated if provided as a string
    * `email`: Optional, will be updated if provided as a string.

    **Returns:**

    A `User` object representing the updated user, or raises a 404 error if the user is
    not found.
    """
    user_result = await session.get(User, id)
    if user_result is None:
        raise _could_not_find_user_exception(id)
    if user.name is not None:
        user_result.name = user.name
    if user.email is not None:
        user_result.email = user.email
    session.add(user_result)
    session.commit()
    session.refresh(user_result)
    return user_result


@app.delete(
    "/users/{id}",
    tags=["User Operations"],
    status_code=204,
    responses={
        404: {"description": "The item was not found"},
    },
    dependencies=[Depends(_verify_jwt)],
)
async def delete_user(id: int, *, session: AsyncSession = Depends(get_session)) -> None:
    """
    Delete a user by its ID in the database.

    **Path Items:**

    * `id`: The integer ID of the user to delete

    **Returns**:

    Nothing, or raises a 404 error if the user is not found.
    """
    user = await session.get(User, id)
    if user is None:
        raise _could_not_find_user_exception(id)
    session.delete(user)
    session.commit()


@app.post("/users/", tags=["User Operations"], dependencies=[Depends(_verify_jwt)])
async def create_user(
    *, session: AsyncSession = Depends(get_session), user: User
) -> User:
    """
    Create a user in the database.

    **Request Body:**

    * `name`: A string for the user's full name.
    * `email`: A string for the user's email. The email address is not verified to be a
      valid email address

    **Returns:**

    The created `User` object.
    """
    db_user = User.model_validate(user)
    session.add(db_user)
    try:
        await session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Duplicate ID value, please choose another.",
        )
    await session.refresh(db_user)
    return db_user


@app.get("/posts/", tags=["Post Operations"])
async def get_posts(*, session: AsyncSession = Depends(get_session)) -> list[Post]:
    """
    Retrieve all posts from the database.

    **Returns:**

    A list of `Post` objects representing all posts in the database.
    """
    result = await session.exec(select(Post))
    return result.all()


@app.post(
    "/posts/",
    tags=["Post Operations"],
    responses={
        404: {"description": "The item was not found"},
    },
    dependencies=[Depends(_verify_jwt)],
)
async def create_post(
    *, session: AsyncSession = Depends(get_session), post: Post
) -> Post:
    """
    Create a post in the database.

    **Request Body:**

    * `title`: A string for the title of the post.
    * `content`: A string for the content to be posted.
    * `user_id`: An integer of an existing user in the database.

    **Returns:**

    The created `Post` object, or raises a 404 error if the `user_id` is not found in
    the database.
    """
    user = await session.get(User, post.user_id)
    if user is None:
        raise _could_not_find_user_exception(post.user_id)
    db_post = Post.model_validate(post)
    session.add(db_post)
    try:
        await session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Duplicate ID value, please choose another.",
        )
    await session.refresh(db_post)
    return db_post


@app.get(
    "/posts/{id}",
    tags=["Post Operations"],
    responses={
        404: {"description": "The item was not found"},
    },
)
async def get_post(id: int, *, session: AsyncSession = Depends(get_session)) -> Post:
    """
    Retrieve a post by its ID from the database.

    **Path Items:**

    * `id`: The integer ID of the post to retrieve.

    **Returns:**

    A `Public` object representing the retrieved user, or raises a 404 error if the post
    is not found.
    """
    result = await session.get(Post, id)
    if result is None:
        raise _could_not_find_post_exception(id)
    return result


@app.put(
    "/posts/{id}",
    tags=["Post Operations"],
    responses={
        404: {"description": "The item was not found"},
    },
    dependencies=[Depends(_verify_jwt)],
)
async def update_post(
    id: int, *, session: AsyncSession = Depends(get_session), post: PostUpdate
) -> Post:
    """
    Update a post by its ID in the database. Note, it is not possible to change the
    `user_id` associated with a post.

    **Path Items:**

    * `id`: The integer ID of the post to update.

    **Request Body:**

    * `title`: Optional, will be updated if provided as a string
    * `content`: Optional, will be updated if provided as a string.

    **Returns:**

    A `Post` object representing the updated user, or raises a 404 error if the post is
    not found.
    """
    post_result = await session.get(Post, id)
    if post_result is None:
        raise _could_not_find_post_exception(id)
    if post.title is not None:
        post_result.title = post.title
    if post.content is not None:
        post_result.content = post.content
    session.add(post_result)
    session.commit()
    session.refresh(post_result)
    return post_result


@app.delete(
    "/posts/{id}",
    tags=["Post Operations"],
    status_code=204,
    responses={
        404: {"description": "The item was not found"},
    },
    dependencies=[Depends(_verify_jwt)],
)
async def delete_post(id: int, *, session: AsyncSession = Depends(get_session)) -> None:
    """
    Delete a post by its ID in the database.

    **Path Items:**

    * `id`: The integer ID of the post to delete

    **Returns**:

    Nothing, or raises a 404 error if the post is not found.
    """
    post = await session.get(Post, id)
    if post is None:
        raise _could_not_find_post_exception(id)
    session.delete(post)
    session.commit()

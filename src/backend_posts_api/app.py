from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .database import get_session, init_db
from .models import (
    Post,
    PostCreate,
    PostPublic,
    PostUpdate,
    User,
    UserCreate,
    UserPublic,
    UserUpdate,
)


@asynccontextmanager
async def _lifespan(_: FastAPI):
    await init_db(create_data=True)
    yield


app = FastAPI(lifespan=_lifespan)


def _could_not_find_post_exception(id: int):
    return HTTPException(status_code=404, detail=f"Could not find post with id: '{id}'")


def _could_not_find_user_exception(id: int):
    return HTTPException(status_code=404, detail=f"Could not find user with id: '{id}'")


@app.get("/")
async def hello_world():
    return {"HELLO": "WORLD"}


@app.get("/users/")
async def get_users(
    *, session: AsyncSession = Depends(get_session)
) -> list[UserPublic]:
    result = await session.exec(select(User))
    return result.all()


@app.get("/users/{id}")
async def get_user(
    id: int, *, session: AsyncSession = Depends(get_session)
) -> UserPublic:
    result = await session.get(User, id)
    if result is None:
        raise _could_not_find_user_exception(id)
    return result


@app.put("/users/{id}")
async def update_user(
    id: int, *, session: AsyncSession = Depends(get_session), user: UserUpdate
) -> UserPublic:
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


@app.delete("/users/{id}", status_code=204)
async def delete_user(id: int, *, session: AsyncSession = Depends(get_session)) -> None:
    user = await session.get(User, id)
    if user is None:
        raise _could_not_find_user_exception(id)
    session.delete(user)
    session.commit()


@app.post("/users/")
async def create_user(
    *, session: AsyncSession = Depends(get_session), user: UserCreate
) -> UserPublic:
    db_user = User.model_validate(user)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


@app.get("/posts/")
async def get_posts(
    *, session: AsyncSession = Depends(get_session)
) -> list[PostPublic]:
    result = await session.exec(select(Post))
    return result.all()


@app.post("/posts/", response_model=PostPublic)
async def create_post(
    *, session: AsyncSession = Depends(get_session), post: PostCreate
) -> PostPublic:
    user = await session.get(User, post.user_id)
    if user is None:
        raise _could_not_find_user_exception(post.user_id)
    db_post = Post.model_validate(post)
    session.add(db_post)
    await session.commit()
    await session.refresh(db_post)
    return db_post


@app.get("/posts/{id}")
async def get_post(
    id: int, *, session: AsyncSession = Depends(get_session)
) -> PostPublic:
    result = await session.get(Post, id)
    if result is None:
        raise _could_not_find_post_exception(id)
    return result


@app.put("/posts/{id}")
async def update_post(
    id: int, *, session: AsyncSession = Depends(get_session), post: PostUpdate
) -> PostPublic:
    post_result = await session.get(Post, id)
    if post_result is None:
        raise _could_not_find_user_exception(id)
    if post.title is not None:
        post_result.title = post.title
    if post.content is not None:
        post_result.content = post.content
    session.add(post_result)
    session.commit()
    session.refresh(post_result)
    return post_result


@app.delete("/posts/{id}", status_code=204)
async def delete_post(id: int, *, session: AsyncSession = Depends(get_session)) -> None:
    post = await session.get(Post, id)
    if post is None:
        raise _could_not_find_post_exception(id)
    session.delete(post)
    session.commit()

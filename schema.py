import logging
from contextlib import asynccontextmanager
from functools import partial
from typing import Iterable, Dict, List

import strawberry
from strawberry.types import Info
from fastapi import FastAPI
from strawberry.fastapi import BaseContext, GraphQLRouter
from databases import Database

from settings import Settings

logger = logging.getLogger(__name__)


class Context(BaseContext):
    db: Database

    def __init__(
        self,
        db: Database,
    ) -> None:
        self.db = db
        super().__init__()


@strawberry.type
class Author:
    name: str


@strawberry.type
class Book:
    title: str
    author: Author


@strawberry.type
class Query:

    @strawberry.field
    async def books(
        self,
        info: Info[Context, None],
        author_ids: list[int] | None = None,
        search: str | None = None,
        limit: int | None = None,
    ) -> list[Book]:
        query = "SELECT books.title, authors.name FROM books JOIN authors ON books.author_id = authors.id"
        conditions: List = []
        params: Dict[str, str | Iterable | int] = {}

        if author_ids:
            conditions.append("authors.id = ANY(:author_ids)")
            params["author_ids"] = tuple(author_ids)

        if search:
            search = f"%{search}%"
            conditions.append(
                "(books.title ILIKE :search OR authors.name ILIKE :search)"
            )
            params["search"] = search

        if conditions:
            query += f" WHERE {' AND '.join(conditions)}"

        if limit:
            query += " LIMIT :limit"
            params["limit"] = limit

        query_result = await info.context.db.fetch_all(query, values=params)
        books = [
            Book(title=row["title"], author=Author(name=row["name"]))
            for row in query_result
        ]

        return books


CONN_TEMPLATE = "postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"
settings = Settings()  # type: ignore
db = Database(
    CONN_TEMPLATE.format(
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT,
        host=settings.DB_SERVER,
        name=settings.DB_NAME,
    ),
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
    db: Database,
):
    async with db:
        yield

schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(  # type: ignore
    schema,
    context_getter=partial(Context, db),
)

app = FastAPI(lifespan=partial(lifespan, db=db))
app.include_router(graphql_app, prefix="/graphql")

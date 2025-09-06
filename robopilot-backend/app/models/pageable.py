import math
from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy.orm import InstrumentedAttribute


class PageRequestSchema(BaseModel):
    page: int | None = 1
    size: int | None = 25
    sort: str | None = "created_at"
    direction: Literal["ASC", "DESC"] | None = "DESC"

    @property
    def offset(self):
        return (self.page - 1) * self.size

    def sql_sort(self, sort: InstrumentedAttribute):
        return sort.asc() if self.direction == "ASC" else sort.desc()


class PageResponseSchema(BaseModel):
    data: list[Any]
    total_pages: int | None
    total_count: int
    page_size: int

    def __init__(self, **data):
        super().__init__(**data)

        self.total_pages = math.ceil(self.total_count / self.page_size)

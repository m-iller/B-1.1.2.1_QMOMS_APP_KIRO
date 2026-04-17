from datetime import datetime

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    statusCode: int
    message: str
    error: str
    timestamp: datetime
    path: str


class PaginationMeta(BaseModel):
    total: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedResponse(BaseModel):
    data: list
    meta: PaginationMeta

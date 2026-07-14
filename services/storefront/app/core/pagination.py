"""Pagination helper mirroring Node `paginationHelper.calculatePagination`."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Pagination:
    page: int
    limit: int
    skip: int
    sortBy: str
    sortOrder: str


def calculate_pagination(
    page: Optional[int] = None,
    limit: Optional[int] = None,
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = None,
) -> Pagination:
    p = int(page) if page else 1
    lim = int(limit) if limit else 10
    skip = (p - 1) * lim
    return Pagination(
        page=p,
        limit=lim,
        skip=skip,
        sortBy=sortBy or "createdAt",
        sortOrder=sortOrder or "desc",
    )

"""Response envelope + ORM serialization helpers.

`send_response` matches the Node `sendResponse`: ``{ success, message, meta?, data }``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi.responses import JSONResponse
from sqlalchemy import inspect


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def model_to_dict(model: Any, exclude: tuple[str, ...] = ()) -> Optional[dict]:
    """Serialize a SQLAlchemy model into a dict keyed by DB column names.

    Column names are camelCase (matching Prisma), so output JSON matches the
    original Node API. The ``metadata`` column is emitted under that key even
    though the Python attribute is ``metadata_``.
    """
    if model is None:
        return None
    result: dict[str, Any] = {}
    mapper = inspect(model).mapper
    for column in mapper.columns:
        if column.name in exclude:
            continue
        result[column.name] = _jsonable(getattr(model, column.key))
    return result


def send_response(
    *,
    status_code: int = 200,
    success: bool = True,
    message: str,
    data: Any = None,
    meta: Optional[dict] = None,
) -> JSONResponse:
    """Build the standard success envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": success,
            "message": message,
            "meta": meta,
            "data": data,
        },
    )

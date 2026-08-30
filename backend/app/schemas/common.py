# -*- coding: utf-8 -*-
"""通用响应模型与分页结构。"""

from typing import Any, Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一接口返回结构。"""

    code: int = 0
    message: str = "success"
    data: T | None = None


class PageResult(BaseModel, Generic[T]):
    """分页结果。"""

    total: int
    page: int
    page_size: int
    items: List[T]


def success(data: Any = None, message: str = "success") -> dict:
    """构造统一成功响应。"""
    return {"code": 0, "message": message, "data": data}


def error(code: int, message: str) -> dict:
    """构造统一失败响应。"""
    return {"code": code, "message": message, "data": None}

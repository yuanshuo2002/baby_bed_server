"""
通用响应模型
定义统一的API响应格式
"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    code: int = Field(default=0, description="业务状态码，0表示成功")
    message: str = Field(default="success", description="响应消息")
    data: Any = Field(default=None, description="响应数据")


class PageParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")


class PageResponse(BaseModel, Generic[T]):
    """分页响应"""
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    items: list[T] = Field(default_factory=list, description="数据列表")

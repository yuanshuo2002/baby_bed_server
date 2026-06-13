"""
统一响应格式工具模块
提供标准化的API响应构造函数
"""
from typing import Any

from fastapi.responses import JSONResponse


def success(data: Any = None, message: str = "success") -> dict:
    """
    构造成功响应

    Args:
        data: 响应数据
        message: 响应消息

    Returns:
        标准响应字典
    """
    return {"code": 0, "message": message, "data": data}


def error(code: int = -1, message: str = "操作失败", data: Any = None) -> dict:
    """
    构造失败响应

    Args:
        code: 业务错误码
        message: 错误消息
        data: 附加数据

    Returns:
        标准响应字典
    """
    return {"code": code, "message": message, "data": data}


def success_response(data: Any = None, message: str = "success") -> JSONResponse:
    """
    构造成功JSON响应对象

    Args:
        data: 响应数据
        message: 响应消息

    Returns:
        JSONResponse对象
    """
    return JSONResponse(content=success(data=data, message=message))


def error_response(code: int = -1, message: str = "操作失败", data: Any = None) -> JSONResponse:
    """
    构造失败JSON响应对象

    Args:
        code: 业务错误码
        message: 错误消息
        data: 附加数据

    Returns:
        JSONResponse对象
    """
    return JSONResponse(content=error(code=code, message=message, data=data))

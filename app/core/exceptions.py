"""
自定义业务异常模块
定义项目中使用的各类异常
"""
from fastapi import HTTPException


class BusinessException(HTTPException):
    """
    业务逻辑异常基类
    用于在业务逻辑中抛出带有业务错误码的异常
    """

    def __init__(
        self,
        code: int = -1,
        message: str = "业务处理失败",
        status_code: int = 200,
    ):
        self.code = code
        self.message = message
        super().__init__(status_code=status_code, detail=message)


class UnauthorizedException(BusinessException):
    """未认证异常（401）"""

    def __init__(self, message: str = "未登录或登录已过期"):
        super().__init__(code=401, message=message, status_code=401)


class ForbiddenException(BusinessException):
    """无权限异常（403）"""

    def __init__(self, message: str = "无权限访问该资源"):
        super().__init__(code=403, message=message, status_code=403)


class NotFoundException(BusinessException):
    """资源不存在异常（404）"""

    def __init__(self, message: str = "请求的资源不存在"):
        super().__init__(code=404, message=message, status_code=404)


class ConflictException(BusinessException):
    """资源冲突异常（409）"""

    def __init__(self, message: str = "资源已存在或发生冲突"):
        super().__init__(code=409, message=message, status_code=409)


class ValidationException(BusinessException):
    """参数校验异常（422）"""

    def __init__(self, message: str = "请求参数校验失败"):
        super().__init__(code=422, message=message, status_code=422)


class RateLimitException(BusinessException):
    """频率限制异常（429）"""

    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(code=429, message=message, status_code=429)


class ExternalApiException(BusinessException):
    """外部API调用异常（502）"""

    def __init__(self, message: str = "外部服务调用失败"):
        super().__init__(code=502, message=message, status_code=502)

"""
用户相关Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    """用户注册请求"""
    phone: str = Field(..., pattern=r"^\+?[0-9]{7,15}$", description="国际手机号，支持带+国家代码")
    password: str = Field(..., min_length=6, max_length=32, description="密码")
    nickname: str | None = Field(None, max_length=50, description="昵称")


class UserLogin(BaseModel):
    """用户登录请求"""
    phone: str = Field(..., pattern=r"^\+?[0-9]{7,15}$", description="国际手机号，支持带+国家代码")
    password: str = Field(..., description="密码")


class WechatLogin(BaseModel):
    """微信登录请求"""
    code: str = Field(..., description="微信登录code")


class UserUpdate(BaseModel):
    """用户信息更新请求"""
    nickname: str | None = Field(None, max_length=50, description="昵称")
    avatar_url: str | None = Field(None, description="头像URL或Base64数据")
    gender: int | None = Field(None, ge=0, le=2, description="性别：0-未知 1-男 2-女")


class UserInfo(BaseModel):
    """用户信息响应"""
    id: int
    phone: str | None = None
    email: str | None = None
    nickname: str | None = None
    avatar_url: str | None = None
    gender: int | None = None
    wechat_openid: str | None = None
    status: str | None = None
    last_login_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str = Field(description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间(秒)")


class SmsCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[0-9]{7,15}$")
    scene: str = Field(default="login", pattern=r"^(login|reset_password|bind_phone)$")


class CodeLoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[0-9]{7,15}$")
    code: str = Field(..., min_length=4, max_length=8)


class ResetPasswordRequest(CodeLoginRequest):
    new_password: str = Field(..., min_length=6, max_length=32)


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=32)


class BindPhoneRequest(BaseModel):
    phone: str | None = Field(None, pattern=r"^\+?[0-9]{7,15}$")
    code: str | None = Field(None, min_length=4, max_length=8)
    old_phone_code: str | None = Field(None, min_length=4, max_length=8)
    new_phone: str | None = Field(None, pattern=r"^\+?[0-9]{7,15}$")
    new_phone_code: str | None = Field(None, min_length=4, max_length=8)


class CancelAccountRequest(BaseModel):
    confirm_text: str
    password: str | None = None

"""
用户认证路由
包含用户注册、登录、微信登录、用户信息管理等接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.response import success
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.user import (
    BindPhoneRequest, CancelAccountRequest, ChangePasswordRequest, CodeLoginRequest,
    ResetPasswordRequest, SmsCodeRequest, UserRegister, UserLogin, WechatLogin, UserUpdate,
)
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["用户认证"])


@router.post("/sms-code", response_model=ApiResponse, summary="发送短信验证码")
async def send_sms_code(body: SmsCodeRequest):
    return success(data=auth_service.send_sms_code(body.phone, body.scene), message="验证码已发送")


@router.post("/code-login", response_model=ApiResponse, summary="验证码登录")
async def code_login(body: CodeLoginRequest, db: AsyncSession = Depends(get_db_session)):
    return success(data=await auth_service.code_login(db, body.phone, body.code), message="登录成功")


@router.post("/reset-password", response_model=ApiResponse, summary="重置密码")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db_session)):
    await auth_service.reset_password(db, body.phone, body.code, body.new_password)
    return success(message="密码重置成功")


@router.post("/register", response_model=ApiResponse, summary="用户注册")
async def register(
    body: UserRegister,
    db: AsyncSession = Depends(get_db_session),
):
    """用户手机号注册"""
    result = await auth_service.register(db, phone=body.phone, password=body.password, nickname=body.nickname)
    return success(data=result, message="注册成功")


@router.post("/login", response_model=ApiResponse, summary="用户登录")
async def login(
    body: UserLogin,
    db: AsyncSession = Depends(get_db_session),
):
    """用户手机号密码登录"""
    result = await auth_service.login(db, phone=body.phone, password=body.password)
    return success(data=result, message="登录成功")


@router.post("/wechat-login", response_model=ApiResponse, summary="微信登录")
async def wechat_login(
    body: WechatLogin,
    db: AsyncSession = Depends(get_db_session),
):
    """微信小程序登录"""
    result = await auth_service.wechat_login(db, code=body.code)
    return success(data=result)


@router.get("/info", response_model=ApiResponse, summary="获取当前用户信息")
async def get_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取当前登录用户的详细信息"""
    result = await auth_service.get_user_info(db, user_id=current_user.id)
    return success(data=result)


@router.put("/info", response_model=ApiResponse, summary="更新用户信息")
async def update_user_info(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """更新当前登录用户的信息"""
    await auth_service.update_user_info(
        db, user_id=current_user.id,
        nickname=body.nickname, avatar_url=body.avatar_url, gender=body.gender,
    )
    return success(message="更新成功")


@router.post("/change-password", response_model=ApiResponse, summary="修改密码")
async def change_password(body: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await auth_service.change_password(db, current_user.id, body.old_password, body.new_password)
    return success(message="密码修改成功")


@router.post("/bind-phone", response_model=ApiResponse, summary="绑定或更换手机号")
async def bind_phone(body: BindPhoneRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await auth_service.bind_phone(db, current_user.id, **body.model_dump())
    return success(message="手机号绑定成功")


@router.post("/cancel-account", response_model=ApiResponse, summary="注销账号")
async def cancel_account(body: CancelAccountRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await auth_service.cancel_account(db, current_user.id, body.confirm_text, body.password)
    return success(message="账号已注销")

"""
认证业务逻辑层
处理用户注册、登录、微信登录等认证相关业务
"""
import hashlib
import random
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException, NotFoundException, ValidationException
from app.core.security import create_access_token
from app.models.user import User
from app.utils.phone import detect_country_code
from config import settings


class AuthService:
    """认证服务"""
    _sms_codes: dict[tuple[str, str], tuple[str, datetime]] = {}

    @staticmethod
    def _password_hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def send_sms_code(cls, phone: str, scene: str) -> dict:
        code = f"{random.randint(0, 999999):06d}"
        cls._sms_codes[(phone, scene)] = (code, datetime.now() + timedelta(minutes=5))
        result = {"expires_in": 300}
        if settings.DEBUG:
            result["debug_code"] = code
        return result

    @classmethod
    def _verify_sms_code(cls, phone: str, code: str, *scenes: str) -> None:
        now = datetime.now()
        for scene in scenes:
            stored = cls._sms_codes.get((phone, scene))
            if stored and stored[0] == code and stored[1] >= now:
                del cls._sms_codes[(phone, scene)]
                return
        raise ValidationException("验证码错误或已过期")

    @staticmethod
    def _token_result(user: User) -> dict:
        token = create_access_token({"sub": str(user.id)})
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
            "user": {"id": user.id, "phone": user.phone, "nickname": user.nickname, "avatar_url": user.avatar_url},
        }

    @staticmethod
    async def register(
        db: AsyncSession,
        phone: str,
        password: str,
        nickname: str | None = None,
    ) -> dict:
        """用户注册"""
        # 检查手机号是否已注册
        result = await db.execute(select(User).where(User.phone == phone))
        if result.scalar_one_or_none():
            raise ConflictException("手机号已注册")

        # 密码哈希
        password_hash = AuthService._password_hash(password)

        # 创建用户
        user = User(
            phone=phone,
            password_hash=password_hash,
            nickname=nickname or f"用户{phone[-4:]}",
        )
        db.add(user)
        await db.flush()

        # 生成JWT Token
        token = create_access_token({"sub": str(user.id)})

        # 检测国家信息
        country_code, country_name, local_phone = detect_country_code(phone)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "phone": user.phone,
                "phone_country": country_name,
                "phone_local": local_phone,
                "nickname": user.nickname,
            },
        }

    @staticmethod
    async def login(db: AsyncSession, phone: str, password: str) -> dict:
        """用户登录"""
        result = await db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        if not user:
            raise UnauthorizedException("手机号或密码错误")

        if user.status != "active":
            raise UnauthorizedException("账号已被注销或禁用")

        # 验证密码
        password_hash = AuthService._password_hash(password)
        if user.password_hash != password_hash:
            raise UnauthorizedException("手机号或密码错误")

        # 更新最后登录时间
        user.last_login_at = datetime.now()

        # 检测国家信息
        country_code, country_name, local_phone = detect_country_code(phone)

        # 生成JWT Token
        token = create_access_token({"sub": str(user.id)})
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "phone": user.phone,
                "phone_country": country_name,
                "phone_local": local_phone,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
            },
        }

    @classmethod
    async def code_login(cls, db: AsyncSession, phone: str, code: str) -> dict:
        cls._verify_sms_code(phone, code, "login")
        result = await db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        if user:
            if user.status != "active":
                raise UnauthorizedException("账号已被注销或禁用")
            user.last_login_at = datetime.now()
            return cls._token_result(user)
        # 未注册用户自动创建
        user = User(phone=phone, nickname=f"用户{phone[-4:]}")
        db.add(user)
        await db.flush()
        user.last_login_at = datetime.now()
        return cls._token_result(user)

    @classmethod
    async def reset_password(cls, db: AsyncSession, phone: str, code: str, new_password: str) -> None:
        cls._verify_sms_code(phone, code, "reset_password")
        result = await db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("用户不存在")
        user.password_hash = cls._password_hash(new_password)

    @classmethod
    async def change_password(cls, db: AsyncSession, user_id: int, old_password: str, new_password: str) -> None:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.password_hash or user.password_hash != cls._password_hash(old_password):
            raise UnauthorizedException("旧密码错误")
        user.password_hash = cls._password_hash(new_password)

    @classmethod
    async def bind_phone(cls, db: AsyncSession, user_id: int, **kwargs) -> None:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        new_phone = kwargs.get("new_phone") or kwargs.get("phone")
        new_code = kwargs.get("new_phone_code") or kwargs.get("code")
        if not new_phone or not new_code:
            raise ValidationException("缺少新手机号或验证码")
        if user.phone:
            old_code = kwargs.get("old_phone_code")
            if not old_code:
                raise ValidationException("缺少当前手机号验证码")
            cls._verify_sms_code(user.phone, old_code, "bind_phone")
        cls._verify_sms_code(new_phone, new_code, "bind_phone")
        exists = await db.execute(select(User).where(User.phone == new_phone, User.id != user_id))
        if exists.scalar_one_or_none():
            raise ConflictException("手机号已被绑定")
        user.phone = new_phone

    @classmethod
    async def cancel_account(cls, db: AsyncSession, user_id: int, confirm_text: str, password: str | None) -> None:
        if confirm_text != "确认注销":
            raise ValidationException("请输入确认注销")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one()
        if user.password_hash and (not password or user.password_hash != cls._password_hash(password)):
            raise UnauthorizedException("登录密码错误")
        # 清除手机号绑定，允许该手机号重新注册
        user.phone = None
        user.status = "inactive"

    @staticmethod
    async def wechat_login(db: AsyncSession, code: str) -> dict:
        """微信小程序登录"""
        if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
            raise UnauthorizedException("微信登录暂未配置")

        # 调用微信接口获取 openid
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    "https://api.weixin.qq.com/sns/jscode2session",
                    params={
                        "appid": settings.WECHAT_APP_ID,
                        "secret": settings.WECHAT_APP_SECRET,
                        "js_code": code,
                        "grant_type": "authorization_code",
                    },
                )
                data = resp.json()
            except httpx.RequestError as e:
                raise UnauthorizedException(f"微信服务器请求失败: {str(e)}")

        # 检查返回错误
        if "openid" not in data:
            errcode = data.get("errcode", 0)
            errmsg = data.get("errmsg", "微信登录失败")
            raise UnauthorizedException(f"微信登录失败: {errmsg}")

        openid = data["openid"]
        session_key = data.get("session_key")

        # 查找或创建用户
        result = await db.execute(select(User).where(User.wechat_openid == openid))
        user = result.scalar_one_or_none()

        if not user:
            # 新用户自动注册
            user = User(
                wechat_openid=openid,
                wechat_unionid=data.get("unionid"),
                nickname=f"微信用户{openid[-6:]}",
            )
            db.add(user)
            await db.flush()

        # 更新登录信息
        user.last_login_at = datetime.now()

        # 生成 JWT Token
        token = create_access_token({"sub": str(user.id)})
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "phone": user.phone,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
            },
        }

    @staticmethod
    async def get_user_info(db: AsyncSession, user_id: int) -> dict:
        """获取用户信息（包含设备状态）"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("用户不存在")

        # 查询用户家庭下的设备状态
        from app.models.baby import Baby
        from app.models.device import Device
        from app.services.family_service import FamilyService

        family = await FamilyService._get_user_family_obj(db, user_id)
        baby_result = await db.execute(select(Baby.id).where(Baby.family_id == family.id))
        baby_ids = [row[0] for row in baby_result.all()]

        # 查询设备列表
        device_list = []
        if baby_ids:
            device_result = await db.execute(
                select(Device).where(Device.baby_id.in_(baby_ids))
            )
            devices = device_result.scalars().all()
            for d in devices:
                device_list.append({
                    "device_sn": d.device_sn,
                    "device_name": d.device_name,
                    "online_status": d.online_status,
                    "last_online_at": d.last_online_at.isoformat() if d.last_online_at else None,
                })

        return {
            "id": user.id,
            "phone": user.phone,
            "email": user.email,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "gender": user.gender,
            "status": user.status,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "devices": device_list,
        }

    @staticmethod
    async def update_user_info(
        db: AsyncSession,
        user_id: int,
        nickname: str | None = None,
        avatar_url: str | None = None,
        gender: int | None = None,
    ) -> None:
        """更新用户信息"""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("用户不存在")

        if nickname is not None:
            user.nickname = nickname
        if avatar_url is not None:
            user.avatar_url = avatar_url
        if gender is not None:
            user.gender = gender


auth_service = AuthService()

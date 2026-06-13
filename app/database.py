"""
SQLAlchemy 异步数据库连接配置
使用 aiomysql 驱动连接 MySQL
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    """ORM模型基类"""
    pass

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=False,  # 禁用连接健康检查，避免 aiomysql 版本兼容问题
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

# 创建异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖函数
    用作 FastAPI 的 Depends 依赖注入
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# 兼容别名，供 main.py 后台任务使用
AsyncSessionLocal = async_session_factory

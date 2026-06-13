# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Baby Bed Server is a FastAPI backend service for a smart baby bed IoT system. It manages device registration, sensor data, family/baby profiles, monitoring events, and integrates with external AI services (LLM, TTS, ASR).

## Tech Stack

- **Framework**: FastAPI 0.110+ with async support
- **Database**: MySQL via SQLAlchemy async (aiomysql driver)
- **Cache**: Redis
- **Auth**: JWT (python-jose)
- **External Services**: LLM API, TTS API, ASR API (configured in config.py)

## Running the Server

```bash
# Development (auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production with gunicorn
gunicorn -c gunicorn_conf.py main:app

# Production with uwsgi
uwsgi --ini uwsgi.ini
```

## Code Architecture

```
app/
├── api/
│   ├── deps.py          # Dependencies: get_current_user, get_db_session
│   └── v1/
│       ├── router.py    # Registers all v1 sub-routers under /api/v1
│       ├── auth.py      # Authentication endpoints
│       ├── device.py    # Device management
│       ├── hardware.py  # Hardware control (lights, animation, modes)
│       ├── sensor.py    # Sensor data upload/query
│       └── ...          # Other domain routers
├── core/
│   ├── exceptions.py    # BusinessException hierarchy
│   ├── response.py      # success(), error() helpers
│   └── security.py      # JWT create/verify/decode
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic layer
└── database.py          # Async SQLAlchemy setup
```

## API Structure

All endpoints are under `/api/v1`. Three endpoint categories:

1. **Hardware endpoints** - No authentication (device calls)
   - `/device/register`, `/sensor/upload`, `/sensor/status/upload`, `/hardware/heartbeat`
   - No `Authorization` header required

2. **App endpoints** - Requires JWT auth (mini-program calls)
   - Most endpoints fall here
   - Pass `Authorization: Bearer {token}` header

3. **Shared endpoints** - Requires JWT auth (both hardware and app)
   - `/device/bind`, `/device/unbind`, `/sensor/events`

Authentication dependency: `get_current_user` from `app.api.deps`

## API Modules

| Module | Prefix | Description |
|--------|--------|-------------|
| auth | `/auth` | 用户认证 |
| device | `/device` | 设备管理 |
| hardware | `/hardware` | 硬件控制(灯光/动画/模式) |
| sensor | `/sensor` | 传感器数据 |
| status | `/status` | 状态日志/哭闹/危险事件 |
| baby | `/baby` | 宝宝管理 |
| family | `/family` | 家庭管理 |
| voice | `/voice` | 自主对话(语音克隆/ASR/TTS) |
| routine | `/routine` | 作息管理(EASY模式) |
| milestone | `/milestone` | 成长记录/里程碑/AI周报 |
| response | `/response` | 被动响应 |
| moment | `/moment` | 温馨瞬间/成长相册 |
| learning | `/learning` | 学习进度 |
| video | `/video` | 视频识别 |
| **interaction** | `/interaction` | **婴儿互动(教育/娱乐)** |
| **system** | `/system` | **系统管理(存储/同步/性能/健康)** |

## 新增接口 (来自需求文档)

### 2.3 婴儿互动（教育/娱乐）
| 接口 | 方法 | 说明 |
|------|------|------|
| `/interaction/content` | POST | 创建互动内容 |
| `/interaction/library` | GET | 获取资源库(按月龄状态推荐) |
| `/interaction/history` | GET | 互动历史 |

### 6.1 硬件端核心接口
| 接口 | 方法 | 说明 |
|------|------|------|
| `/device/register` | POST | 设备注册[硬件] |
| `/hardware/heartbeat` | POST | 心跳获取baby_id[硬件] |
| `/sensor/upload` | POST | 传感器数据上传[硬件] |
| `/sensor/status/upload` | POST | 婴儿状态及风险等级上传[硬件] |

## Response Format

Standard success response:
```json
{"code": 0, "message": "success", "data": {...}}
```

Standard error response (via `BusinessException`):
```json
{"code": 401, "message": "未登录或登录已过期", "data": null}
```

## Database Patterns

- All database operations are async
- Use `db: AsyncSession = Depends(get_db_session)` in route handlers
- Session auto-commits on success, auto-rolls back on exception
- Models inherit from `app.database.Base`

## Service Layer Pattern

Business logic lives in services under `app/services/`. Services are instantiated as singletons:

```python
# In app/services/example_service.py
class ExampleService:
    @staticmethod
    async def some_method(db: AsyncSession, ...) -> ...:
        ...

example_service = ExampleService()

# In routes
from app.services.example_service import example_service
```

## Adding a New API

1. Create schema in `app/schemas/` if needed
2. Create model in `app/models/` if needed
3. Add service methods in `app/services/`
4. Create router in `app/api/v1/{domain}.py`
5. Register in `app/api/v1/router.py`

## Key Files

- `main.py` - FastAPI app initialization and middleware
- `config.py` - All configuration via pydantic-settings
- `app/api/deps.py` - Auth dependencies (get_current_user)
- `app/core/exceptions.py` - Exception types
- `app/core/response.py` - Response helpers

## Environment Variables

See `.env` and `config.py` for all settings. Key variables:
- Database: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- JWT: `JWT_SECRET_KEY`, `JWT_EXPIRE_MINUTES`
- External APIs: `LLM_API_URL`, `TTS_API_URL`, `ASR_API_URL`
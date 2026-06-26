# Baby Bed Server

智能婴儿床后端服务 API，支持设备管理、传感器数据采集、婴儿状态监控、语音交互、成长记录等功能。

## 技术栈

- **Framework**: FastAPI 0.110+ (异步支持)
- **Database**: MySQL via SQLAlchemy async
- **Cache**: Redis
- **Auth**: JWT (python-jose)
- **External Services**: LLM API, TTS API, ASR API

## 项目结构

```
baby_bed_server2/
├── app/
│   ├── api/
│   │   └── v1/           # API v1 路由
│   │       ├── auth.py       # 用户认证
│   │       ├── baby.py       # 宝宝管理
│   │       ├── device.py     # 设备管理
│   │       ├── family.py     # 家庭管理
│   │       ├── hardware.py   # 硬件控制
│   │       ├── interaction.py # 婴儿互动
│   │       ├── milestone.py  # 成长记录
│   │       ├── moment.py     # 温馨瞬间
│   │       ├── routine.py    # 作息管理
│   │       ├── sensor.py     # 传感器数据
│   │       ├── status.py     # 状态日志
│   │       ├── voice.py      # 语音交互
│   │       └── ...
│   ├── core/             # 核心模块
│   │   ├── exceptions.py    # 业务异常
│   │   ├── response.py      # 响应格式化
│   │   └── security.py      # JWT 安全
│   ├── models/           # ORM 模型
│   ├── schemas/           # Pydantic schemas
│   ├── services/         # 业务逻辑层
│   ├── utils/            # 工具函数
│   └── database.py       # 数据库配置
├── tests/               # 单元测试
├── main.py              # 应用入口
├── config.py            # 配置管理
├── requirements.txt    # 依赖列表
└── .python-version     # uv/Python 版本锁定
```

## API 概览

### 硬件端接口（无需认证）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/device/register` | POST | 设备注册 |
| `/api/v1/hardware/heartbeat` | POST | 心跳获取baby_id |
| `/api/v1/sensor/upload` | POST | 传感器数据上传 |
| `/api/v1/sensor/status/upload` | POST | 婴儿状态及风险等级上传 |

### 应用端接口（需要 JWT 认证）

| 模块 | 前缀 | 说明 |
|------|------|------|
| auth | `/api/v1/auth` | 用户认证 |
| device | `/api/v1/device` | 设备管理 |
| baby | `/api/v1/baby` | 宝宝管理 |
| family | `/api/v1/family` | 家庭管理 |
| routine | `/api/v1/routine` | 作息管理 |
| milestone | `/api/v1/milestone` | 成长记录 |
| voice | `/api/v1/voice` | 语音交互 |
| video | `/api/v1/video` | 视频识别 |
| interaction | `/api/v1/interaction` | 婴儿互动 |

## 快速开始

### 1. 安装依赖

```bash
# 安装 uv（如果还没有）
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 创建并激活独立环境
uv venv --python 3.11.13 .venv
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=baby_bed

# JWT 配置
JWT_SECRET_KEY=your_secret_key
JWT_EXPIRE_MINUTES=1440

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 外部 API
LLM_API_URL=https://api.example.com/llm
TTS_API_URL=http://127.0.0.1:40028/tts
ASR_API_URL=http://127.0.0.1:40021/asr
```

### 3. 运行服务

**开发模式：**
```bash
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**生产模式（Gunicorn）：**
```bash
source .venv/bin/activate
gunicorn -c gunicorn_conf.py main:app
```

**生产模式（UWSGI）：**
```bash
uwsgi --ini uwsgi.ini
```

## API 响应格式

**成功响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {...}
}
```

**错误响应：**
```json
{
  "code": 401,
  "message": "未登录或登录已过期",
  "data": null
}
```

## 主要功能模块

### 设备管理
- 设备注册与绑定
- 设备状态监控
- 离线设备自动清理

### 传感器数据
- 温湿度、噪声等传感器数据采集
- 婴儿状态识别
- 风险等级评估

### 婴儿互动
- 教育内容推荐
- 互动历史记录
- 资源库管理

### 成长记录
- 里程碑记录
- AI 周报生成
- 成长相册

### 语音交互
- 语音克隆
- ASR/TTS 集成
- 对话管理

### 本地 TTS 服务（MeloTTS）

如果你要把 TTS 切到本地声线服务，可以单独启动这个微服务：

```bash
source .venv/bin/activate
uv run uvicorn app.services.melotts_tts_app:app --host 0.0.0.0 --port 40028
```

可用环境变量：

```env
MELOTTS_LANGUAGE=ZH
MELOTTS_DEVICE=cpu
MELOTTS_DEFAULT_SPEAKER=ZH
MELOTTS_SPEAKER_MOM=ZH
MELOTTS_SPEAKER_DAD=ZH
MELOTTS_SPEAKER_NANNY=ZH
MELOTTS_SPEAKER_OTHER=ZH
MELOTTS_OUTPUT_FORMAT=wav
MELOTTS_SAMPLE_RATE=24000
MELOTTS_SPEED=1.0
```

后端主服务默认会把 TTS 请求转发到 `http://127.0.0.1:40028/tts`，并按家庭音色的 `voice_role` 选择声线。

## 三端联调启动顺序

推荐按下面顺序启动，便于排查：

1. 启动 ASR 服务

```bash
cd /home/simon/voice_services/asr_fast
CUDA_VISIBLE_DEVICES=4 ASR_DEVICE=cuda ASR_COMPUTE_TYPE=float16 \
  uv run uvicorn app:app --app-dir /home/simon/voice_services/asr_fast \
  --host 0.0.0.0 --port 40021
```

2. 启动本地 TTS 服务

```bash
uv run uvicorn app.services.melotts_tts_app:app --host 0.0.0.0 --port 40028
```

3. 启动主后端服务

```bash
gunicorn -c gunicorn_conf.py main:app
```

4. 快速检查

```bash
curl http://127.0.0.1:40021/health
curl http://127.0.0.1:40028/health
curl http://127.0.0.1:34223/api/v1/health
```

如果你想让 TTS 跑在 GPU 上，可以把 `MELOTTS_DEVICE` 改成 `cuda`；如果本机模型还没准备好，先用 `cpu` 也可以联调接口。

### 视频回填

如果历史视频记录的 `img_url` 为空，可以在项目根目录执行：

```bash
uv run python scripts/backfill_video_covers.py
```

## 测试

```bash
pytest tests/
```

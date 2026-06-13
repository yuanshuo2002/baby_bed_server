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
baby_bed_server/
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
└── requirements.txt    # 依赖列表
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
pip install -r requirements.txt
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
TTS_API_URL=https://api.example.com/tts
ASR_API_URL=https://api.example.com/asr
```

### 3. 运行服务

**开发模式：**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**生产模式（Gunicorn）：**
```bash
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

## 测试

```bash
pytest tests/
```

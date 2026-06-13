# Baby Agent System 测试指南

## 1. 环境准备

### 1.1 克隆项目

```powershell
cd D:\DeepBlue\AIProjects
git clone -b new_Raspberry_pi https://github.com/648428732qq-sketch/baby_agent_system------2.0.git
cd baby_agent_system------2.0
```

### 1.2 创建虚拟环境

```powershell
python -m venv .venv
```

### 1.3 安装依赖

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 1.4 安装额外依赖（如有）

```powershell
.\.venv\Scripts\python.exe -m pip install pyserial
```

## 2. 依赖验证

### 语法检查

```powershell
.\.venv\Scripts\python.exe -m py_compile main.py agents/voice_agent.py agents/video_agent.py core/langgraph_orchestrator.py
```

### 导入测试

```powershell
.\.venv\Scripts\python.exe test_imports.py
```

### 依赖完整性检查

```powershell
.\.venv\Scripts\python.exe -c "import serial, redis, cv2, PIL, pvrecorder, sounddevice, torch, langgraph; print('OK')"
```

## 3. Redis 配置（可选）

### 启动 Redis 容器

```powershell
docker run -d -p 6379:6379 --name redis-server redis:latest
```

### 验证 Redis

```powershell
docker ps                           # 查看运行状态
docker exec -it redis-server redis-cli ping  # 测试连接，返回 PONG 即成功
```

### Redis 命令

```powershell
docker stop redis-server   # 停止
docker start redis-server  # 启动
docker rm redis-server     # 删除容器
```

> 注意：不安装 Redis 时，系统会自动切换到内存 Pub/Sub（仅限单进程）

## 4. 运行测试

### 单元测试（无需 GUI）

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/ -v
```

### 模拟系统测试

```powershell
.\.venv\Scripts\python.exe test_system.py
```

### Agent 创建测试

```powershell
.\.venv\Scripts\python.exe simple_test.py
```

## 5. 启动主程序

### 正常启动（需要显示器）

```powershell
cd D:\DeepBlue\AIProjects\baby_agent_system------2.0
.\.venv\Scripts\python.exe main.py
```

### 后台运行（无头模式）

```powershell
# 直接在终端运行，Ctrl+C 退出
.\.venv\Scripts\python.exe main.py
```

## 6. 配置文件

项目已有 `config.json`，无需额外创建。如需保护敏感信息，可创建 `.env` 文件。

## 7. 目录结构

```
baby_agent_system------2.0/
├── agents/           # Agent 模块（UI/语音/视频/通知）
├── core/              # 核心逻辑（LangGraph/Redis）
├── config/            # 配置和台词
├── soothing_audio/    # 被动情景音效
├── music/             # 主动播放音乐库
├── tests/             # 单元测试
├── main.py            # 主程序入口
└── config.json        # 主配置文件
```

## 8. 常见问题

| 问题 | 解决方案 |
|------|----------|
| `ModuleNotFoundError: No module named 'serial'` | `.\.venv\Scripts\python.exe -m pip install pyserial` |
| Redis 连接失败 | 系统会自动切换到内存模式，或启动 Docker Redis |
| GUI 无法显示 | 确保 Windows 有桌面环境，或使用 pytest 测试 |

## 9. 参考文档

- 项目 README: `README.md`
- 详细设计: `AGENTS.md`
- Linux 适配: `LINUX_ADAPTATION_CHANGELOG.md`
# Ubuntu 24.04 开发板从零克隆并运行 baby_agent_system------2.0 教程

## 1. 安装 Git

更新软件源：

```bash
sudo apt update
```

安装 Git：

```bash
sudo apt install git -y
```

验证安装：

```bash
git --version
```

正常输出类似：

```text
git version 2.43.0
```

---

## 2. 克隆项目

克隆指定分支：

```bash
git clone -b new_Raspberry_pi --single-branch https://github.com/648428732qq-sketch/baby_agent_system------2.0.git
```

输入：

```text
Username:
你的GitHub用户名
```

然后输入：

```text
GitHub Personal Access Token
```

等待下载完成：

```text
Receiving objects: 100%
Resolving deltas: 100%
done.
```

---

## 3. 进入项目目录

```bash
cd baby_agent_system------2.0
```

确认当前分支：

```bash
git branch
```

应该显示：

```text
* new_Raspberry_pi
```

---

## 4. 查看 Python 版本

```bash
python3 --version
```

应看到：

```text
Python 3.12.x
```

---

## 5. 安装 uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

加载环境变量：

```bash
source ~/.local/bin/env
```

验证：

```bash
uv --version
```

如果想永久生效：

```bash
echo 'source ~/.local/bin/env' >> ~/.bashrc
source ~/.bashrc
```

---

## 6. 安装 Tkinter（GUI 必需）

```bash
sudo apt update
sudo apt install python3-tk -y
```

验证：

```bash
python3 -c "import tkinter;print('OK')"
```

---

## 7. 安装项目依赖

```bash
uv sync
```

---

## 8. 启动程序

```bash
uv run main.py
```

---

## 9. 如果通过 SSH 运行 GUI

检查：

```bash
echo $DISPLAY
```

如果为空：

```bash
export DISPLAY=:0
```

然后再次启动：

```bash
uv run main.py
```

---

# 常见问题

## git 命令不存在

```bash
sudo apt install git -y
```

## uv 命令不存在

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
```

## No module named tkinter

```bash
sudo apt install python3-tk -y
```

## GitHub 克隆卡住

```bash
git ls-remote https://github.com/648428732qq-sketch/baby_agent_system------2.0.git
```

如果出现用户名提示，说明网络正常，只是需要认证。

---

# 一键执行顺序

```bash
sudo apt update

sudo apt install git python3-tk -y

git clone -b new_Raspberry_pi --single-branch https://github.com/648428732qq-sketch/baby_agent_system------2.0.git

cd baby_agent_system------2.0

curl -LsSf https://astral.sh/uv/install.sh | sh

source ~/.local/bin/env

uv sync

uv run main.py
```

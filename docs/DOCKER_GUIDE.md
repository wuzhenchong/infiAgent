# MLA Docker 完整使用指南 🐳

**无需安装 Python，仅需 Docker！**

---

## 📋 目录

- [简介](#简介)
- [安装 Docker](#安装-docker)
- [快速开始](#快速开始)
- [配置管理](#配置管理)
- [数据持久化](#数据持久化)
- [常见问题](#常见问题)
- [高级使用](#高级使用)

---

## 📖 简介

MLA Docker 版本特点：

- ✅ **零依赖**：无需安装 Python 和依赖包
- ✅ **开箱即用**：一行命令启动
- ✅ **完整功能**：CLI、Tool Server、Config Web 全包含
- ✅ **跨平台**：Mac、Linux、Windows 统一体验
- ✅ **数据持久**：对话历史保存在宿主机

---

## 🔧 安装 Docker

### Mac

下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

**M 系列芯片用户需安装 Rosetta 2：**
```bash
softwareupdate --install-rosetta --agree-to-license
```

### Windows

下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

### Linux

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 添加当前用户到 docker 组
sudo usermod -aG docker $USER
```

**验证安装：**
```bash
docker --version
docker ps
```

---

## 🚀 快速开始

### 步骤 1: 拉取镜像

```bash
docker pull chenglinhku/mla:latest
```

### 步骤 2: 启动容器

```bash
# 进入你的工作目录
cd /path/to/your/project

# 启动容器
docker run -it --rm \
  -v $(pwd):/workspace \
  -v ~/.mla_v3:/root/mla_v3 \
  -v mla-config:/mla_config \
  -p 8002:8002 \
  -p 9641:9641 \
  chenglinhku/mla:latest \
  cli
```

### 步骤 3: 配置 API Key

**方式 A: 通过 Web 界面（推荐）**

1. 容器启动后，打开浏览器：`http://localhost:9641`
2. 点击左侧 `run_env_config/llm_config.yaml`
3. 编辑配置文件，填入 API Key
4. 点击"💾 保存文件"

<p align="center">
  <img src="../assets/config_web_screen_shot.png" alt="配置管理界面" width="800">
</p>

**方式 B: 首次启动交互式配置**

容器启动时会提示：
```
是否现在配置 API key? [y/N]: y
请输入你的 OpenRouter API Key: sk-or-v1-xxxxx
✅ API key 已配置！
```

### 步骤 4: 开始使用

```bash
[alpha_agent] > 列出当前目录的文件
[alpha_agent] > @coder_agent 编写一个 hello world 程序
```

---

## ⚙️ 配置管理

### Web 配置界面

**访问地址：** `http://localhost:9641`

**功能：**
- 📁 树形目录显示所有配置文件
- ✏️ 在线编辑 YAML 配置
- ⚡ 快速配置 API Key 和 Base URL
- 💾 实时保存，自动生效
- 🔄 一键重新加载
- 🔒 自动 YAML 格式验证

**可编辑的配置：**
- `llm_config.yaml` - LLM 配置
- `tool_config.yaml` - 工具服务器配置
- `general_prompts.yaml` - 通用提示词
- `level_0_tools.yaml` - 工具定义
- `level_1/2/3_agents.yaml` - 各层级智能体

### 命令行配置

```bash
# 进入容器配置
docker run -it --rm \
  -v mla-config:/mla_config \
  chenglinhku/mla:latest \
  /bin/bash

# 在容器内
mla-agent --config-show
mla-agent --config-set api_key "your-key"
```

---

## 💾 数据持久化

### 数据存储位置

| 数据类型 | 存储位置 | 说明 |
|---------|---------|------|
| 对话历史 | `~/.mla_v3/` | 宿主机本地 |
| 配置文件 | Docker volume `mla-config` | 持久化 |
| 工作文件 | 当前目录 | 实时同步 |

### 生命周期

| 操作 | 对话历史 | 配置文件 | 工作文件 |
|------|---------|---------|---------|
| 停止容器 | ✅ 保留 | ✅ 保留 | ✅ 保留 |
| 删除镜像 | ✅ 保留 | ✅ 保留 | ✅ 保留 |
| 删除 volume | ✅ 保留 | ❌ 丢失 | ✅ 保留 |

### 备份和恢复

**备份配置：**
```bash
docker run --rm \
  -v mla-config:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/mla-config-backup.tar.gz -C /data .
```

**恢复配置：**
```bash
docker run --rm \
  -v mla-config:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/mla-config-backup.tar.gz -C /data
```

**备份对话历史：**
```bash
tar czf mla-conversations-backup.tar.gz ~/.mla_v3
```

---

## 🎯 使用场景

### 场景 1: 日常研究工作

```bash
cd ~/my_research
docker run -it --rm \
  -v $(pwd):/workspace \
  -v ~/.mla_v3:/root/mla_v3 \
  -v mla-config:/mla_config \
  -p 8002:8002 -p 9641:9641 \
  chenglinhku/mla:latest cli

[alpha_agent] > 写一篇关于 Transformer 的综述论文
```

### 场景 2: 多项目管理

```bash
# 项目 A
cd ~/project_a
docker run ... cli
# 对话历史独立：~/.mla_v3/conversations/{hash_a}_*

# 项目 B（新终端）
cd ~/project_b  
docker run ... cli
# 对话历史独立：~/.mla_v3/conversations/{hash_b}_*
```

### 场景 3: CI/CD 集成

```yaml
# GitHub Actions
jobs:
  generate-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run MLA
        run: |
          docker run --rm \
            -v ${{ github.workspace }}:/workspace \
            -e OPENROUTER_API_KEY=${{ secrets.API_KEY }} \
            chenglinhku/mla:latest \
            task --task_id /workspace --user_input "生成文档"
```

### 场景 4: 服务器部署

```bash
# 后台运行长时间任务
docker run -d --name mla-research \
  -v /data/research:/workspace \
  -v mla-config:/mla_config \
  chenglinhku/mla:latest \
  task --task_id /workspace --user_input "完成论文"

# 查看日志
docker logs -f mla-research
```

---

## 🐛 常见问题

### Q1: 无法连接到 Tool Server

**症状：** CLI 启动后显示 "Tool Server failed to start"

**解决：**
```bash
# 检查端口配置
docker run --rm chenglinhku/mla:latest \
  cat /app/config/run_env_config/tool_config.yaml

# 确保端口一致（默认 8002）
```

### Q2: 配置不生效

**症状：** 修改配置后仍然提示 API key 错误

**解决：**
```bash
# 检查配置是否正确保存
docker run --rm -v mla-config:/mla_config chenglinhku/mla:latest \
  cat /mla_config/llm_config.yaml

# 重新配置
docker run -it --rm -v mla-config:/mla_config chenglinhku/mla:latest \
  mla-agent --config-set api_key "your-key"
```

### Q3: 权限错误

**症状：** 容器创建的文件无法在宿主机访问

**解决（Linux）：**
```bash
docker run -it --rm \
  -v $(pwd):/workspace \
  -u $(id -u):$(id -g) \
  chenglinhku/mla:latest cli
```

### Q4: Web 配置界面无法访问

**症状：** `http://localhost:9641` 无法打开

**解决：**
```bash
# 确保端口已暴露
docker run -it --rm \
  -v $(pwd):/workspace \
  -v mla-config:/mla_config \
  -p 9641:9641 \  # ← 确保这行存在
  chenglinhku/mla:latest cli

# 检查端口是否被占用
lsof -i:9641  # Mac/Linux
netstat -ano | findstr 9641  # Windows
```

### Q5: 中文显示乱码

**症状：** CLI 中中文显示为问号或方块

**解决：**
```bash
docker run -it --rm \
  -e LANG=C.UTF-8 \
  -e LC_ALL=C.UTF-8 \
  -v $(pwd):/workspace \
  chenglinhku/mla:latest cli
```

---

## 🌍 跨平台使用

### Mac / Linux

```bash
docker run -it --rm \
  -v $(pwd):/workspace \
  -v ~/.mla_v3:/root/mla_v3 \
  -v mla-config:/mla_config \
  -p 8002:8002 -p 9641:9641 \
  chenglinhku/mla:latest cli
```

### Windows PowerShell

```powershell
docker run -it --rm `
  -v ${PWD}:/workspace `
  -v ${HOME}\.mla_v3:/root/mla_v3 `
  -v mla-config:/mla_config `
  -p 8002:8002 -p 9641:9641 `
  chenglinhku/mla:latest cli
```

### Windows CMD

```cmd
docker run -it --rm ^
  -v %cd%:/workspace ^
  -v %USERPROFILE%\.mla_v3:/root/mla_v3 ^
  -v mla-config:/mla_config ^
  -p 8002:8002 -p 9641:9641 ^
  chenglinhku/mla:latest cli
```

---

## 💡 便捷使用技巧

### 创建别名

**Mac/Linux (~/.zshrc 或 ~/.bashrc)：**
```bash
alias mla='docker run -it --rm \
  -v $(pwd):/workspace \
  -v ~/.mla_v3:/root/mla_v3 \
  -v mla-config:/mla_config \
  -p 8002:8002 -p 9641:9641 \
  chenglinhku/mla:latest cli'

# 使用
cd ~/my_project
mla  # 一键启动！
```

**Windows PowerShell ($PROFILE)：**
```powershell
function mla {
    docker run -it --rm `
      -v ${PWD}:/workspace `
      -v ${HOME}\.mla_v3:/root/mla_v3 `
      -v mla-config:/mla_config `
      -p 8002:8002 -p 9641:9641 `
      chenglinhku/mla:latest cli
}
```

### 创建启动脚本

**mla-start.sh (Mac/Linux):**
```bash
#!/bin/bash
docker run -it --rm \
  -v "$(pwd)":/workspace \
  -v ~/.mla_v3:/root/mla_v3 \
  -v mla-config:/mla_config \
  -p 8002:8002 -p 9641:9641 \
  chenglinhku/mla:latest cli
```

```bash
chmod +x mla-start.sh
./mla-start.sh
```

---

## 🔄 更新镜像

### 检查更新

```bash
# 查看本地镜像信息
docker images chenglinhku/mla:latest

# 拉取最新版本
docker pull chenglinhku/mla:latest
```

### 清理旧镜像

```bash
# 删除旧版本
docker image prune -a

# 或指定删除
docker rmi chenglinhku/mla:old-version
```

---

## 📊 资源管理

### 查看容器资源使用

```bash
docker stats
```

### 限制资源

```bash
docker run -it --rm \
  --memory="4g" \
  --cpus="2" \
  -v $(pwd):/workspace \
  chenglinhku/mla:latest cli
```

### 清理所有数据

```bash
# 删除所有容器
docker container prune

# 删除未使用的镜像
docker image prune -a

# 删除 volume（配置会丢失！）
docker volume rm mla-config

# 清理对话历史（宿主机）
rm -rf ~/.mla_v3/conversations/*
```

---

## 🌐 网络配置

### 使用代理

```bash
docker run -it --rm \
  -e HTTP_PROXY=http://proxy.example.com:8080 \
  -e HTTPS_PROXY=http://proxy.example.com:8080 \
  -e NO_PROXY=localhost,127.0.0.1 \
  chenglinhku/mla:latest cli
```

### 访问宿主机服务

```bash
# 容器内访问宿主机
# Mac/Windows: host.docker.internal
# Linux: 172.17.0.1

docker run -it --rm \
  --add-host=host.docker.internal:host-gateway \
  chenglinhku/mla:latest cli
```

---

## 🔐 安全最佳实践

### 1. 不要在镜像中硬编码密钥

```bash
# ❌ 错误
# 将包含密钥的配置文件打包到镜像

# ✅ 正确
# 使用 volume 或环境变量传递密钥
```

### 2. 使用 .env 文件

```bash
# 创建 .env
echo "OPENROUTER_API_KEY=your-key" > .env

# 使用（需要 docker-compose）
docker-compose run --rm mla-agent
```

### 3. 配置文件权限

```bash
# 只读挂载配置
-v $(pwd)/config.yaml:/app/config.yaml:ro
```

---

## 📝 与本地安装对比

| 特性 | 本地安装 | Docker |
|------|---------|---------|
| 需要 Python | ✅ | ❌ |
| 安装复杂度 | 中 | 低 |
| 启动速度 | 快 | 快 |
| 性能 | 100% | 95-100% |
| 环境隔离 | 需要 venv | 自动 |
| 跨平台 | 需适配 | 一致 |
| 更新 | pip install | docker pull |
| 配置方式 | CLI/文件 | CLI/文件/**Web** |

---

## 🎓 学习资源

- [CLI 详细教程](CLI_GUIDE.md)
- [配置文件说明](../config/agent_library/Default/)
- [Tool Server API](../tool_server_lite/README.md)
- [主 README](../README.md)

---

**开始使用 Docker 版 MLA，无需配置环境！** 🐳


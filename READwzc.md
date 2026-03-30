# infiAgent 安装与使用指南

尝试了两种方法，都是Web UI 模式，一种是在docker中启动，需要参数；另一种是直接在WSL中运行（需要python）。

- 存在字符转义问题（已向开发者提交issue）：比如latex中的`\begin`会被识别为转义字符，`\b`变成一个小方块。表格中`\\`会被转义为单个`\`。

## 方式 1: Docker（推荐 - 无需 Python）

**1. 安装 Docker**

- Mac/Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Linux: `curl -fsSL https://get.docker.com | sh`

**2. 拉取镜像**

```bash
docker pull chenglinhku/mlav3:latest
```

**3. 选择模式：Web UI 模式（推荐）**

选择你自己的工作目录运行下面的命令：

```bash
# Web UI 模式 (windows PowerShell)
cd /test  # 这里替换为你的路径
# XXXX 为可选端口，用于 agent 开发网页时暴露端口（如 5002）
docker run -d --name mla-webui `
  -e HOST_PWD="/project" `      # 环境变量 HOST_PWD
  -v "${PWD}:/workspace/project" `  # 将宿主机工作目录 ${PWD} 映射到容器内的 /workspace/project
  -v "${HOME}\.mla_v3:/root/mla_v3" `   # 映射用户配置目录
  -v "${PWD}\..\mla-config:/mla_config" `  # 映射配置文件目录，这里改成你自己的配置路径
  -p 8002:8002 `
  -p 9641:9641 `
  -p 4242:4242 `
  chenglinhku/mlav3:latest webui
```

我的配置：当前工作目录 `${PWD}` 是 `E:\All_Project\try_Agent\test`，配置路径是 `E:\All_Project\try_Agent\mla-config`。

```bash
docker run -d --name mla-webui `
  -e HOST_PWD="/project" `
  -v "${PWD}:/workspace/project" `
  -v "${HOME}\.mla_v3:/root/mla_v3" `
  -v "E:\All_Project\try_Agent\mla-config:/mla_config" `
  -p 8002:8002 `
  -p 9641:9641 `
  -p 4242:4242 `
  chenglinhku/mlav3:latest webui
```

docker 参数说明：`-v` 用于挂载卷，`-e` 用于设置环境变量，`-p` 用于端口映射。`${PWD}`对应当前目录，即 `/test`，`${HOME}`对应用户主目录。

配置设置界面：http://localhost:9641
然后打开主界面：http://localhost:4242

默认用户名 user
默认密码 password

📖 **[Docker 完整指南](docs/DOCKER_GUIDE.md)**

## 方式2：自行部署WSL+Web UI 模式

在WSL中创建环境:

**1. 安装包**

```bash
# 确保 Python 版本 > 3.10
cd 安装路径
python -m venv venv   #创建虚拟环境
source venv/bin/activate  # Windows: venv\Scripts\activate  #启动虚拟环境venv
git clone https://github.com/ChenglinPoly/infiAgent.git
cd infiAgent
pip install -e .
```

**2. 安装 Playwright**

```bash
playwright install chromium
```

**3. 安装 Web UI 的依赖**

```bash
pip install flask flask-cors
```

或者添加到 `requirements.txt`：

```
flask
flask-cors
```

#### 启动方式

#### 方法 1：使用便捷脚本（推荐）

**注意**：启动脚本会自动启动工具服务器（tool_server_lite），无需手动启动。首次运行时会询问您设置工作空间路径（Workspace Root）。

1. 启动服务器（会自动启动 Web UI 和工具服务器）：

   - 首次运行时会提示输入工作空间路径
   - 直接回车将使用当前目录作为工作空间（与 CLI 模式相同）
   - 或输入绝对路径指定自定义工作空间

   ```bash
   cd web_ui/server
   ./start.sh
   ```

   或者使用统一管理脚本：

   ```bash
   cd web_ui/server
   ./server start
   ```
2. 停止服务器（会同时停止 Web UI 和工具服务器）：

   ```bash
   cd web_ui/server
   ./stop.sh
   ```

   或者：

   ```bash
   cd web_ui/server
   ./server stop
   ```
3. 查看服务器状态：

   ```bash
   cd web_ui/server
   ./server status
   ```

   会显示 Web UI 和工具服务器的运行状态。
4. 重启服务器：

   ```bash
   cd web_ui/server
   ./server restart
   ```
5. 打开浏览器访问：

   ```
   http://localhost:22228
   ```

   **服务器地址**：

   - Web UI: http://localhost:22228
   - 工具服务器 API: http://localhost:24243
   - 工具服务器文档: http://localhost:24243/docs

#### 方法 2：直接运行 Python（传统方式）

**注意**：如果使用此方法，需要手动启动工具服务器。

1. 启动工具服务器（在一个终端）：

   ```bash
   cd tool_server_lite
   python server.py
   ```
2. 启动 Web UI 服务器（在另一个终端）：

   ```bash
   cd web_ui/server
   python server.py
   ```
3. 打开浏览器访问：

   ```
   http://localhost:22228
   ```

📖 **Web UI 使用与界面说明**：详见 [web_ui/README.md](web_ui/README.md)。

## 使用说明

### 工作目录对应

根据配置 `-v "${PWD}:/workspace/project"`，宿主机的工作目录 `${PWD}` 对应容器内的 `/workspace/project`，保持容器内外的文件一致。

以user用户登录后，会在工作目录下产生 `user`目录。创建一个工作空间，会在 `user`下创建一个同名文件夹。

如：在宿主机的 `${PWD}` 下启动docker，创建工作空间 `test_agent`，则容器内路径为 `/workspace/project/user/test_agent`，宿主机路径为 `${PWD}/user/test_agent`。

### agent对话日志存放

windows 下的 `${HOME}\.mla_v3\conversations` 存放了产生的子agent的执行记录，json格式。

工作空间内 `chat_history.json` 存放了主agent的聊天记录。

### 配置文件

配置主要包括两部分：LLM的api配置和agent的config。

**配置持久化：** 在容器中配置的路径是 `mla-config`，在docker启动时指定 `-v E:\All_Project\try_Agent\mla-config:/mla_config`，把配置放在本地的 `E:\All_Project\try_Agent\mla-config` 中，映射到容器内的 `/mla_config`，实现配置持久化。

**LLM的api配置：** `base_url: https://yunwu.ai/v1`，`api_key: your_api_key`，可以在 `mla-config/llm_config.yaml` 中修改。模型选择gemini，需要写成：`openai/gemini-3-pro-preview`，要使用openai接口格式（详细可以参考云雾的文档）。如果用其他模型，需要参考对应模型的api格式进行配置。

该工程采用 LiteLLM 原生，实现LLM调用。

### 启动docker的配置（可以在桌面端设置）

**Ports：**

保持端口映射一致：4242（Web UI），9641（工具服务器），8002（可选端口，用于agent开发网页时暴露端口）。

**Volumes：**

| Source (Host)                              | Destination (Container) |
| ------------------------------------------ | ----------------------- |
| E:\All_Project\try_Agent\test⁠              | /workspace/project      |
| C:\Users\chong/.mla_v3⁠                     | /root/mla_v3            |
| E:\All_Project\try_Agent\mla-config⁠        | /mla_config             |

Environment variables：

| Name       | Value            |
| ---------- | ---------------- |
| HOST_PWD   | /project         |


### LLM api的配置

该配置存放在 `mla-config/llm_config.yaml` 中。

重点配置部分包括：base_url, api_key, model_name。

配置说明：本工程使用了 LiteLLM 作为 LLM 的接口，决定调用哪个api。指定模型时，需要指定使用哪个厂商的接口格式。比如我要使用gemini的模型 `gemini-3-pro-preview`，但是我想用openai chat api的格式调用它，则需要在配置中指定 `model_name: openai/gemini-3-pro-preview`。base_url 配置为云雾的地址 `https://yunwu.ai/v1`。（注意要写到v1）

openai、anthropic、gemini均有不同的接口格式，这涉及到api和请求参数的不同，常见的有如下种类的接口：

- **openai Chat API** `https://yunwu.ai/v1/chat/completions`
- **openai Responses API** （新的 API 原语，是聊天完成的升级版，允许使用内置工具）`https://yunwu.ai/v1/responses`
- **Anthropic Claude 接口** `https://yunwu.ai/v1/messages`
- **gemini 原生接口**
  - 文本生成 `https://yunwu.ai/v1beta/models/gemini-2.5-pro:generateContent`
  - 文本生成（流） `https://yunwu.ai/v1beta/models/gemini-3-pro-preview:streamGenerateContent`
  - 图片生成 `https://yunwu.ai/v1beta/models/gemini-2.5-flash-image-preview:generateContent`
- **gemini chat兼容接口** `https://yunwu.ai/v1/chat/completions` **（类似openai chat api）**

上面的不同的url可以从一个侧面说明不同接口的区别。实际上，各类桌面客户端也是根据厂商不同，内置了不同的api调用方式。

📖详细可以学习云雾的文档 https://yunwu.apifox.cn/doc-5459006

## infiAgent 原理

**tools：** 构造很多工具，比如网络搜索，查论文，读取pdf，md格式转为word等。逻辑代码位于 `tool_server_lite` 目录下。把工具定义提供给LLM，供其选择。
**agents：** 基于工具构造多层次的agent，Level-1的agent完成独立简单的任务，层层调用，最高层次的agent负责整体任务的分解和协调。agent的实现是由LLM完成。
内部调用 LiteLLM 作为 LLM 的接口，决定调用某个tool或子agent，最后整合结果返回给用户。

**如何进行扩展？**
自定义某项特殊任务的agent，可以设计多个Level的agent.

**Claude code？**
可以在claude code中利用subagent和skills，实现类似的功能。

## 建议过程

1、先跑起来（需要了解docker）；其中有一个我写的文档READwzc.md可以参考。
2、配置LLM的api（需要了解调用api是怎么个原理，可以参考云雾api和下面的章节）；
3、尝试官方案例；（B站视频）
4、尝试用中文文章直接翻译成英文文章；
5、尝试开发新的agent，完成诸如将英文文章改成中文专利等任务。
（需要了解的知识：markdown、latex，python编程、docker使用、LLM调用原理、agent原理等）

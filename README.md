# multimodal-voice-assistant

# Multimodal Voice Assistant (多模态语音助手)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

这是一个多模态语音助手项目，旨在通过结合语音、文本等多种交互方式，提供更智能、更便捷的用户体验。

## 项目简介

本项目利用 Python 作为后端核心，结合 Web 技术（JavaScript, HTML, CSS）构建前端界面，实现一个能够理解并响应用户语音指令的智能助手。 "多模态"意味着它可能支持不止一种输入或输出形式，例如：

*   **语音输入/输出**: 用户可以通过麦克风与助手交流。
*   **文本输入/输出**: 用户可以在界面上输入文字，助手也可以通过文本反馈信息。
*   **图像输入** 能通过指令进行截图，调用摄像头，并用这些内容和llm对话。

## 主要功能

*   **实时语音识别 (Real-time Speech Recognition):** 能够捕捉麦克风输入，并将用户的语音实时、准确地转换为文本。
*   **自然语言理解 (Natural Language Understanding - NLU):** 分析转换后的文本，理解用户的意图和关键信息（例如指令、询问的对象、参数等）。
*   **对话管理 (Dialogue Management):** 在多轮交互中维护对话状态和上下文，使对话更加连贯自然。
*   **任务执行与技能调用 (Task Execution & Skill Invocation):** 根据理解的用户意图，执行相应的操作，例如：
    *   **信息查询:** 获取天气预报、时间、百科知识、新闻等。
    *   **媒体控制:** 播放/暂停音乐、调整音量。
    *   **简单助理任务:** 设置提醒、创建待办事项。
*   **语音合成 (Text-to-Speech - TTS):** 将助手的文本回复通过 edge-tts 转换成清晰自然的语音进行播放。
*   **Web 界面交互 (Web Interface Interaction):** 提供一个用户友好的网页界面，可以：
    *   显示语音识别的文本和助手的回复。
    *   允许用户通过文本输入与助手交互。
    *   (可能) 展示图片、链接等多媒体信息。
*   **多模态反馈 (Multimodal Feedback):** 结合语音、文本以及可能的视觉元素（在Web界面上）来呈现信息和交互结果。
*   **图像分析(Image Analysis):** 可以通过pygame.camera调用摄像头或者截图当前页面，并与llm互动获取想要的信息
*   **剪切板提取():** 可以通过pypercli获取剪切板中的文本内容并自动判断是否需要进行执行
*   **上下文管理():** 通过EnhancedConversationContext类管理对话记录，支持记住或者遗忘特定信息，根据相似度判断是否清除旧的上下文，能够根据对话历史生成更相关的回复
*   **日志记录():** 使用rich库美化日志输出，并将日志保存到文件中
*   **网页搜索():** 使用DuckDuckGo搜索用户指定的内容，并返回搜索结果摘要

## 安装指南

**环境要求:**

*   Python 3.x
*   pip (Python 包管理器)
*   (如果前端需要构建) Node.js 和 npm/yarn

**步骤:**

1.  **克隆仓库:**
    ```bash
    git clone https://github.com/HeYiShengXiaoMo-vrkim/multimodal-voice-assistant.git
    cd multimodal-voice-assistant
    ```

2.  **创建并激活虚拟环境 (推荐):**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **安装后端依赖:**

    ```bash
    pip install -r requirements.txt
    ```
  
4.  **安装前端依赖 (如果需要):**
    *(假设你有一个 `package.json` 并且前端代码在 `frontend` 目录)*
    ```bash
    # cd frontend  # 进入前端目录 (如果需要)
    # npm install  # 或者 yarn install
    # npm run build # 如果需要构建步骤
    ```
    *(请根据你的项目结构和前端工具链进行修改)*

5.  **配置 (如果需要):**
    *   检查是否有 `.env.example` 或 `config.py.example` 文件，根据说明创建并配置必要的 API 密钥或设置。

## 如何使用
### 方式一：(有前后端方便观察)

1.  **启动后端服务:**
    ```bash
    python bakend_app.py
    ```
    *   留意终端输出，查看服务运行在哪个地址和端口 (默认 `http://127.0.0.1:5000`)。

2.  **访问前端界面:**
    *   打开你的 Web 浏览器，访问后端服务提供的地址 (例如 `http://127.0.0.1:5000`)。
    *   或者，如果前端是独立服务或需要本地文件打开，请根据项目具体情况操作 (例如直接打开 `index.html` 或访问 `http://localhost:3000` 等)。

3.  **开始交互:**
    *   根据界面提示，使用麦克风或文本框与语音助手进行交互。
  
### 方式二：(直接体验多模态功能)
1.  **直接运行main.py**
    ```bash
    python main.py
    ```
    *   等待项目加载完成后使用`wake_words`加`命令`的方式完成对项目的调用

## 贡献

欢迎对此项目做出贡献！如果你有任何建议或发现 Bug，请随时创建 Issue 或提交 Pull Request。

1.  Fork 本仓库
2.  创建你的 Feature 分支 (`git checkout -b feature/AmazingFeature`)
3.  提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4.  将更改推送到分支 (`git push origin feature/AmazingFeature`)
5.  打开一个 Pull Request

## 许可证

本项目采用 [MIT](LICENSE) 许可证。请查看 `LICENSE` 文件获取详细信息。
*(请确保你的项目中包含一个 `LICENSE` 文件，例如我之前提供的 MIT 许可证模板)*

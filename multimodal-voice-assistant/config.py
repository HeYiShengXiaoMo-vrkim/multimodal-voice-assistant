"""
配置文件，存储 API 密钥、模型名称、唤醒词等。
"""
from pathlib import Path
import tempfile

# --- API 配置 ---
# DeepSeek
DEEPSEEK_API_KEY = "sk-3b30d77c798b43ca9ba331b64f91fad8" # 请替换为你的 DeepSeek API 密钥
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_CHAT_MODEL = "deepseek-chat"
DEEPSEEK_VISION_MODEL = "deepseek-chat" # DeepSeek 可能使用相同模型处理视觉
DEEPSEEK_THINKING_MODEL = "deepseek-Reasoner" # 用于功能判断的模型 (如果需要区分)

# Gemini
GEMINI_API_KEY = "AIzaSyCd1p06Y3QvKo7Q79uo5CBY2ifgjVREpjI" # <--- 在这里替换为你的 Gemini API 密钥
GEMINI_CHAT_MODEL = "gemini-1.5-flash-latest" # 文本模型
GEMINI_VISION_MODEL = "gemini-1.5-flash-latest" # 视觉模型 (Flash 支持多模态)
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com" # 基础 URL (库内部使用)

# --- 选择使用的 LLM ---
# 设置为 'gemini' 或 'deepseek'
ACTIVE_LLM = 'gemini' # <--- 在这里切换 'gemini' 或 'deepseek'

# --- 唤醒词 ---
WAKE_WORD = '请'

# --- 系统消息 ---
# DeepSeek
DEEPSEEK_SYS_MSG = (
    '你是一个多模态 AI 语音助手。你的用户可能会附带一张图片（截图或摄像头捕捉）作为上下文。'
    '任何图片都已经被处理成详细的文本描述，并附加到用户的语音转录文本后面。'
    '请生成最有用、最真实的回复，仔细考虑所有先前生成的文本。'
    '不要期待或请求图片，仅在提供上下文时使用它。'
    '利用所有对话上下文，使你的回复与对话相关。'
    '回复应清晰简洁，避免冗长。'
)
# Gemini
GEMINI_SYS_MSG = (
    "You are a multimodal AI voice assistant. Your user might provide an image (screenshot or webcam capture) as context. "
    "Generate helpful and factual responses, considering all prior text and the image if provided. "
    "Keep your responses concise and relevant to the conversation."
)
# DeepSeek Function Call System Message
DEEPSEEK_FUNC_SYS_MSG = (
    '你是一个 AI 功能调用决策模型。你需要判断为了让语音助手更好地回应用户，'
    '是应该提取用户剪贴板内容、截屏、捕捉摄像头画面，还是不调用任何功能。'
    '摄像头可以假定为面向用户的普通笔记本摄像头。'
    '你只能从以下列表中选择一项进行回复：["extract clipboard", "take screenshot", "capture webcam", "None"]。\n'
    '除了列表中最符合逻辑的选项外，不要回复任何其他内容，也不要解释。请确保功能调用名称与列表中的完全一致。'
)
# Gemini Function Call System Message
GEMINI_FUNC_SYS_MSG = (
    "You are an AI function call decision model. Decide if the assistant should extract clipboard content, take a screenshot, capture the webcam, or do nothing to best respond to the user. "
    "The webcam is a standard laptop webcam facing the user. "
    "Respond with ONLY ONE of the following, exactly as written: ['extract clipboard', 'take screenshot', 'capture webcam', 'None']. "
    "Do not add explanations."
)

# --- Whisper 配置 ---
WHISPER_MODEL_SIZE = 'medium'
# 缓存目录
CACHE_DIR = Path(tempfile.gettempdir()) / "whisper_stt_cache"
CACHE_DIR.mkdir(exist_ok=True)

# --- 其他配置 ---
TEMP_DIR = Path(tempfile.gettempdir())
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
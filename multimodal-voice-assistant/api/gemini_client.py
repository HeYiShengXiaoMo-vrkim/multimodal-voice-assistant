"""
封装 Gemini API 调用。
"""
import google.generativeai as genai
# 导入 protos 以访问 FinishReason
from google.generativeai import protos
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from logger import log
import config
import traceback # 导入 traceback

# 配置 Gemini (在模块加载时执行一次)
try:
    if config.GEMINI_API_KEY and config.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY":
        genai.configure(api_key=config.GEMINI_API_KEY)
        log("Gemini API 已配置。", title="INIT", style="green")
    else:
        log("Gemini API 密钥未设置，无法配置。", title="CONFIG_ERROR", style="bold red")
except Exception as e:
    log(f"配置 Gemini API 时出错: {e}", title="ERROR", style="bold red")

# 配置安全设置 (可选，降低阻塞可能性)
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

def call_gemini_api(prompt_parts, model_name, system_instruction=None):
    """通用的 Gemini API 调用函数"""
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        log("Gemini API 密钥未设置，无法调用。", title="API_ERROR", style="bold red")
        return None
    try:
        log(f"准备调用 Gemini API ({model_name})...", title="API_CALL", style="cyan")
        # 每次调用时创建模型实例，确保使用正确的 system_instruction
        model = genai.GenerativeModel(
            model_name,
            system_instruction=system_instruction,
            safety_settings=safety_settings # 应用安全设置
        )
        # 注意: prompt_parts 应该是 list 类型
        if not isinstance(prompt_parts, list):
            prompt_parts = [prompt_parts]

        response = model.generate_content(prompt_parts)
        log(f"Gemini API 调用完成。", title="API_CALL", style="cyan")

        # 检查是否有候选内容，并处理可能的阻塞
        if response.candidates:
             # 检查完成原因 - 使用 protos.Candidate.FinishReason
             finish_reason = response.candidates[0].finish_reason
             # 使用枚举成员进行比较
             if finish_reason == protos.Candidate.FinishReason.STOP:
                 return response.text # 直接返回文本内容
             elif finish_reason == protos.Candidate.FinishReason.MAX_TOKENS:
                 log("Gemini API 调用因达到最大 Token 数而停止。", title="API_WARNING", style="yellow")
                 return response.text # 仍然返回部分内容
             else:
                 # 使用 .name 获取枚举名称字符串
                 log(f"Gemini API 调用未正常完成，原因: {protos.Candidate.FinishReason(finish_reason).name}", title="API_WARNING", style="yellow")
                 # 尝试获取部分内容
                 try:
                     return response.text
                 except ValueError:
                     log(f"Gemini 响应中无有效文本内容。阻塞详情: {response.prompt_feedback}", title="API_ERROR", style="bold red")
                     return None
        else:
             # 处理没有候选内容的情况，通常是因为 prompt feedback 阻塞
             log(f"Gemini API 未返回候选内容。阻塞详情: {response.prompt_feedback}", title="API_ERROR", style="bold red")
             return None

    except Exception as e:
        log(f"调用 Gemini API 时出错 ({model_name}): {e}", title="API_ERROR", style="bold red")
        # 可以在这里添加更详细的错误处理，例如网络错误 vs API 错误
        log(traceback.format_exc(), title="TRACEBACK", style="dim white")
        return None

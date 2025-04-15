"""
提供统一的 LLM 调用接口，根据配置选择 DeepSeek 或 Gemini。
"""
import base64
from logger import log
import config
from conversation import EnhancedConversationContext # 需要类型提示
from api import deepseek_client, gemini_client

def llm_prompt(conversation_context: EnhancedConversationContext, prompt: str, img_base64: str | None = None):
    """根据 ACTIVE_LLM 选择调用 DeepSeek 或 Gemini"""
    if config.ACTIVE_LLM == 'gemini':
        return gemini_prompt(conversation_context, prompt, img_base64)
    elif config.ACTIVE_LLM == 'deepseek':
        return deepseek_prompt(conversation_context, prompt, img_base64)
    else:
        log(f"未知的 ACTIVE_LLM 设置: {config.ACTIVE_LLM}", title="ERROR", style="bold red")
        return "抱歉，LLM 配置错误。"

def deepseek_prompt(conversation_context: EnhancedConversationContext, prompt: str, img_base64: str | None = None):
    """向 DeepSeek 发送提示"""
    # DeepSeek 的 messages 包含 system + history + new user prompt
    messages = [{'role': 'system', 'content': config.DEEPSEEK_SYS_MSG}]
    messages.extend(conversation_context.get_context()) # 添加历史记录

    user_content_list = [{"type": "text", "text": prompt}] # 新的用户提示总是文本

    if img_base64:
        user_content_list.append({
             "type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
        })
        log("已添加图片上下文到 DeepSeek 提示", title="LLM_PROMPT", style="blue")
        model_to_use = config.DEEPSEEK_VISION_MODEL
    else:
        model_to_use = config.DEEPSEEK_CHAT_MODEL

    messages.append({'role': 'user', 'content': user_content_list}) # 添加当前用户输入

    response_message = deepseek_client.call_deepseek_api(messages, model_to_use)

    if response_message and response_message.get("content"):
        response_content = response_message["content"]
        # 注意：添加交互应在主回调函数中进行，以确保 user_input 是原始输入
        # conversation_context.add_exchange(prompt, response_content) # 不在此处添加
        return response_content
    else:
        return "抱歉，我在处理你的 DeepSeek 请求时遇到了问题。"

def gemini_prompt(conversation_context: EnhancedConversationContext, prompt: str, img_base64: str | None = None):
    """向 Gemini 发送提示"""
    # Gemini 的 prompt 可以是简单的文本 + 图片列表
    context_str = conversation_context.get_formatted_context_string()
    prompt_with_history = f"Previous conversation:\n{context_str}\n\nUser prompt: {prompt}" if context_str else f"User prompt: {prompt}"

    prompt_parts = [prompt_with_history] # 开始部分是文本
    model_to_use = config.GEMINI_CHAT_MODEL

    if img_base64:
        try:
            image_bytes = base64.b64decode(img_base64)
            image_part = {
                "mime_type": "image/jpeg",
                "data": image_bytes
            }
            prompt_parts.append(image_part) # 添加图片部分
            model_to_use = config.GEMINI_VISION_MODEL # 切换到视觉模型
            log("已添加图片上下文到 Gemini 提示", title="LLM_PROMPT", style="blue")
        except Exception as e:
            log(f"处理 Gemini 图片时出错: {e}", title="ERROR", style="bold red")
            prompt_parts.append("\n\n(System note: Image processing failed)")

    # 调用 Gemini API
    response_content = gemini_client.call_gemini_api(prompt_parts, model_to_use, system_instruction=config.GEMINI_SYS_MSG)

    if response_content:
        # conversation_context.add_exchange(prompt, response_content) # 不在此处添加
        return response_content
    else:
        return "Sorry, I encountered an issue while processing your Gemini request."


def function_call(prompt: str):
    """根据 ACTIVE_LLM 选择调用 DeepSeek 或 Gemini 进行功能判断"""
    if config.ACTIVE_LLM == 'gemini':
        return gemini_function_call(prompt)
    elif config.ACTIVE_LLM == 'deepseek':
        return deepseek_function_call(prompt)
    else:
        log(f"未知的 ACTIVE_LLM 设置: {config.ACTIVE_LLM}", title="ERROR", style="bold red")
        return "none"

def deepseek_function_call(prompt: str):
    """使用 DeepSeek 判断功能调用"""
    messages = [{"role": "system", "content": config.DEEPSEEK_FUNC_SYS_MSG}, {"role": "user", "content": prompt}]
    # 通常使用基础聊天模型进行功能判断
    response_message = deepseek_client.call_deepseek_api(messages, config.DEEPSEEK_CHAT_MODEL)

    if response_message and response_message.get("content"):
        response_raw = response_message["content"].strip()
        # 移除可能的引号
        if (response_raw.startswith('"') and response_raw.endswith('"')) or \
           (response_raw.startswith("'") and response_raw.endswith("'")):
            response_text = response_raw[1:-1].strip().lower()
        else:
            response_text = response_raw.lower()

        allowed_calls = ["extract clipboard", "take screenshot", "capture webcam", "none"]
        if response_text in allowed_calls:
            log(f"DeepSeek 功能调用决策: {response_text}", title="FUNCTION_CALL", style="yellow")
            return response_text
        else:
            log(f"DeepSeek 功能调用返回无效选项 (原始: '{response_message['content']}', 处理后: '{response_text}')", title="WARNING", style="yellow")
            return "none"
    else:
        log("DeepSeek 功能调用决策失败", title="ERROR", style="bold red")
        return "none"

def gemini_function_call(prompt: str):
    """使用 Gemini 判断功能调用"""
    prompt_parts = [prompt] # Gemini 不需要 role
    response_text_raw = gemini_client.call_gemini_api(
        prompt_parts,
        config.GEMINI_CHAT_MODEL, # 使用基础聊天模型
        system_instruction=config.GEMINI_FUNC_SYS_MSG
    )

    if response_text_raw:
        response_text = response_text_raw.strip().lower()
        # 尝试去除可能的引号或 Markdown 格式
        response_text = response_text.strip('"`\'')

        allowed_calls = ["extract clipboard", "take screenshot", "capture webcam", "none"]
        if response_text in allowed_calls:
            log(f"Gemini 功能调用决策: {response_text}", title="FUNCTION_CALL", style="yellow")
            return response_text
        else:
            log(f"Gemini 功能调用返回无效选项 (原始: '{response_text_raw}', 处理后: '{response_text}')", title="WARNING", style="yellow")
            return "none"
    else:
        log("Gemini 功能调用决策失败", title="ERROR", style="bold red")
        return "none"

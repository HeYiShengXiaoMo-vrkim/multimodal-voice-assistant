"""
封装 DeepSeek API 调用。
"""
import requests
from logger import log
import config

def call_deepseek_api(messages, model_name):
    """通用的 DeepSeek API 调用函数"""
    headers = {
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": messages,
        "max_tokens": 1536,
        "temperature": 0.7,
    }
    api_url = f"{config.DEEPSEEK_BASE_URL}/chat/completions"
    try:
        log(f"准备调用 DeepSeek API ({model_name})...", title="API_CALL", style="cyan")
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        log(f"DeepSeek API 调用完成。", title="API_CALL", style="cyan")
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"] # 返回消息对象 {role: 'assistant', content: '...'}
        else:
            log(f"DeepSeek API 返回无效响应: {result}", title="API_ERROR", style="bold red")
            return None
    except requests.exceptions.Timeout:
        log(f"调用 DeepSeek API 超时 ({api_url})", title="API_ERROR", style="bold red")
        return None
    except requests.exceptions.RequestException as e:
        log(f"调用 DeepSeek API 时出错 ({api_url}): {e}", title="API_ERROR", style="bold red")
        return None
    except Exception as e:
        log(f"处理 DeepSeek API 响应时出错: {e}", title="ERROR", style="bold red")
        return None
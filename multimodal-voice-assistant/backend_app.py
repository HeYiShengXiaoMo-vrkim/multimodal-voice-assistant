from flask import Flask, request, jsonify, send_from_directory
import os
import traceback

# --- 导入你的助手核心逻辑 ---
# (假设你的模块化代码结构如之前建议)
import config
from logger import log, save_log # 导入日志
from conversation import EnhancedConversationContext
# from audio import stt, tts # 后端可能不需要直接处理音频 I/O
from input_handler import take_screenshot, web_cam_capture, get_clipboard_text, encode_image
from web_search import duckduckgo_search, process_search_results
from llm_interface import llm_prompt, function_call

# --- 初始化 Flask 应用 ---
app = Flask(__name__, static_folder='voice-assistant-frontend', static_url_path='')

# --- 初始化助手组件 ---
# (这些组件现在由后端管理，而不是在 main.py 的监听循环中)
try:
    conversation_context = EnhancedConversationContext()
    log("后端应用启动，对话上下文已初始化。", title="BACKEND_INIT", style="green")
    # 可以在这里预加载模型或进行其他初始化，如果需要的话
except Exception as e:
    log(f"后端初始化助手组件时出错: {e}", title="BACKEND_ERROR", style="bold red")
    # 根据错误严重性决定是否退出
    # exit()

# --- 核心处理函数 (改编自 main.py 的 callback 逻辑) ---
def handle_command(command_text):
    """处理来自前端的文本指令"""
    log(f'收到指令: {command_text}', title="API_REQUEST", style="bold green")
    response_text = ""
    image_data_base64 = None # 用于存储可能的图片数据

    try:
        # --- 处理特殊指令 ---
        if command_text.lower().startswith("记住 "):
            info_to_remember = command_text[len("记住 "):].strip()
            if info_to_remember:
                conversation_context.remember(info_to_remember)
                response_text = "好的，我记住这条信息了。" if config.ACTIVE_LLM == 'deepseek' else "Okay, I've remembered that."
            else:
                response_text = "请告诉我需要记住什么。" if config.ACTIVE_LLM == 'deepseek' else "Please tell me what to remember."
        elif command_text.lower() in ["忘记所有", "清除记忆", "忘记刚才说的"]:
            response_text = conversation_context.forget()
        elif command_text.lower().startswith("搜索 "):
            search_query = command_text[len("搜索 "):].strip()
            if search_query:
                search_results = duckduckgo_search(search_query)
                processed_results = process_search_results(search_results)
                if config.ACTIVE_LLM == 'gemini':
                    llm_input_prompt = f"Please answer the user's question about '{search_query}' based on the following search results:\n\n{processed_results}"
                else:
                    llm_input_prompt = f"请根据以下搜索结果回答用户关于 '{search_query}' 的问题:\n\n{processed_results}"
                response_text = llm_prompt(conversation_context, llm_input_prompt)
            else:
                response_text = "请告诉我需要搜索什么内容。" if config.ACTIVE_LLM == 'deepseek' else "Please tell me what you want to search for."

        # --- 常规处理流程 ---
        else:
            call = function_call(command_text)
            img_base64_for_llm = None
            clipboard_context = None
            photo_path_to_delete = None # 追踪临时文件

            if 'take screenshot' in call:
                photo_path = take_screenshot()
                if photo_path:
                    img_base64_for_llm = encode_image(photo_path)
                    image_data_base64 = img_base64_for_llm # 将截图数据也传给前端（如果需要）
                    photo_path_to_delete = photo_path
                else:
                    error_msg = "(系统提示: 截图操作失败)" if config.ACTIVE_LLM == 'deepseek' else "\n\n(System note: Screenshot failed)"
                    command_text += error_msg
            elif 'capture webcam' in call:
                photo_path = web_cam_capture()
                if photo_path:
                    img_base64_for_llm = encode_image(photo_path)
                    image_data_base64 = img_base64_for_llm # 将摄像头数据也传给前端
                    photo_path_to_delete = photo_path
                else:
                    error_msg = "(系统提示: 摄像头捕捉失败)" if config.ACTIVE_LLM == 'deepseek' else "\n\n(System note: Webcam capture failed)"
                    command_text += error_msg
            elif 'extract clipboard' in call:
                paste = get_clipboard_text()
                if paste:
                    if config.ACTIVE_LLM == 'gemini':
                         clipboard_context = f'\n\nCurrent clipboard content:\n"""\n{paste}\n"""'
                    else:
                         clipboard_context = f'\n\n当前剪贴板内容如下:\n"""\n{paste}\n"""'
                else:
                    clipboard_context = "\n\n(系统提示: 剪贴板为空或无法访问)" if config.ACTIVE_LLM == 'deepseek' else "\n\n(System note: Clipboard is empty or inaccessible)"

            final_prompt = command_text
            if clipboard_context:
                final_prompt += clipboard_context

            response_text = llm_prompt(conversation_context, final_prompt, img_base64=img_base64_for_llm)

            # 添加交互到上下文
            if response_text:
                 conversation_context.add_exchange(command_text, response_text) # 使用原始指令

            # 清理临时图片文件
            if photo_path_to_delete and photo_path_to_delete.exists():
                try:
                    os.remove(photo_path_to_delete)
                    log(f"已删除临时图片文件: {photo_path_to_delete.name}", title="CLEANUP", style="dim")
                except Exception as e_del_img:
                    log(f"删除临时图片文件失败: {e_del_img}", title="WARNING", style="yellow")

        log(f'助手响应: {response_text[:100]}...', title="API_RESPONSE", style="bold magenta")
        return response_text, image_data_base64 # 返回文本和可能的图片数据

    except Exception as e:
        log(f"处理指令时发生错误: {e}", title="API_ERROR", style="bold red")
        log(traceback.format_exc(), title="TRACEBACK", style="dim white")
        # 返回错误信息给前端
        return f"处理指令时发生内部错误: {e}", None


# --- API 端点 ---
@app.route('/api/command', methods=['POST'])
def api_command():
    """接收前端指令并返回响应的 API 端点"""
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({"error": "请求体无效，缺少 'command' 字段"}), 400

    command = data['command']
    # command_type = data.get('type', 'text') # 可以根据类型做不同处理，暂时只用 command

    response_text, image_data = handle_command(command)

    if response_text is None: # 如果处理函数返回 None 表示严重错误
         return jsonify({"error": "处理指令时发生严重内部错误"}), 500

    response_payload = {"response": response_text}
    if image_data:
        # 如果有图片，将其包含在响应中 (例如 Base64 格式)
        response_payload["image_base64"] = image_data
        # 或者可以保存图片并返回 URL，但这更复杂

    return jsonify(response_payload)

# --- 前端文件服务 ---
@app.route('/')
def serve_index():
    """服务前端主页面 index.html"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """服务前端的 CSS, JS 等静态文件"""
    # 检查文件是否存在于 static_folder 中
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path) and not os.path.isdir(file_path):
        return send_from_directory(app.static_folder, path)
    else:
        # 如果不是静态文件请求，可以重定向回首页或返回 404
        return serve_index() # 或者 abort(404)

# --- 运行 Flask 应用 ---
if __name__ == '__main__':
    # 检查 API 密钥 (与 main.py 类似)
    key_to_check = config.GEMINI_API_KEY if config.ACTIVE_LLM == 'gemini' else config.DEEPSEEK_API_KEY
    default_key_gemini = "YOUR_GEMINI_API_KEY"
    default_key_deepseek = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    is_key_missing = False
    if config.ACTIVE_LLM == 'gemini' and (not key_to_check or key_to_check == default_key_gemini):
        is_key_missing = True
    elif config.ACTIVE_LLM == 'deepseek' and (not key_to_check or key_to_check == default_key_deepseek or len(key_to_check) < 10):
        is_key_missing = True

    if is_key_missing:
         log(f"错误: 请在 config.py 中为 {config.ACTIVE_LLM.upper()} 设置有效的 API 密钥。后端服务未启动。", title="CONFIG_ERROR", style="bold red")
         save_log() # 保存日志
    else:
        log("启动 Flask 后端服务器...", title="BACKEND_INIT", style="bold blue")
        # debug=True 会在代码更改时自动重载，方便开发，但生产环境应设为 False
        # host='0.0.0.0' 使服务器可以从局域网其他设备访问
        app.run(debug=True, host='0.0.0.0', port=5000)
        # 程序结束时保存日志 (正常退出时可能不会执行，Ctrl+C 会)
        save_log()

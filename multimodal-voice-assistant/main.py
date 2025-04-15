"""
多模态 AI 语音助手主程序。
负责监听、处理回调、协调各模块。
"""
import speech_recognition as sr
import time
import re
import os
import traceback
import pygame # 用于退出时清理

# 导入自定义模块
import config
from logger import log, save_log
from conversation import EnhancedConversationContext
from audio import preprocessing, stt, tts
from input_handler import take_screenshot, web_cam_capture, get_clipboard_text, encode_image
from web_search import duckduckgo_search, process_search_results
from llm_interface import llm_prompt, function_call

# --- 初始化 ---
# 初始化语音识别器
try:
    r = sr.Recognizer()
    # 调整麦克风设置 (移至 start_listening)
    # r.energy_threshold = 4000
    # r.dynamic_energy_threshold = True
    # r.pause_threshold = 0.8
except Exception as e:
    log(f"初始化 SpeechRecognition Recognizer 失败: {e}", title="ERROR", style="bold red")
    exit()

# 初始化对话上下文管理器
conversation_context = EnhancedConversationContext()

# --- 核心回调逻辑 ---
def extract_prompt(transcribed_text: str, wake_word: str) -> str | None:
    """从转录文本中提取唤醒词之后的有效指令"""
    log(f"语音转文本结果: '{transcribed_text}'", title="DEBUG", style="bold blue")
    pattern = rf'.*?\b{re.escape(wake_word)}[\s,.?!]*([^\s].*)'
    match = re.search(pattern, transcribed_text, re.IGNORECASE | re.DOTALL)
    if match:
        prompt = match.group(1).strip()
        prompt = re.sub(r'[.。，,?？!！]$', '', prompt).strip() # 移除结尾标点
        log(f"提取的指令: '{prompt}'", title="DEBUG", style="bold green")
        return prompt if prompt else None
    else:
        log("未匹配到唤醒词或唤醒词后无指令。", title="INFO", style="yellow")
        return None

def callback(recognizer, audio):
    """语音识别回调函数"""
    prompt_audio_path = config.TEMP_DIR / f"prompt_{int(time.time())}.wav"
    processed_audio_path = None
    photo_path_to_delete = None # 用于追踪需要删除的图片

    try:
        # 1. 保存原始录音
        with open(prompt_audio_path, 'wb') as f:
            f.write(audio.get_wav_data())
        log(f"临时录音已保存: {prompt_audio_path.name}", title="AUDIO", style="cyan")

        # 2. 预处理音频
        processed_audio_path = preprocessing.preprocess_audio(prompt_audio_path)

        # 3. 语音转文本
        prompt_text = stt.wav_to_text(processed_audio_path)
        if not prompt_text: # STT 失败或为空
            return

        # 4. 提取指令
        clean_prompt = extract_prompt(prompt_text, config.WAKE_WORD)
        if not clean_prompt: # 未提取到有效指令
            return

        log(f'用户: {clean_prompt}', title="USER_INPUT", style="bold green")
        response = "" # 初始化响应

        # 5. 处理特殊指令 (非 LLM)
        if clean_prompt.lower().startswith("记住 "):
            info_to_remember = clean_prompt[len("记住 "):].strip()
            if info_to_remember:
                conversation_context.remember(info_to_remember)
                response = "好的，我记住这条信息了。" if config.ACTIVE_LLM == 'deepseek' else "Okay, I've remembered that."
            else:
                response = "请告诉我需要记住什么。" if config.ACTIVE_LLM == 'deepseek' else "Please tell me what to remember."
        elif clean_prompt.lower() in ["忘记所有", "清除记忆", "忘记刚才说的"]:
            response = conversation_context.forget() # forget 方法返回确认信息
        elif clean_prompt.lower().startswith("搜索 "):
            search_query = clean_prompt[len("搜索 "):].strip()
            if search_query:
                search_results = duckduckgo_search(search_query)
                processed_results = process_search_results(search_results)
                # 构造给 LLM 的提示，包含搜索结果
                if config.ACTIVE_LLM == 'gemini':
                    llm_input_prompt = f"Please answer the user's question about '{search_query}' based on the following search results:\n\n{processed_results}"
                else:
                    llm_input_prompt = f"请根据以下搜索结果回答用户关于 '{search_query}' 的问题:\n\n{processed_results}"
                # 调用 LLM 处理搜索结果
                response = llm_prompt(conversation_context, llm_input_prompt)
            else:
                response = "请告诉我需要搜索什么内容。" if config.ACTIVE_LLM == 'deepseek' else "Please tell me what you want to search for."

        # 6. 常规处理流程 (调用 LLM)
        else:
            # a. 判断是否需要功能调用
            call = function_call(clean_prompt)
            img_base64 = None
            clipboard_context = None

            # b. 执行功能调用 (如果需要)
            if 'take screenshot' in call:
                photo_path = take_screenshot()
                if photo_path:
                    img_base64 = encode_image(photo_path)
                    photo_path_to_delete = photo_path # 记录待删除路径
                else:
                    error_msg = "(系统提示: 截图操作失败)" if config.ACTIVE_LLM == 'deepseek' else "\n\n(System note: Screenshot failed)"
                    clean_prompt += error_msg
            elif 'capture webcam' in call:
                photo_path = web_cam_capture()
                if photo_path:
                    img_base64 = encode_image(photo_path)
                    photo_path_to_delete = photo_path
                else:
                    error_msg = "(系统提示: 摄像头捕捉失败)" if config.ACTIVE_LLM == 'deepseek' else "\n\n(System note: Webcam capture failed)"
                    clean_prompt += error_msg
            elif 'extract clipboard' in call:
                paste = get_clipboard_text()
                if paste:
                    if config.ACTIVE_LLM == 'gemini':
                         clipboard_context = f'\n\nCurrent clipboard content:\n"""\n{paste}\n"""'
                    else:
                         clipboard_context = f'\n\n当前剪贴板内容如下:\n"""\n{paste}\n"""'
                else:
                    clipboard_context = "\n\n(系统提示: 剪贴板为空或无法访问)" if config.ACTIVE_LLM == 'deepseek' else "\n\n(System note: Clipboard is empty or inaccessible)"

            # c. 构造最终 Prompt
            final_prompt = clean_prompt
            if clipboard_context:
                final_prompt += clipboard_context

            # d. 调用 LLM 获取响应
            response = llm_prompt(conversation_context, final_prompt, img_base64=img_base64)

            # e. 添加本次交互到上下文 (在获取响应之后)
            # 使用原始的 clean_prompt 和最终的 response
            if response: # 只有在成功获取响应后才添加
                 conversation_context.add_exchange(clean_prompt, response)


        # 7. 记录并读出响应
        if response: # 确保有响应内容
            log(f'助手 ({config.ACTIVE_LLM.upper()}): {response}', title="ASSISTANT_RESPONSE", style="bold magenta")
            tts.speak(response)
        else:
            log("未能从 LLM 获取有效响应。", title="WARNING", style="yellow")
            # 可以选择播放一个默认的错误提示音
            # tts.speak("抱歉，处理时遇到问题。")

    except sr.WaitTimeoutError:
        log("录音超时，未检测到有效语音。", title="INFO", style="yellow")
    except Exception as e:
        log(f"处理回调时发生错误: {e}", title="ERROR", style="bold red")
        log(traceback.format_exc(), title="TRACEBACK", style="dim white")
    finally:
        # 8. 清理临时文件
        if prompt_audio_path and prompt_audio_path.exists():
            try: os.remove(prompt_audio_path)
            except Exception as e_del: log(f"删除文件 {prompt_audio_path.name} 失败: {e_del}", title="WARNING", style="yellow")
        if processed_audio_path and processed_audio_path.exists() and processed_audio_path != prompt_audio_path:
             try: os.remove(processed_audio_path)
             except Exception as e_del: log(f"删除文件 {processed_audio_path.name} 失败: {e_del}", title="WARNING", style="yellow")
        if photo_path_to_delete and photo_path_to_delete.exists():
             try: os.remove(photo_path_to_delete)
             except Exception as e_del: log(f"删除文件 {photo_path_to_delete.name} 失败: {e_del}", title="WARNING", style="yellow")


# --- 启动监听 ---
def start_listening():
    """启动背景监听"""
    # 检查麦克风
    try:
         mic_list = sr.Microphone.list_microphone_names()
         if not mic_list:
             log("错误: 未检测到任何麦克风设备。", title="ERROR", style="bold red")
             return False # 指示启动失败
         log(f"可用麦克风: {mic_list}", title="INFO", style="dim")
    except Exception as e:
         log(f"检查麦克风时出错: {e}", title="ERROR", style="bold red")
         return False

    # 调整麦克风以适应环境噪音
    log("正在调整麦克风以适应环境噪音 (请保持安静)...", title="ACTION", style="bold blue")
    with sr.Microphone() as source:
        try:
            r.energy_threshold = 4000 # 初始能量阈值
            r.dynamic_energy_threshold = True # 启用动态能量阈值
            r.pause_threshold = 0.8 # 语句结束的停顿时间
            r.adjust_for_ambient_noise(source, duration=1.5)
            log(f"环境噪音调整完毕。能量阈值: {r.energy_threshold:.2f}", title="ACTION", style="bold blue")
        except Exception as e:
            log(f"调整环境噪音时出错: {e}", title="ERROR", style="bold red")
            # 即使调整失败，也尝试继续

    # 打印使用说明
    log(f"请说 '{config.WAKE_WORD}' 加上你的指令。", title="使用说明", style="bold magenta")

    # 启动后台监听
    try:
        # phrase_time_limit: 录制音频片段的最长时间（秒）
        stop_listening = r.listen_in_background(sr.Microphone(), callback, phrase_time_limit=20)
        log("已开始在后台监听...", title="ACTION", style="bold blue")
        return stop_listening # 返回停止函数
    except Exception as e:
        log(f"启动后台监听失败: {e}", title="ERROR", style="bold red")
        return None


# --- 程序入口 ---
if __name__ == "__main__":
    # 检查 API 密钥
    key_to_check = config.GEMINI_API_KEY if config.ACTIVE_LLM == 'gemini' else config.DEEPSEEK_API_KEY
    default_key_gemini = "YOUR_GEMINI_API_KEY"
    default_key_deepseek = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # 示例
    is_key_missing = False

    if config.ACTIVE_LLM == 'gemini' and (not key_to_check or key_to_check == default_key_gemini):
        is_key_missing = True
    elif config.ACTIVE_LLM == 'deepseek' and (not key_to_check or key_to_check == default_key_deepseek or len(key_to_check) < 10): # 简单长度检查
        is_key_missing = True

    if is_key_missing:
         log(f"错误: 请在 config.py 中为 {config.ACTIVE_LLM.upper()} 设置有效的 API 密钥。", title="CONFIG_ERROR", style="bold red")
    else:
        # 启动监听
        stop_listening_func = start_listening()

        if stop_listening_func:
            # 保持主线程运行，直到用户按下 Ctrl+C
            try:
                while True:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                log("收到退出信号 (Ctrl+C)，正在停止...", title="ACTION", style="bold blue")
            except Exception as e:
                 log(f"主循环发生意外错误: {e}", title="CRITICAL_ERROR", style="bold red")
                 log(traceback.format_exc(), title="TRACEBACK", style="dim white")
            finally:
                # 停止监听并保存日志
                if stop_listening_func:
                    stop_listening_func(wait_for_stop=False)
                log("监听已停止。", title="ACTION", style="bold blue")
                save_log()
                # 确保 Pygame 资源被释放
                pygame.quit()
                log("Pygame 已退出。", title="INFO", style="dim")
        else:
             log("程序未能成功启动监听。", title="ERROR", style="bold red")
             save_log() # 即使启动失败也保存日志

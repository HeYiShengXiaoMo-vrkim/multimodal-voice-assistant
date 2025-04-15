"""
文本转语音 (TTS) 功能，使用 edge-tts。
"""
import asyncio
import os
from pathlib import Path
import tempfile
import pygame
from logger import log
import config

# 尝试导入 edge_tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    log("错误: 未安装 edge-tts。无法使用 TTS 功能。", title="ERROR", style="bold red")
    log("请尝试安装: pip install edge-tts", title="INFO", style="yellow")

# 初始化 Pygame Mixer (如果尚未初始化)
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
except pygame.error as e:
    log(f"初始化 Pygame Mixer 失败: {e}", title="WARNING", style="yellow")
    # 即使 Mixer 初始化失败，也允许程序继续，只是无法播放声音

async def _generate_and_play(text: str):
    """异步生成并播放语音"""
    import time
    log("正在生成语音...", title="TTS", style="cyan")
    # 选择语音和语速
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural", rate='+20%')
    temp_file = config.TEMP_DIR / f"response_{int(time.time())}.mp3"

    try:
        await communicate.save(str(temp_file))
        log("语音生成完毕，正在播放...", title="TTS", style="cyan")

        # 检查 Mixer 是否已初始化
        if not pygame.mixer.get_init():
             log("Pygame Mixer 未初始化，无法播放语音。", title="ERROR", style="bold red")
             return

        pygame.mixer.music.load(str(temp_file))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10) # 避免 CPU 占用
        # 不需要手动 quit mixer，除非程序结束
        log("语音播放完毕。", title="TTS", style="cyan")
    except pygame.error as e:
         log(f"播放语音时 Pygame 出错: {e}", title="ERROR", style="bold red")
    except Exception as e:
         log(f"生成或播放语音时出错: {e}", title="ERROR", style="bold red")
    finally:
        # 清理临时文件
        if temp_file.exists():
            try:
                os.remove(temp_file)
            except Exception as e_del:
                log(f"删除临时 TTS 文件失败: {e_del}", title="WARNING", style="yellow")

def speak(text: str):
    """使用 edge-tts 将文本转换为语音并播放 (同步接口)"""
    if not EDGE_TTS_AVAILABLE:
        log("edge-tts 不可用，跳过语音播放。", title="WARNING", style="yellow")
        return
    if not text:
        log("TTS 收到空文本，跳过播放。", title="WARNING", style="yellow")
        return

    try:
        # 获取或创建事件循环
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # 如果在异步环境，创建任务
            asyncio.ensure_future(_generate_and_play(text))
        else:
            # 否则，运行直到完成
            loop.run_until_complete(_generate_and_play(text))
    except Exception as e:
         log(f"运行 TTS 异步任务时出错: {e}", title="ERROR", style="bold red")

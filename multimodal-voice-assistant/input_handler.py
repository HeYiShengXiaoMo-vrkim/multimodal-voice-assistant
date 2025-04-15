"""
处理截图、摄像头捕捉、剪贴板和图像编码。
"""
import base64
import time
from pathlib import Path
import tempfile
from PIL import ImageGrab, Image
import pyperclip
import pygame
import pygame.camera
from logger import log
import config

def take_screenshot() -> Path | None:
    """截取屏幕并保存为低质量 JPG 文件，返回文件路径"""
    log("正在截屏...", title="ACTION", style="bold blue")
    try:
        path = config.TEMP_DIR / f"screenshot_{int(time.time())}.jpg"
        screenshot = ImageGrab.grab()
        rgb_screenshot = screenshot.convert('RGB')
        rgb_screenshot.save(path, quality=15) # 低质量 JPG
        log(f"截屏已保存到 {path}", title="ACTION", style="bold blue")
        return path
    except Exception as e:
        log(f"截屏失败: {e}", title="ERROR", style="bold red")
        return None

def web_cam_capture() -> Path | None:
    """使用 Pygame 捕捉摄像头图像并保存，返回文件路径"""
    log("正在捕捉摄像头图像...", title="ACTION", style="bold blue")
    cam = None # 初始化 cam 变量
    try:
        pygame.camera.init()
        cameras = pygame.camera.list_cameras()

        if not cameras:
            log('错误: 未找到摄像头', title="ERROR", style="bold red")
            pygame.camera.quit()
            return None

        cam = pygame.camera.Camera(cameras[0], (640, 480))
        cam.start()
        time.sleep(0.5) # 等待稳定
        image = cam.get_image()
        cam.stop() # 停止摄像头
        pygame.camera.quit() # 退出摄像头模块

        path = config.TEMP_DIR / f"webcam_{int(time.time())}.jpg"
        pygame.image.save(image, str(path)) # 保存图像

        log(f"摄像头图像已捕捉并保存到 {path}", title="ACTION", style="bold blue")
        return path
    except ImportError:
         log("错误: Pygame 未安装或初始化失败。无法捕捉摄像头。", title="ERROR", style="bold red")
         return None
    except Exception as e:
        log(f'捕捉摄像头图像时出错: {str(e)}', title="ERROR", style="bold red")
        if cam: # 如果摄像头已启动，尝试停止
            try:
                cam.stop()
            except: pass
        try: # 尝试退出摄像头模块
            pygame.camera.quit()
        except: pass
        return None


def get_clipboard_text() -> str | None:
    """获取剪贴板中的文本内容"""
    log("正在提取剪贴板文本...", title="ACTION", style="bold blue")
    try:
        clipboard_content = pyperclip.paste()
        if isinstance(clipboard_content, str) and clipboard_content.strip():
            log("剪贴板文本已提取。", title="ACTION", style="bold blue")
            return clipboard_content[:1500] + '...' if len(clipboard_content) > 1500 else clipboard_content
        else:
            log('剪贴板中没有文本内容', title="INFO", style="yellow")
            return None
    except Exception as e:
        log(f'无法访问剪贴板: {e}', title="ERROR", style="bold red")
        return None


def encode_image(image_path: Path) -> str | None:
    """将图像文件编码为 Base64 字符串"""
    if not image_path or not image_path.exists():
        log(f"错误: 图像文件无效或不存在 {image_path}", title="ERROR", style="bold red")
        return None
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        log(f"编码图像时出错 ({image_path}): {e}", title="ERROR", style="bold red")
        return None

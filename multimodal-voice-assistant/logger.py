"""
日志记录模块，使用 Rich 进行控制台输出，并保存到文件。
"""
import re
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import config # 导入配置以获取 LOG_DIR

# 初始化 Rich Console
console = Console()
log_messages = []

def log(message, title="INFO", style="bold blue"):
    """使用 Rich 在控制台打印格式化的日志消息，并存储到内存"""
    try:
        console.print(Panel(Markdown(f"**{message}**"), border_style=style, expand=False, title=title))
        log_messages.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][{title}] {message}")
    except Exception as e:
        # Fallback to simple print if Rich fails
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}][{title}] {message}")
        print(f"Rich logging failed: {e}")


def save_log():
    """将内存中的日志消息保存到带时间戳的文件中"""
    if not log_messages:
        print("没有日志消息需要保存。")
        return

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = config.LOG_DIR / f"assistant_log_{timestamp}.txt"
    try:
        with open(filename, "w", encoding='utf-8') as f:
            for msg in log_messages:
                # 移除 ANSI 转义码
                clean_message = re.sub(r'\x1b\[.*?m', '', msg)
                f.write(f"{clean_message}\n")
        print(f"日志已保存到 {filename}")
    except Exception as e:
        print(f"保存日志失败: {e}")

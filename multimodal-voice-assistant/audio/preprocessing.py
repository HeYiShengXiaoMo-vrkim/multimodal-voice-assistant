"""
音频预处理功能。
"""
from pathlib import Path
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from pydub.effects import normalize
from logger import log

def preprocess_audio(audio_path: Path) -> Path:
    """对音频进行预处理（归一化），返回处理后的文件路径"""
    if not audio_path or not audio_path.exists():
        log(f"音频预处理失败: 文件不存在 {audio_path}", title="ERROR", style="bold red")
        return audio_path # 返回原路径或 None 可能更好?

    try:
        log(f"正在预处理音频: {audio_path.name}", title="AUDIO_PREP", style="cyan")
        audio = AudioSegment.from_file(audio_path)

        if len(audio) < 100: # 小于 100ms
             log("音频过短，跳过归一化。", title="AUDIO_PREP", style="yellow")
             return audio_path

        # 应用归一化
        normalized_audio = normalize(audio)

        processed_path = audio_path.with_name(f"{audio_path.stem}_processed.wav")
        normalized_audio.export(processed_path, format="wav")
        log(f"音频预处理完成: {processed_path.name}", title="AUDIO_PREP", style="cyan")
        return processed_path
    except CouldntDecodeError:
        log(f"音频预处理失败: 无法解码文件 {audio_path.name}", title="ERROR", style="bold red")
        return audio_path
    except Exception as e:
        log(f"音频预处理失败 ({audio_path.name}): {e}", title="ERROR", style="bold red")
        return audio_path
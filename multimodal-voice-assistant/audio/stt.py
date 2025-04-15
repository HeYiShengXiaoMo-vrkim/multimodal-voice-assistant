"""
语音转文本 (STT) 功能，使用 Faster Whisper 和缓存。
"""
import os
import hashlib
import json
from pathlib import Path
from faster_whisper import WhisperModel
import opencc
from logger import log
import config

# 初始化 Whisper 模型 (在模块加载时执行)
whisper_model = None
try:
    num_cores = os.cpu_count() or 1
    # 尝试 GPU
    whisper_model = WhisperModel(config.WHISPER_MODEL_SIZE, device='cuda', compute_type='int8')
    log(f"Whisper 模型 '{config.WHISPER_MODEL_SIZE}' 加载成功 (使用 GPU)", title="INIT", style="green")
except Exception as e:
    log(f"加载 Whisper GPU 模型失败: {e}. 尝试使用 CPU...", title="WARNING", style="yellow")
    try:
        # 回退 CPU
        whisper_model = WhisperModel(config.WHISPER_MODEL_SIZE, device='cpu', compute_type='int8', cpu_threads=num_cores // 2, num_workers=num_cores // 2)
        log(f"Whisper 模型 '{config.WHISPER_MODEL_SIZE}' 加载成功 (使用 CPU)", title="INIT", style="green")
    except Exception as e_cpu:
        log(f"加载 Whisper CPU 模型失败: {e_cpu}", title="ERROR", style="bold red")
        # 程序无法在没有 STT 的情况下运行，可以选择退出或抛出异常
        raise RuntimeError("无法加载 Whisper 模型，程序无法继续。") from e_cpu

# 创建 OpenCC 转换器实例 (繁体到简体)
cc = opencc.OpenCC('t2s.json')

def _load_stt_cache(audio_path: Path, model_size: str) -> dict | None:
    """加载缓存的 Whisper 转录结果"""
    if not audio_path or not audio_path.exists():
        return None
    try:
        cache_key = hashlib.md5(audio_path.read_bytes()).hexdigest()
        cache_file = config.CACHE_DIR / f"{cache_key}_{model_size}.json"
        if cache_file.is_file():
            with cache_file.open("r", encoding="utf-8") as f:
                cached_data = json.load(f)
            if cached_data.get("model_size") == model_size:
                log(f"使用缓存的 STT 结果: {cache_file.name}", title="CACHE", style="green")
                return cached_data
            else:
                log("STT 缓存模型大小不匹配，忽略缓存。", title="CACHE", style="yellow")
    except Exception as e:
        log(f"加载 STT 缓存失败 ({audio_path.name}): {e}", title="ERROR", style="bold red")
    return None

def _save_stt_cache(audio_path: Path, model_size: str, result: dict):
    """保存 Whisper 转录结果到缓存"""
    if not audio_path or not audio_path.exists():
        return
    try:
        cache_key = hashlib.md5(audio_path.read_bytes()).hexdigest()
        cache_file = config.CACHE_DIR / f"{cache_key}_{model_size}.json"
        result["model_size"] = model_size
        with cache_file.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log(f"STT 结果已缓存: {cache_file.name}", title="CACHE", style="green")
    except Exception as e:
        log(f"保存 STT 缓存失败 ({audio_path.name}): {e}", title="ERROR", style="bold red")

def wav_to_text(audio_path: Path) -> str:
    """使用 Faster Whisper 将 WAV 音频文件转换为文本，使用缓存，并转换为简体中文"""
    if whisper_model is None:
        log("Whisper 模型未加载，无法进行语音识别。", title="ERROR", style="bold red")
        return ""
    if not audio_path or not audio_path.exists():
        log(f"语音识别失败: 音频文件无效或不存在 {audio_path}", title="ERROR", style="bold red")
        return ""

    try:
        log("正在进行语音识别...", title="STT", style="blue")

        cached_result = _load_stt_cache(audio_path, config.WHISPER_MODEL_SIZE)
        if cached_result:
            segments = cached_result.get("segments", [])
            text = ''.join(segment.get("text", "") for segment in segments).strip()
            simplified_text = cc.convert(text)
            log(f"识别结果 (缓存): {text}", title="STT_RESULT_CACHE", style="dim")
            log(f"转换为简体 (缓存): {simplified_text}", title="STT_RESULT_SIMPLIFIED", style="dim")
            return simplified_text

        segments_gen, info = whisper_model.transcribe(str(audio_path), language='zh', beam_size=5)
        segments = list(segments_gen) # 转换生成器

        transcription_result = {
            "text": "".join(s.text for s in segments).strip(),
            "segments": [{"start": s.start, "end": s.end, "text": s.text} for s in segments],
            "language": info.language,
            "language_probability": info.language_probability,
        }

        _save_stt_cache(audio_path, config.WHISPER_MODEL_SIZE, transcription_result)

        text = transcription_result["text"]
        log(f"识别结果 (原始): {text}", title="STT_RESULT_ORIGINAL", style="dim")

        simplified_text = cc.convert(text)
        log(f"转换为简体: {simplified_text}", title="STT_RESULT_SIMPLIFIED", style="dim")

        return simplified_text

    except Exception as e:
        log(f"语音识别失败 ({audio_path.name}): {e}", title="ERROR", style="bold red")
        import traceback
        log(traceback.format_exc(), title="TRACEBACK", style="dim white")
        return ""

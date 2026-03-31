import base64
import json
import logging
from typing import Any, Tuple

from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _build_client(timeout_seconds: int | None = None) -> OpenAI:
    settings = get_settings()
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")
    timeout = timeout_seconds if timeout_seconds is not None else settings.qwen_timeout_seconds
    return OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.qwen_base_url,
        timeout=timeout,
        max_retries=settings.qwen_max_retries,
    )


def stream_chat(prompt: str, want_audio: bool) -> Tuple[str, str | None]:
    """Call Qwen Omni via OpenAI兼容接口，严格按官方文档流式调用并拼接结果。"""
    settings = get_settings()
    client = _build_client()
    logger.info(
        "LLM_CALL_START module=stream_chat model=%s want_audio=%s prompt_len=%s timeout=%ss retries=%s",
        settings.qwen_model,
        want_audio,
        len(prompt),
        settings.qwen_timeout_seconds,
        settings.qwen_max_retries,
    )

    text_parts: list[str] = []
    audio_parts: list[str] = []

    try:
        response = client.chat.completions.create(
            model=settings.qwen_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            # Qwen-Omni 要求 stream=True，否则会报错
            stream=True,
            stream_options={"include_usage": True},
            modalities=["text", "audio"] if want_audio else ["text"],
            audio={"voice": settings.qwen_audio_voice, "format": settings.qwen_audio_format}
            if want_audio
            else None,
        )

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                text_parts.append(delta.content)
            if want_audio and delta and hasattr(delta, "audio") and delta.audio:
                audio_parts.append(delta.audio.get("data", ""))
    except Exception:
        logger.exception(
            "LLM_CALL_ERROR module=stream_chat model=%s want_audio=%s",
            settings.qwen_model,
            want_audio,
        )
        raise

    text = "".join(text_parts).strip()
    audio_b64 = "".join(audio_parts) if want_audio and audio_parts else None
    logger.info(
        "LLM_CALL_OK module=stream_chat model=%s text_len=%s audio_returned=%s",
        settings.qwen_model,
        len(text),
        bool(audio_b64),
    )
    return text, audio_b64


def text_chat(prompt: str, timeout_seconds: int | None = None) -> str:
    """Call Qwen Text-only model (qwen-plus) for pure text generation without audio."""
    settings = get_settings()
    effective_timeout = timeout_seconds if timeout_seconds is not None else settings.qwen_timeout_seconds
    client = _build_client(timeout_seconds=effective_timeout)
    logger.info(
        "LLM_CALL_START module=text_chat model=%s prompt_len=%s timeout=%ss retries=%s",
        settings.qwen_text_model,
        len(prompt),
        effective_timeout,
        settings.qwen_max_retries,
    )

    text_parts: list[str] = []
    try:
        response = client.chat.completions.create(
            model=settings.qwen_text_model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=True,
            stream_options={"include_usage": True},
        )

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                text_parts.append(delta.content)
    except Exception:
        logger.exception(
            "LLM_CALL_ERROR module=text_chat model=%s",
            settings.qwen_text_model,
        )
        raise

    text = "".join(text_parts).strip()
    logger.info(
        "LLM_CALL_OK module=text_chat model=%s text_len=%s",
        settings.qwen_text_model,
        len(text),
    )
    return text


def _delta_to_text(delta: Any) -> str:
    if delta is None or not getattr(delta, "content", None):
        return ""
    content = delta.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                continue
            text = getattr(item, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)
    return ""


def _extract_json(raw: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(raw[start : end + 1])
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def generate_card_from_audio(audio_bytes: bytes, audio_format: str) -> tuple[str, str, list[str], str]:
    settings = get_settings()
    client = _build_client()
    logger.info(
        "LLM_CALL_START module=generate_card_from_audio model=%s audio_format=%s audio_bytes=%s timeout=%ss retries=%s",
        settings.qwen_model,
        audio_format,
        len(audio_bytes),
        settings.qwen_timeout_seconds,
        settings.qwen_max_retries,
    )

    encoded = base64.b64encode(audio_bytes).decode("utf-8")
    fmt = (audio_format or "wav").strip().lower()
    if fmt == "mp3":
        mime = "audio/mpeg"
    elif fmt in {"m4a", "aac"}:
        mime = "audio/aac"
    else:
        mime = f"audio/{fmt}"
    # DashScope validates input_audio.data as URL-like string; local bytes should be sent as data URL.
    data_url = f"data:{mime};base64,{encoded}"
    prompt = (
        "你是学习助手。请先转写音频，再根据内容生成学习卡片。"
        "输出必须是 JSON，字段：transcript(全文转写), front(卡片正面问题), back(卡片背面答案), tags(1-3个中文标签数组)。"
        "不要输出 JSON 之外的任何文字。"
    )

    text_parts: list[str] = []
    try:
        response = client.chat.completions.create(
            model=settings.qwen_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": data_url,
                                "format": fmt,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            stream=True,
            stream_options={"include_usage": True},
            modalities=["text"],
        )

        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            text = _delta_to_text(delta)
            if text:
                text_parts.append(text)
    except Exception:
        logger.exception(
            "LLM_CALL_ERROR module=generate_card_from_audio model=%s audio_format=%s",
            settings.qwen_model,
            audio_format,
        )
        raise

    raw_text = "".join(text_parts).strip()
    payload = _extract_json(raw_text) or {}
    transcript = str(payload.get("transcript") or "").strip()
    front = str(payload.get("front") or "").strip()
    back = str(payload.get("back") or "").strip()
    tags_raw = payload.get("tags") or []
    tags = [str(tag).strip() for tag in tags_raw if str(tag).strip()] if isinstance(tags_raw, list) else []

    if not transcript:
        transcript = raw_text or "语音内容转写失败，请手动编辑"
    if not front:
        front = transcript[:40] if transcript else "语音学习卡片"
    if not back:
        back = transcript
    if not tags:
        tags = ["语音", "AI生成"]

    logger.info(
        "LLM_CALL_OK module=generate_card_from_audio model=%s transcript_len=%s tags=%s",
        settings.qwen_model,
        len(transcript),
        len(tags),
    )

    return front, back, tags, transcript

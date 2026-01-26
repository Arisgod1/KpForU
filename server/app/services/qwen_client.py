from typing import Tuple

from openai import OpenAI

from app.core.config import get_settings


def _build_client() -> OpenAI:
    settings = get_settings()
    if not settings.dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not configured")
    return OpenAI(api_key=settings.dashscope_api_key, base_url=settings.qwen_base_url)


def stream_chat(prompt: str, want_audio: bool) -> Tuple[str, str | None]:
    """Call Qwen Omni via OpenAI兼容接口，严格按官方文档流式调用并拼接结果。"""
    settings = get_settings()
    client = _build_client()

    text_parts: list[str] = []
    audio_parts: list[str] = []

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

    text = "".join(text_parts).strip()
    audio_b64 = "".join(audio_parts) if want_audio and audio_parts else None
    return text, audio_b64

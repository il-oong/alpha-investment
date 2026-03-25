"""Gemini 2.5 Flash API 서비스
모든 AI 에이전트가 공통으로 사용하는 Gemini 호출 래퍼
"""
import json
import logging
from google import genai
from google.genai import types

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def ask_gemini(
    prompt: str,
    system_instruction: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    response_json: bool = False,
) -> str:
    """Gemini에 프롬프트를 보내고 응답을 받는다.

    Args:
        prompt: 사용자 프롬프트
        system_instruction: 시스템 지시사항 (에이전트 페르소나)
        temperature: 창의성 (0.0~2.0)
        max_tokens: 최대 토큰
        response_json: True면 JSON 응답 강제

    Returns:
        Gemini 응답 텍스트
    """
    settings = get_settings()
    client = get_client()

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    if system_instruction:
        config.system_instruction = system_instruction
    if response_json:
        config.response_mime_type = "application/json"

    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=config,
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini API 호출 실패: {e}")
        raise


async def ask_gemini_json(
    prompt: str,
    system_instruction: str | None = None,
    temperature: float = 0.3,
) -> dict:
    """Gemini에 JSON 응답을 요청한다."""
    text = await ask_gemini(
        prompt=prompt,
        system_instruction=system_instruction,
        temperature=temperature,
        response_json=True,
    )
    return json.loads(text)

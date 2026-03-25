"""카카오 알림톡 서비스
5단계 매도 알림 + 서킷브레이커 긴급 알림
"""
import logging
import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

# 알림 레벨별 설정
ALERT_LEVELS = {
    1: {"name": "모니터링", "emoji": "📡", "channel": "app", "description": "RSI 65 → 앱 내 표시"},
    2: {"name": "주의", "emoji": "🟡", "channel": "kakao", "description": "RSI 70 / 목표가 80% → 카톡"},
    3: {"name": "경고", "emoji": "🟠", "channel": "kakao_push", "description": "목표가 1차 / Stage 3 → 카톡+푸시"},
    4: {"name": "위험", "emoji": "🔴", "channel": "kakao_urgent", "description": "악재 80점↑ / 매도 → 긴급"},
    5: {"name": "긴급", "emoji": "🚨", "channel": "kakao_urgent", "description": "손절가 도달 → 즉시 손절"},
}


async def send_kakao_message(message: str) -> bool:
    """카카오톡 나에게 보내기 (알림톡)

    카카오 REST API를 통해 메시지 발송.
    실제 운영 시 카카오 비즈니스 채널 + 알림톡 템플릿 사용 권장.
    """
    settings = get_settings()
    if not settings.kakao_rest_api_key:
        logger.warning("카카오 API 키가 설정되지 않았습니다")
        return False

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://kapi.kakao.com/v2/api/talk/memo/default/send",
                headers={
                    "Authorization": f"Bearer {settings.kakao_rest_api_key}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "template_object": f'{{"object_type":"text","text":"{message}","link":{{"web_url":"","mobile_web_url":""}}}}'
                },
            )
            if resp.status_code == 200:
                logger.info("카카오톡 발송 성공")
                return True
            else:
                logger.error(f"카카오톡 발송 실패: {resp.status_code} {resp.text}")
                return False
    except Exception as e:
        logger.error(f"카카오톡 발송 에러: {e}")
        return False


async def send_alert(
    ticker: str,
    name: str,
    level: int,
    title: str,
    message: str,
) -> bool:
    """레벨별 알림 발송

    Lv1: 앱 내 표시만
    Lv2: 카카오톡
    Lv3: 카카오톡 + 앱 푸시
    Lv4: 긴급 카카오톡
    Lv5: 긴급 카카오톡 (손절 알림)
    """
    level_info = ALERT_LEVELS.get(level, ALERT_LEVELS[1])
    emoji = level_info["emoji"]

    formatted_message = (
        f"{emoji} [{level_info['name']}] {ticker} {name}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{title}\n\n"
        f"{message}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"ALPHA Investment Platform"
    )

    # Lv1은 앱 내 알림만
    if level == 1:
        logger.info(f"[Lv1 앱 알림] {ticker}: {title}")
        return True

    # Lv2 이상은 카카오톡 발송
    return await send_kakao_message(formatted_message)


async def send_circuit_breaker_alert(step: int, analysis: str) -> bool:
    """서킷브레이커 긴급 알림

    STEP 1: 발동 즉시 - 신규 매수 전면 중단
    STEP 2: 1~5분 - Gemini 원인 분석
    STEP 3: 5~15분 - 원인별 대응 전략
    STEP 4: 재개 직후 - 사용자 최종 판단 요청
    """
    message = (
        f"🚨🚨🚨 서킷브레이커 발동 🚨🚨🚨\n"
        f"━━━━━━━━━━━━━━━\n"
        f"STEP {step}/4\n\n"
        f"{analysis}\n\n"
        f"⚠️ 즉시 전면 매도는 최악의 선택입니다\n"
        f"반드시 분석 후 판단하세요\n"
        f"━━━━━━━━━━━━━━━\n"
        f"ALPHA Investment Platform"
    )

    return await send_kakao_message(message)


async def send_daily_briefing(briefing_type: str, content: str) -> bool:
    """일일 브리핑 카카오톡 발송"""
    type_labels = {
        "us_close": "🌙 미장 마감 브리핑",
        "morning": "☀️ JKP 오전 전략",
        "noon": "🍽️ 점심 뉴스 브리핑",
        "market_close": "📊 장마감 수급 정리",
        "us_open": "🗽 미장 시작 감시",
    }

    label = type_labels.get(briefing_type, "📋 브리핑")
    message = f"{label}\n━━━━━━━━━━━━━━━\n{content}\n━━━━━━━━━━━━━━━"

    return await send_kakao_message(message)

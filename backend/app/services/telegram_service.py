"""텔레그램 봇 알림 서비스
5단계 매도 알림 + 서킷브레이커 긴급 알림
"""
import logging
import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"

# 알림 레벨별 설정
ALERT_LEVELS = {
    1: {"name": "모니터링", "emoji": "📡", "channel": "app", "description": "RSI 65 → 앱 내 표시"},
    2: {"name": "주의", "emoji": "🟡", "channel": "telegram", "description": "RSI 70 / 목표가 80% → 텔레그램"},
    3: {"name": "경고", "emoji": "🟠", "channel": "telegram", "description": "목표가 1차 / Stage 3 → 텔레그램"},
    4: {"name": "위험", "emoji": "🔴", "channel": "telegram", "description": "악재 80점↑ / 매도 → 긴급"},
    5: {"name": "긴급", "emoji": "🚨", "channel": "telegram", "description": "손절가 도달 → 즉시 손절"},
}


async def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """텔레그램 메시지 발송"""
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("텔레그램 설정이 없습니다 (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")
        return False

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{TELEGRAM_API}/bot{settings.telegram_bot_token}/sendMessage",
                json={
                    "chat_id": settings.telegram_chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                },
            )
            if resp.status_code == 200:
                logger.info("텔레그램 발송 성공")
                return True
            else:
                logger.error(f"텔레그램 발송 실패: {resp.status_code} {resp.text}")
                return False
    except Exception as e:
        logger.error(f"텔레그램 발송 에러: {e}")
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
    Lv2~5: 텔레그램 발송
    """
    level_info = ALERT_LEVELS.get(level, ALERT_LEVELS[1])
    emoji = level_info["emoji"]

    formatted = (
        f"{emoji} <b>[{level_info['name']}] {ticker} {name}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{title}\n\n"
        f"{message}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<i>ALPHA Investment Platform</i>"
    )

    if level == 1:
        logger.info(f"[Lv1 앱 알림] {ticker}: {title}")
        return True

    return await send_telegram_message(formatted)


async def send_circuit_breaker_alert(step: int, analysis: str) -> bool:
    """서킷브레이커 긴급 알림"""
    message = (
        f"🚨🚨🚨 <b>서킷브레이커 발동</b> 🚨🚨🚨\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>STEP {step}/4</b>\n\n"
        f"{analysis}\n\n"
        f"⚠️ 즉시 전면 매도는 최악의 선택입니다\n"
        f"반드시 분석 후 판단하세요\n"
        f"━━━━━━━━━━━━━━━"
    )
    return await send_telegram_message(message)


async def send_daily_briefing(briefing_type: str, content: str) -> bool:
    """일일 브리핑 텔레그램 발송"""
    type_labels = {
        "us_close": "🌙 미장 마감 브리핑",
        "morning": "☀️ JKP 오전 전략",
        "noon": "🍽️ 점심 뉴스 브리핑",
        "market_close": "📊 장마감 수급 정리",
        "us_open": "🗽 미장 시작 감시",
    }

    label = type_labels.get(briefing_type, "📋 브리핑")
    message = f"<b>{label}</b>\n━━━━━━━━━━━━━━━\n{content}\n━━━━━━━━━━━━━━━"

    return await send_telegram_message(message)

"""자동매매 시스템 API
스마트 타임 게이트 & 5단계 안전 등급
"""
from datetime import datetime

from fastapi import APIRouter

from app.services import supabase_service

router = APIRouter()

# 시간대별 위험도
TIME_ZONES = {
    "09:00-09:30": {"level": "danger", "name": "장 초반 급변"},
    "09:30-10:00": {"level": "caution", "name": "변동성 잔존"},
    "10:00-14:30": {"level": "safe", "name": "최적 운용"},
    "14:30-15:00": {"level": "caution", "name": "마감 준비"},
    "15:00-15:30": {"level": "danger", "name": "동시호가 혼란"},
}

# 안전 등급
SAFETY_LEVELS = {
    1: {"name": "Green Zone", "description": "모든 조건 통과 — 자동매매 완전 허용"},
    2: {"name": "Yellow Zone", "description": "일부 경고 — 매수만 허용, 카톡 승인 필요"},
    3: {"name": "Orange Zone", "description": "주의 — 신규 매수 금지, 손절만 자동"},
    4: {"name": "Red Zone", "description": "위험 — 모든 자동매매 중단, 알림만 발송"},
    5: {"name": "Emergency", "description": "서킷브레이커 — 분석 후 사용자 최종 판단"},
}


def get_current_time_zone() -> dict:
    """현재 시간대의 위험도 반환"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    if "09:00" <= current_time < "09:30":
        return {"zone": "09:00-09:30", **TIME_ZONES["09:00-09:30"]}
    elif "09:30" <= current_time < "10:00":
        return {"zone": "09:30-10:00", **TIME_ZONES["09:30-10:00"]}
    elif "10:00" <= current_time < "14:30":
        return {"zone": "10:00-14:30", **TIME_ZONES["10:00-14:30"]}
    elif "14:30" <= current_time < "15:00":
        return {"zone": "14:30-15:00", **TIME_ZONES["14:30-15:00"]}
    elif "15:00" <= current_time < "15:30":
        return {"zone": "15:00-15:30", **TIME_ZONES["15:00-15:30"]}
    else:
        return {"zone": "장외시간", "level": "closed", "name": "장 마감"}


@router.get("/status")
async def trading_status():
    """자동매매 현재 상태"""
    time_zone = get_current_time_zone()
    return {
        "auto_trade_enabled": False,  # Phase 3에서 활성화
        "time_zone": time_zone,
        "safety_levels": SAFETY_LEVELS,
        "note": "자동매매는 Phase 3에서 활성화됩니다",
    }


@router.get("/time-gate")
async def time_gate_status():
    """스마트 타임 게이트 현재 구간"""
    return {
        "current": get_current_time_zone(),
        "zones": TIME_ZONES,
    }


@router.get("/safety-level")
async def safety_level():
    """5단계 안전 등급 현재 레벨"""
    return {
        "current_level": 4,  # Phase 1에서는 Red Zone (자동매매 비활성)
        "levels": SAFETY_LEVELS,
        "note": "Phase 1: 수동 투자 + AI 신호 활용 모드",
    }


@router.get("/circuit-breaker")
async def circuit_breaker_status():
    """서킷브레이커 상태"""
    return {
        "active": False,
        "steps": [
            "STEP 1: 신규 매수 전면 중단 + 예약 취소 + 긴급 알림",
            "STEP 2: Gemini 원인 긴급 분석 (일시적/구조적 판별)",
            "STEP 3: 원인별 대응 전략 결정",
            "STEP 4: 사용자 최종 판단 요청 (전량보유/분할매도/전량매도)",
        ],
        "rules": [
            "시장가 전량 자동매도 — 어떤 경우에도 자동 실행 금지",
            "발동 즉시 패닉 매도 금지 — 서킷브레이커 발동 = 보통 최저점",
            "원인 분석 없는 행동 금지 — 반드시 Gemini 분석 후 판단",
        ],
    }


@router.get("/stats")
async def trading_stats():
    """시간대별 승률 통계"""
    stats = await supabase_service.get_time_slot_stats()
    return {"stats": stats}

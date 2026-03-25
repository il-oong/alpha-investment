"""보유종목 5단계 알림 API"""
from fastapi import APIRouter, Query

from app.services import supabase_service
from app.services.kakao_service import ALERT_LEVELS

router = APIRouter()

# 임시 user_id (추후 인증 시스템으로 교체)
DEFAULT_USER = "default"


@router.get("/")
async def get_alerts(limit: int = Query(50, le=200)):
    """알림 히스토리 조회"""
    alerts = await supabase_service.get_alerts(DEFAULT_USER, limit=limit)
    return {"alerts": alerts}


@router.get("/levels")
async def get_alert_levels():
    """5단계 알림 레벨 설명"""
    return {"levels": ALERT_LEVELS}


@router.get("/settings")
async def get_alert_settings():
    """알림 설정 조회 (단계별 % 커스터마이징)"""
    settings = await supabase_service.get_user_settings(DEFAULT_USER)
    return {"settings": settings}

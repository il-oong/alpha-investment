"""보유종목 5단계 알림 API"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_alerts():
    """알림 히스토리 조회"""
    return {"alerts": [], "status": "not_implemented"}


@router.get("/settings")
async def get_alert_settings():
    """알림 설정 조회 (단계별 % 커스터마이징)"""
    return {"status": "not_implemented"}

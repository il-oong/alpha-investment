"""자동매매 시스템 API"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def trading_status():
    """자동매매 현재 상태 (안전등급, 타임게이트)"""
    return {"status": "not_implemented"}


@router.get("/time-gate")
async def time_gate_status():
    """스마트 타임 게이트 현재 구간"""
    return {"status": "not_implemented"}


@router.get("/safety-level")
async def safety_level():
    """5단계 안전 등급 현재 레벨"""
    return {"status": "not_implemented"}


@router.get("/circuit-breaker")
async def circuit_breaker_status():
    """서킷브레이커 상태"""
    return {"status": "not_implemented"}

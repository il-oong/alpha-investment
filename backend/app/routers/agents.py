"""7개 AI 에이전트 상태 & 리포트 API"""
from fastapi import APIRouter

router = APIRouter()

AGENT_LIST = [
    "macro_sentinel",
    "news_scanner",
    "quant_engine",
    "fundamental_ai",
    "flow_tracker",
    "dark_pool_detector",
    "us_sentinel",
]


@router.get("/")
async def list_agents():
    """에이전트 목록 및 상태"""
    return {"agents": AGENT_LIST, "status": "not_implemented"}


@router.get("/{agent_name}/report")
async def get_agent_report(agent_name: str):
    """특정 에이전트 최신 리포트 조회"""
    return {"agent": agent_name, "report": None, "status": "not_implemented"}

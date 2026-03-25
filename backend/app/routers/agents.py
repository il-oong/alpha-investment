"""7개 AI 에이전트 상태 & 리포트 API"""
from fastapi import APIRouter

from app.agents.jkp_persona import JKPPersona
from app.services import supabase_service

router = APIRouter()
jkp = JKPPersona()


@router.get("/")
async def list_agents():
    """에이전트 목록 및 상태"""
    agents = []
    for name, agent in jkp.agents.items():
        agents.append(agent.to_dict())
    agents.append(jkp.to_dict())
    return {"agents": agents}


@router.get("/{agent_name}/report")
async def get_agent_report(agent_name: str):
    """특정 에이전트 최신 리포트 조회"""
    report = await supabase_service.get_latest_agent_report(agent_name)
    return {"agent": agent_name, "report": report}


@router.post("/{agent_name}/run")
async def run_agent(agent_name: str, ticker: str = "", market: str = "KR"):
    """특정 에이전트 수동 실행"""
    if agent_name == "jkp_persona" and ticker:
        result = await jkp.analyze(ticker=ticker, market=market)
        return {"agent": agent_name, "result": result}

    agent = jkp.agents.get(agent_name)
    if not agent:
        return {"error": f"에이전트 '{agent_name}' 없음"}

    result = await agent.analyze(ticker=ticker, market=market)
    return {"agent": agent_name, "result": result}

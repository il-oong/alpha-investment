from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.routers import analysis, briefing, alerts, portfolio, agents, trading

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="JKP 페르소나 기반 7개 AI 에이전트 통합 투자 분석 시스템",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(briefing.router, prefix="/api/v1/briefing", tags=["Briefing"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(portfolio.router, prefix="/api/v1/portfolio", tags=["Portfolio"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["Trading"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

"""FRED API 서비스
거시경제 데이터: 금리, DXY, 유가, CPI, 실업률 등
"""
import logging
from datetime import datetime, timedelta

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

# 주요 FRED 시리즈 ID
SERIES = {
    "fed_funds_rate": "FEDFUNDS",         # 기준금리
    "us_10y_yield": "DGS10",              # 미국 10년물 국채
    "us_2y_yield": "DGS2",               # 미국 2년물 국채
    "cpi": "CPIAUCSL",                    # 소비자물가지수
    "core_cpi": "CPILFESL",              # 근원 CPI
    "unemployment": "UNRATE",             # 실업률
    "pce": "PCE",                         # 개인소비지출
    "gdp": "GDP",                         # GDP
    "dxy": "DTWEXBGS",                    # 달러인덱스 (광의)
    "wti": "DCOILWTICO",                  # WTI 유가
    "gold": "GOLDAMGBD228NLBM",           # 금 가격
    "vix": "VIXCLS",                      # VIX
    "m2": "M2SL",                         # M2 통화량
    "initial_claims": "ICSA",             # 신규 실업수당 청구
    "retail_sales": "RSXFS",              # 소매판매
}


async def get_series(
    series_id: str,
    days: int = 365,
) -> list[dict]:
    """FRED 시계열 데이터 조회

    Args:
        series_id: FRED 시리즈 ID
        days: 조회 기간 (일)

    Returns:
        [{date, value}, ...]
    """
    settings = get_settings()
    if not settings.fred_api_key:
        logger.warning("FRED API 키가 설정되지 않았습니다")
        return []

    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id": series_id,
                "api_key": settings.fred_api_key,
                "file_type": "json",
                "observation_start": start_date,
                "sort_order": "desc",
            },
        )
        resp.raise_for_status()
        observations = resp.json().get("observations", [])

    results = []
    for obs in observations:
        if obs.get("value") != ".":
            results.append({
                "date": obs["date"],
                "value": float(obs["value"]),
            })
    return results


async def get_latest_value(series_id: str) -> dict | None:
    """FRED 시리즈 최신값 1개"""
    data = await get_series(series_id, days=30)
    return data[0] if data else None


async def get_macro_snapshot() -> dict:
    """거시경제 스냅샷 (주요 지표 최신값 일괄 조회)"""
    snapshot = {}
    key_series = [
        "fed_funds_rate", "us_10y_yield", "us_2y_yield",
        "cpi", "unemployment", "dxy", "wti", "gold", "vix",
    ]

    for name in key_series:
        series_id = SERIES.get(name)
        if series_id:
            try:
                latest = await get_latest_value(series_id)
                snapshot[name] = latest
            except Exception as e:
                logger.error(f"FRED {name} 조회 실패: {e}")
                snapshot[name] = None

    # 장단기 금리차 (10Y - 2Y)
    if snapshot.get("us_10y_yield") and snapshot.get("us_2y_yield"):
        spread = snapshot["us_10y_yield"]["value"] - snapshot["us_2y_yield"]["value"]
        snapshot["yield_spread"] = {
            "value": round(spread, 3),
            "inverted": spread < 0,  # 장단기 역전 여부
        }

    return snapshot


async def get_economic_calendar_data() -> list[dict]:
    """주요 경제 이벤트 일정 (FRED 기반 추정)"""
    # FRED는 캘린더 API가 없으므로, 주요 발표일 패턴으로 추정
    # 실제로는 외부 캘린더 API를 사용하는 것이 좋음
    events = [
        {"event": "FOMC Meeting", "frequency": "6 weeks"},
        {"event": "CPI Release", "frequency": "monthly, ~13th"},
        {"event": "Jobs Report", "frequency": "monthly, 1st Friday"},
        {"event": "GDP Release", "frequency": "quarterly"},
        {"event": "PCE Release", "frequency": "monthly, ~last week"},
    ]
    return events

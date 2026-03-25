"""KIS Open API 서비스 (한국투자증권)
한국 주가 조회, 수급 데이터, 호가, 일별 시세, 주문
"""
import logging
from datetime import datetime, timedelta

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_token: str | None = None
_token_expires: datetime | None = None


async def _get_access_token() -> str:
    """OAuth 액세스 토큰 발급 (24시간 유효)"""
    global _token, _token_expires

    if _token and _token_expires and datetime.now() < _token_expires:
        return _token

    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.kis_base_url}/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": settings.kis_app_key,
                "appsecret": settings.kis_app_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        _token = data["access_token"]
        _token_expires = datetime.now() + timedelta(hours=23)
        return _token


async def _headers() -> dict:
    """공통 API 헤더"""
    settings = get_settings()
    token = await _get_access_token()
    return {
        "authorization": f"Bearer {token}",
        "appkey": settings.kis_app_key,
        "appsecret": settings.kis_app_secret,
        "Content-Type": "application/json; charset=utf-8",
    }


async def get_stock_price(ticker: str) -> dict:
    """현재가 조회

    Returns:
        {price, change, change_pct, volume, high, low, open, prev_close}
    """
    settings = get_settings()
    headers = await _headers()
    headers["tr_id"] = "FHKST01010100"

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kis_base_url}/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=headers,
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker},
        )
        resp.raise_for_status()
        output = resp.json().get("output", {})

    return {
        "ticker": ticker,
        "price": int(output.get("stck_prpr", 0)),
        "change": int(output.get("prdy_vrss", 0)),
        "change_pct": float(output.get("prdy_ctrt", 0)),
        "volume": int(output.get("acml_vol", 0)),
        "high": int(output.get("stck_hgpr", 0)),
        "low": int(output.get("stck_lwpr", 0)),
        "open": int(output.get("stck_oprc", 0)),
        "prev_close": int(output.get("stck_sdpr", 0)),
    }


async def get_daily_prices(ticker: str, days: int = 100) -> list[dict]:
    """일별 시세 조회 (기술적 분석용)

    Returns:
        [{date, open, high, low, close, volume}, ...]
    """
    settings = get_settings()
    headers = await _headers()
    headers["tr_id"] = "FHKST01010400"

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kis_base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            headers=headers,
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": ticker,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0",
            },
        )
        resp.raise_for_status()
        items = resp.json().get("output", [])

    results = []
    for item in items[:days]:
        results.append({
            "date": item.get("stck_bsop_date", ""),
            "open": int(item.get("stck_oprc", 0)),
            "high": int(item.get("stck_hgpr", 0)),
            "low": int(item.get("stck_lwpr", 0)),
            "close": int(item.get("stck_clpr", 0)),
            "volume": int(item.get("acml_vol", 0)),
        })
    return results


async def get_investor_trends(ticker: str) -> dict:
    """투자자별 매매 동향 (외인/기관/개인)

    Returns:
        {foreign_net, institution_net, individual_net, foreign_consecutive_days}
    """
    settings = get_settings()
    headers = await _headers()
    headers["tr_id"] = "FHKST01010900"

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kis_base_url}/uapi/domestic-stock/v1/quotations/inquire-member",
            headers=headers,
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker},
        )
        resp.raise_for_status()
        output = resp.json().get("output", [])

    # 외인 연속 매수일 계산
    foreign_consecutive = 0
    for day in output:
        frgn = int(day.get("frgn_ntby_qty", 0))
        if frgn > 0:
            foreign_consecutive += 1
        else:
            break

    return {
        "ticker": ticker,
        "data": output[:20],
        "foreign_consecutive_days": foreign_consecutive,
    }


async def get_stock_info(ticker: str) -> dict:
    """종목 기본 정보 (PER/PBR/EPS 등)"""
    settings = get_settings()
    headers = await _headers()
    headers["tr_id"] = "FHKST01010100"

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.kis_base_url}/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=headers,
            params={"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": ticker},
        )
        resp.raise_for_status()
        output = resp.json().get("output", {})

    return {
        "ticker": ticker,
        "name": output.get("hts_kor_isnm", ""),
        "per": float(output.get("per", 0)),
        "pbr": float(output.get("pbr", 0)),
        "eps": int(output.get("eps", 0)),
        "market_cap": int(output.get("hts_avls", 0)),  # 시가총액 (억)
        "52w_high": int(output.get("stck_dryy_hgpr", 0)),
        "52w_low": int(output.get("stck_dryy_lwpr", 0)),
    }


# ── 주문 관련 (Phase 3) ───────────────────────────────────

async def place_order(
    account_no: str,
    ticker: str,
    order_type: str,  # "buy" / "sell"
    quantity: int,
    price: int = 0,  # 0이면 시장가
) -> dict:
    """주문 실행 (Phase 3에서 활성화)

    ⚠️ 안전 원칙:
    - 시장가 전량 자동매도 절대 금지
    - AccountGuard 8단계 검증 통과 후에만 실행
    """
    # Phase 3까지 비활성화
    raise NotImplementedError("자동매매는 Phase 3에서 활성화됩니다")

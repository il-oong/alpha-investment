"""Supabase 클라이언트 서비스
PostgreSQL CRUD + 실시간 구독
"""
import logging
from supabase import create_client, Client

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        settings = get_settings()
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


# ── Watchlist ──────────────────────────────────────────────

async def get_watchlist(user_id: str) -> list[dict]:
    sb = get_supabase()
    res = sb.table("watchlist").select("*").eq("user_id", user_id).execute()
    return res.data


async def add_watchlist(user_id: str, ticker: str, market: str = "KR", name: str = "") -> dict:
    sb = get_supabase()
    res = sb.table("watchlist").insert({
        "user_id": user_id,
        "ticker": ticker,
        "market": market,
        "name": name,
    }).execute()
    return res.data[0] if res.data else {}


async def remove_watchlist(user_id: str, ticker: str) -> bool:
    sb = get_supabase()
    sb.table("watchlist").delete().eq("user_id", user_id).eq("ticker", ticker).execute()
    return True


# ── Portfolio ──────────────────────────────────────────────

async def get_portfolio(user_id: str) -> list[dict]:
    sb = get_supabase()
    res = sb.table("portfolio").select("*").eq("user_id", user_id).execute()
    return res.data


async def upsert_portfolio(user_id: str, data: dict) -> dict:
    sb = get_supabase()
    data["user_id"] = user_id
    res = sb.table("portfolio").upsert(data).execute()
    return res.data[0] if res.data else {}


# ── Agent Reports ──────────────────────────────────────────

async def save_agent_report(agent_name: str, ticker: str | None, report: dict, score: float | None = None) -> dict:
    sb = get_supabase()
    res = sb.table("agent_reports").insert({
        "agent_name": agent_name,
        "ticker": ticker,
        "report": report,
        "score": score,
    }).execute()
    return res.data[0] if res.data else {}


async def get_latest_agent_report(agent_name: str, ticker: str | None = None) -> dict | None:
    sb = get_supabase()
    query = sb.table("agent_reports").select("*").eq("agent_name", agent_name)
    if ticker:
        query = query.eq("ticker", ticker)
    res = query.order("created_at", desc=True).limit(1).execute()
    return res.data[0] if res.data else None


# ── Alerts ─────────────────────────────────────────────────

async def save_alert(user_id: str, ticker: str, level: int, title: str, message: str, channel: str = "app") -> dict:
    sb = get_supabase()
    res = sb.table("alerts").insert({
        "user_id": user_id,
        "ticker": ticker,
        "level": level,
        "title": title,
        "message": message,
        "channel": channel,
    }).execute()
    return res.data[0] if res.data else {}


async def get_alerts(user_id: str, limit: int = 50) -> list[dict]:
    sb = get_supabase()
    res = (
        sb.table("alerts")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data


# ── Market Snapshot ────────────────────────────────────────

async def save_market_snapshot(data: dict) -> dict:
    sb = get_supabase()
    res = sb.table("market_snapshot").upsert(data, on_conflict="date").execute()
    return res.data[0] if res.data else {}


async def get_latest_market_snapshot() -> dict | None:
    sb = get_supabase()
    res = sb.table("market_snapshot").select("*").order("date", desc=True).limit(1).execute()
    return res.data[0] if res.data else None


# ── Daily Analysis ─────────────────────────────────────────

async def save_daily_analysis(data: dict) -> dict:
    sb = get_supabase()
    res = sb.table("daily_analysis").upsert(data, on_conflict="ticker,date").execute()
    return res.data[0] if res.data else {}


async def get_daily_analysis(ticker: str, days: int = 30) -> list[dict]:
    sb = get_supabase()
    res = (
        sb.table("daily_analysis")
        .select("*")
        .eq("ticker", ticker)
        .order("date", desc=True)
        .limit(days)
        .execute()
    )
    return res.data


# ── News Feed ──────────────────────────────────────────────

async def save_news(articles: list[dict]) -> list[dict]:
    sb = get_supabase()
    res = sb.table("news_feed").insert(articles).execute()
    return res.data


async def get_recent_news(limit: int = 20) -> list[dict]:
    sb = get_supabase()
    res = (
        sb.table("news_feed")
        .select("*")
        .order("published_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data


# ── User Settings ──────────────────────────────────────────

async def get_user_settings(user_id: str) -> dict | None:
    sb = get_supabase()
    res = sb.table("user_settings").select("*").eq("user_id", user_id).limit(1).execute()
    return res.data[0] if res.data else None


async def upsert_user_settings(user_id: str, data: dict) -> dict:
    sb = get_supabase()
    data["user_id"] = user_id
    res = sb.table("user_settings").upsert(data, on_conflict="user_id").execute()
    return res.data[0] if res.data else {}


# ── Sell Signals ───────────────────────────────────────────

async def save_sell_signal(data: dict) -> dict:
    sb = get_supabase()
    res = sb.table("sell_signals").insert(data).execute()
    return res.data[0] if res.data else {}


# ── Auto Trade Log ─────────────────────────────────────────

async def save_auto_trade_log(data: dict) -> dict:
    sb = get_supabase()
    res = sb.table("auto_trade_log").insert(data).execute()
    return res.data[0] if res.data else {}


# ── Time Slot Stats ────────────────────────────────────────

async def get_time_slot_stats() -> list[dict]:
    sb = get_supabase()
    res = sb.table("time_slot_stats").select("*").order("time_slot").execute()
    return res.data

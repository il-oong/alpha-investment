"""뉴스 RSS 수집 서비스
매경/한경/WSJ/Bloomberg RSS 파싱 + 종목 태깅
"""
import logging
import re
from datetime import datetime
from xml.etree import ElementTree

import httpx

logger = logging.getLogger(__name__)

# RSS 피드 소스
RSS_FEEDS = {
    "매경": "https://www.mk.co.kr/rss/30100041/",
    "한경": "https://www.hankyung.com/feed/stock",
    "WSJ_Markets": "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines",
    "Reuters": "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best",
}

# 제외할 소스가 유효하지 않을 수 있으므로 에러 허용
VALID_FEEDS: dict[str, str] = {}


async def _fetch_rss(url: str, timeout: float = 10.0) -> list[dict]:
    """RSS 피드를 파싱하여 기사 목록 반환"""
    articles = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=timeout, follow_redirects=True)
            resp.raise_for_status()

        root = ElementTree.fromstring(resp.text)

        # RSS 2.0 or Atom
        items = root.findall(".//item") or root.findall(
            ".//{http://www.w3.org/2005/Atom}entry"
        )

        for item in items[:20]:
            title_el = item.find("title") or item.find(
                "{http://www.w3.org/2005/Atom}title"
            )
            link_el = item.find("link") or item.find(
                "{http://www.w3.org/2005/Atom}link"
            )
            pub_el = item.find("pubDate") or item.find(
                "{http://www.w3.org/2005/Atom}published"
            )
            desc_el = item.find("description") or item.find(
                "{http://www.w3.org/2005/Atom}summary"
            )

            title = title_el.text if title_el is not None and title_el.text else ""
            link = ""
            if link_el is not None:
                link = link_el.text or link_el.get("href", "")
            pub_date = pub_el.text if pub_el is not None else ""
            description = desc_el.text if desc_el is not None and desc_el.text else ""
            # HTML 태그 제거
            description = re.sub(r"<[^>]+>", "", description)[:500]

            if title:
                articles.append({
                    "title": title.strip(),
                    "url": link.strip(),
                    "published_at": pub_date,
                    "summary": description.strip(),
                })
    except Exception as e:
        logger.error(f"RSS 파싱 실패 ({url}): {e}")

    return articles


async def fetch_all_news() -> list[dict]:
    """모든 소스에서 뉴스 수집"""
    all_articles = []

    for source, url in RSS_FEEDS.items():
        articles = await _fetch_rss(url)
        for article in articles:
            article["source"] = source
        all_articles.extend(articles)
        logger.info(f"{source}: {len(articles)}건 수집")

    return all_articles


async def fetch_korean_news() -> list[dict]:
    """한국 뉴스만 수집 (매경 + 한경)"""
    articles = []
    for source in ["매경", "한경"]:
        url = RSS_FEEDS.get(source)
        if url:
            fetched = await _fetch_rss(url)
            for a in fetched:
                a["source"] = source
            articles.extend(fetched)
    return articles


async def fetch_global_news() -> list[dict]:
    """글로벌 뉴스만 수집 (WSJ + Reuters)"""
    articles = []
    for source in ["WSJ_Markets", "Reuters"]:
        url = RSS_FEEDS.get(source)
        if url:
            fetched = await _fetch_rss(url)
            for a in fetched:
                a["source"] = source
            articles.extend(fetched)
    return articles

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "ALPHA Investment Platform"
    debug: bool = False

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # Gemini AI
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # KIS (한국투자증권) Open API
    kis_app_key: str = ""
    kis_app_secret: str = ""
    kis_base_url: str = "https://openapi.koreainvestment.com:9443"

    # Alpha Vantage
    alpha_vantage_api_key: str = ""

    # FRED API
    fred_api_key: str = ""

    # Kakao Alert
    kakao_rest_api_key: str = ""
    kakao_redirect_uri: str = ""

    # Trading Safety
    daily_trade_limit: int = 5_000_000  # 일일 최대 거래 한도 (원)
    single_order_limit: int = 1_000_000  # 단일 주문 한도 (원)
    max_stock_weight: float = 0.3  # 종목별 최대 비중 30%

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

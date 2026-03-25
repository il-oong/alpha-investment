-- ALPHA Investment Platform - Initial Schema
-- Supabase PostgreSQL 15개 테이블

-- 1. 관심종목
CREATE TABLE IF NOT EXISTS watchlist (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid(),
    ticker VARCHAR(20) NOT NULL,
    market VARCHAR(10) NOT NULL DEFAULT 'KR', -- KR / US
    name VARCHAR(100),
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    memo TEXT,
    UNIQUE(user_id, ticker)
);

-- 2. 일별 기술적 분석
CREATE TABLE IF NOT EXISTS daily_analysis (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    rsi NUMERIC(6,2),
    macd NUMERIC(12,4),
    macd_signal NUMERIC(12,4),
    bollinger_upper NUMERIC(12,2),
    bollinger_lower NUMERIC(12,2),
    stage INTEGER, -- Weinstein 1~4
    vcp_detected BOOLEAN DEFAULT FALSE,
    volume_ratio NUMERIC(8,2),
    score NUMERIC(5,2), -- 0~100
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(ticker, date)
);

-- 3. 시장 스냅샷 (지수/VIX/환율)
CREATE TABLE IF NOT EXISTS market_snapshot (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL,
    kospi NUMERIC(10,2),
    kosdaq NUMERIC(10,2),
    sp500 NUMERIC(10,2),
    nasdaq NUMERIC(10,2),
    dow NUMERIC(10,2),
    vix NUMERIC(8,2),
    usd_krw NUMERIC(10,2),
    wti NUMERIC(10,2),
    gold NUMERIC(10,2),
    us_10y_yield NUMERIC(6,3),
    fear_greed_index INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(date)
);

-- 4. 뉴스 + 감성분석 + 종목 태깅
CREATE TABLE IF NOT EXISTS news_feed (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    source VARCHAR(50), -- 매경/한경/WSJ/Bloomberg
    url TEXT,
    published_at TIMESTAMPTZ,
    sentiment_score NUMERIC(5,2), -- -100 ~ 100
    tickers TEXT[], -- 관련 종목 배열
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. 알림 히스토리
CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid(),
    ticker VARCHAR(20) NOT NULL,
    level INTEGER NOT NULL CHECK (level BETWEEN 1 AND 5),
    -- Lv1: 앱 표시, Lv2: 카톡, Lv3: 카톡+푸시, Lv4: 긴급, Lv5: 즉시손절
    title VARCHAR(200) NOT NULL,
    message TEXT,
    channel VARCHAR(20) NOT NULL DEFAULT 'app', -- app / kakao / push
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. 보유종목 (매수가/목표가/손절가)
CREATE TABLE IF NOT EXISTS portfolio (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid(),
    account_id BIGINT REFERENCES registered_accounts(id),
    ticker VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    quantity INTEGER NOT NULL DEFAULT 0,
    avg_buy_price NUMERIC(12,2) NOT NULL,
    target_price_1 NUMERIC(12,2), -- 1차 목표가
    target_price_2 NUMERIC(12,2), -- 2차 목표가
    stop_loss_price NUMERIC(12,2), -- 손절가
    current_score NUMERIC(5,2), -- 현재 종합점수
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. 에이전트 분석 리포트
CREATE TABLE IF NOT EXISTS agent_reports (
    id BIGSERIAL PRIMARY KEY,
    agent_name VARCHAR(30) NOT NULL,
    ticker VARCHAR(20), -- NULL이면 시장 전체 분석
    report JSONB NOT NULL, -- 분석 결과 JSON
    score NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. FOMC/CPI 경제 일정
CREATE TABLE IF NOT EXISTS economic_calendar (
    id BIGSERIAL PRIMARY KEY,
    event_name VARCHAR(200) NOT NULL,
    event_date TIMESTAMPTZ NOT NULL,
    importance VARCHAR(10) DEFAULT 'medium', -- low/medium/high
    country VARCHAR(10) DEFAULT 'US',
    actual VARCHAR(50),
    forecast VARCHAR(50),
    previous VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. 매도 신호 로그
CREATE TABLE IF NOT EXISTS sell_signals (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid(),
    ticker VARCHAR(20) NOT NULL,
    signal_level INTEGER NOT NULL CHECK (signal_level BETWEEN 1 AND 5),
    reason TEXT NOT NULL,
    agent_name VARCHAR(30),
    recommended_action VARCHAR(50), -- hold / partial_sell / full_sell / stop_loss
    executed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. 사용자 전체 설정값
CREATE TABLE IF NOT EXISTS user_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE DEFAULT auth.uid(),
    investment_style VARCHAR(20) DEFAULT 'neutral', -- aggressive/neutral/conservative
    target_price_1_pct NUMERIC(5,2) DEFAULT 10.0,
    target_price_2_pct NUMERIC(5,2) DEFAULT 20.0,
    stop_loss_pct NUMERIC(5,2) DEFAULT -7.0,
    rsi_overbought NUMERIC(5,2) DEFAULT 70.0,
    rsi_oversold NUMERIC(5,2) DEFAULT 30.0,
    foreign_consecutive_days INTEGER DEFAULT 3, -- 외인 연속매수 기준일
    -- 트레이더 5인 가중치 (합계 100)
    weight_livermore NUMERIC(5,2) DEFAULT 20.0,
    weight_oneil NUMERIC(5,2) DEFAULT 20.0,
    weight_weinstein NUMERIC(5,2) DEFAULT 20.0,
    weight_minervini NUMERIC(5,2) DEFAULT 20.0,
    weight_lynch NUMERIC(5,2) DEFAULT 20.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 11. 종목별 개별 설정 (오버라이드)
CREATE TABLE IF NOT EXISTS ticker_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid(),
    ticker VARCHAR(20) NOT NULL,
    target_price_1_pct NUMERIC(5,2),
    target_price_2_pct NUMERIC(5,2),
    stop_loss_pct NUMERIC(5,2),
    rsi_overbought NUMERIC(5,2),
    rsi_oversold NUMERIC(5,2),
    memo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, ticker)
);

-- 12. 등록 계좌 (화이트리스트)
CREATE TABLE IF NOT EXISTS registered_accounts (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid(),
    broker VARCHAR(30) NOT NULL, -- KIS / 키움 / 대신
    account_number_encrypted TEXT NOT NULL,
    account_alias VARCHAR(50),
    app_key_encrypted TEXT NOT NULL,
    app_secret_encrypted TEXT NOT NULL,
    is_real BOOLEAN NOT NULL DEFAULT FALSE, -- 실전/모의
    auto_trade_enabled BOOLEAN DEFAULT FALSE,
    daily_limit NUMERIC(15,2) DEFAULT 5000000,
    single_order_limit NUMERIC(15,2) DEFAULT 1000000,
    max_stock_weight NUMERIC(5,2) DEFAULT 30.0,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 13. 계좌별 주문 로그
CREATE TABLE IF NOT EXISTS account_order_log (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES registered_accounts(id),
    ticker VARCHAR(20) NOT NULL,
    order_type VARCHAR(10) NOT NULL, -- buy / sell
    quantity INTEGER NOT NULL,
    price NUMERIC(12,2) NOT NULL,
    total_amount NUMERIC(15,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending/filled/rejected/cancelled
    rejected_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 14. 자동매매 전체 기록 + 실패 DB
CREATE TABLE IF NOT EXISTS auto_trade_log (
    id BIGSERIAL PRIMARY KEY,
    account_id BIGINT NOT NULL REFERENCES registered_accounts(id),
    ticker VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL, -- buy / sell / stop_loss
    safety_level INTEGER NOT NULL, -- 1~5
    time_zone VARCHAR(20), -- safe/caution/danger
    quantity INTEGER,
    price NUMERIC(12,2),
    success BOOLEAN NOT NULL,
    failure_reason TEXT,
    agent_scores JSONB, -- 각 에이전트 점수
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 15. 시간대별 승률 통계
CREATE TABLE IF NOT EXISTS time_slot_stats (
    id BIGSERIAL PRIMARY KEY,
    time_slot VARCHAR(20) NOT NULL, -- e.g. "09:00-09:30"
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    win_rate NUMERIC(5,2) DEFAULT 0,
    avg_return NUMERIC(8,4) DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(time_slot)
);

-- 인덱스
CREATE INDEX idx_daily_analysis_ticker_date ON daily_analysis(ticker, date DESC);
CREATE INDEX idx_news_feed_published ON news_feed(published_at DESC);
CREATE INDEX idx_alerts_user_created ON alerts(user_id, created_at DESC);
CREATE INDEX idx_agent_reports_agent_created ON agent_reports(agent_name, created_at DESC);
CREATE INDEX idx_sell_signals_user_ticker ON sell_signals(user_id, ticker, created_at DESC);
CREATE INDEX idx_auto_trade_log_account ON auto_trade_log(account_id, created_at DESC);

-- RLS (Row Level Security)
ALTER TABLE watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticker_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE registered_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sell_signals ENABLE ROW LEVEL SECURITY;

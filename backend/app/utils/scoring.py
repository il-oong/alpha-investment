"""종합 점수 산출 유틸리티
트레이더 5인 가중치 기반 0~100점
"""


def calc_technical_score(technicals: dict) -> float:
    """기술적 분석 점수 (0~100)"""
    score = 50.0  # 기본 중립

    # RSI
    rsi = technicals.get("rsi")
    if rsi is not None:
        if 40 <= rsi <= 60:
            score += 5  # 중립 구간
        elif rsi < 30:
            score += 15  # 과매도 → 매수 기회
        elif rsi > 70:
            score -= 15  # 과매수 → 주의

    # MACD
    macd = technicals.get("macd")
    if macd:
        if macd["histogram"] > 0:
            score += 10
        else:
            score -= 10

    # Weinstein Stage
    stage = technicals.get("weinstein_stage", {})
    stage_num = stage.get("stage")
    if stage_num == 2:
        score += 15
    elif stage_num == 4:
        score -= 20
    elif stage_num == 1:
        score += 5
    elif stage_num == 3:
        score -= 10

    # VCP
    vcp = technicals.get("vcp", {})
    if vcp.get("detected"):
        score += 10

    # 볼린저
    bb = technicals.get("bollinger")
    if bb:
        pct_b = bb.get("pct_b", 0.5)
        if pct_b < 0.2:
            score += 5  # 하단 근접 → 반등 기대
        elif pct_b > 0.8:
            score -= 5  # 상단 근접 → 주의

    return max(0, min(100, round(score, 2)))


def calc_fundamental_score(fundamentals: dict) -> float:
    """펀더멘털 점수 (0~100) - CAN SLIM + PEG"""
    score = 50.0

    per = fundamentals.get("per", 0)
    pbr = fundamentals.get("pbr", 0)
    peg = fundamentals.get("peg", 0)
    roe = fundamentals.get("roe", 0)

    # PER
    if 0 < per < 15:
        score += 10
    elif per > 30:
        score -= 10

    # PBR
    if 0 < pbr < 1.5:
        score += 5
    elif pbr > 5:
        score -= 5

    # PEG (Peter Lynch)
    if 0 < peg < 1.0:
        score += 15  # 저평가 성장주
    elif 0 < peg < 1.5:
        score += 5
    elif peg > 2.0:
        score -= 10

    # ROE
    if isinstance(roe, (int, float)):
        if roe > 0.15:
            score += 10
        elif roe < 0.05:
            score -= 5

    return max(0, min(100, round(score, 2)))


def calc_flow_score(flow_data: dict) -> float:
    """수급 점수 (0~100)"""
    score = 50.0

    consecutive = flow_data.get("foreign_consecutive_days", 0)
    if consecutive >= 5:
        score += 20
    elif consecutive >= 3:
        score += 10
    elif consecutive <= -3:
        score -= 10
    elif consecutive <= -5:
        score -= 20

    return max(0, min(100, round(score, 2)))


def calc_composite_score(
    technical_score: float,
    fundamental_score: float,
    flow_score: float,
    macro_score: float,
    news_score: float,
    weights: dict | None = None,
) -> float:
    """JKP 종합 점수 (0~100)
    트레이더 5인 가중치 반영

    기본 가중치:
    - 기술적 (Livermore + Weinstein + Minervini): 40%
    - 펀더멘털 (O'Neil + Lynch): 20%
    - 수급: 15%
    - 매크로: 15%
    - 뉴스: 10%
    """
    if weights is None:
        weights = {
            "technical": 0.40,
            "fundamental": 0.20,
            "flow": 0.15,
            "macro": 0.15,
            "news": 0.10,
        }

    composite = (
        technical_score * weights.get("technical", 0.4)
        + fundamental_score * weights.get("fundamental", 0.2)
        + flow_score * weights.get("flow", 0.15)
        + macro_score * weights.get("macro", 0.15)
        + news_score * weights.get("news", 0.1)
    )

    return max(0, min(100, round(composite, 2)))

"""기술적 지표 계산 유틸리티
RSI, MACD, 볼린저밴드, VCP, Weinstein Stage, 이동평균
"""
import math


def calc_rsi(closes: list[float], period: int = 14) -> float | None:
    """RSI (Relative Strength Index) 계산"""
    if len(closes) < period + 1:
        return None

    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calc_macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict | None:
    """MACD 계산

    Returns:
        {macd, signal, histogram}
    """
    if len(closes) < slow + signal:
        return None

    def ema(data: list[float], period: int) -> list[float]:
        k = 2 / (period + 1)
        result = [data[0]]
        for i in range(1, len(data)):
            result.append(data[i] * k + result[-1] * (1 - k))
        return result

    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)

    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema(macd_line[slow - 1:], signal)

    macd_val = macd_line[-1]
    signal_val = signal_line[-1] if signal_line else 0
    histogram = macd_val - signal_val

    return {
        "macd": round(macd_val, 4),
        "signal": round(signal_val, 4),
        "histogram": round(histogram, 4),
    }


def calc_bollinger_bands(
    closes: list[float],
    period: int = 20,
    std_dev: float = 2.0,
) -> dict | None:
    """볼린저 밴드 계산

    Returns:
        {upper, middle, lower, bandwidth, pct_b}
    """
    if len(closes) < period:
        return None

    recent = closes[-period:]
    middle = sum(recent) / period
    variance = sum((x - middle) ** 2 for x in recent) / period
    std = math.sqrt(variance)

    upper = middle + std_dev * std
    lower = middle - std_dev * std
    bandwidth = (upper - lower) / middle * 100 if middle != 0 else 0
    pct_b = (closes[-1] - lower) / (upper - lower) if (upper - lower) != 0 else 0.5

    return {
        "upper": round(upper, 2),
        "middle": round(middle, 2),
        "lower": round(lower, 2),
        "bandwidth": round(bandwidth, 2),
        "pct_b": round(pct_b, 4),
    }


def calc_moving_averages(closes: list[float]) -> dict:
    """주요 이동평균선 계산"""
    mas = {}
    for period in [5, 10, 20, 50, 60, 120, 200]:
        if len(closes) >= period:
            ma = sum(closes[-period:]) / period
            mas[f"ma{period}"] = round(ma, 2)
        else:
            mas[f"ma{period}"] = None
    return mas


def detect_weinstein_stage(closes: list[float]) -> dict:
    """Weinstein Stage 분석 (30주 MA 기준)

    Stage 1: 기저 (바닥 다지기) - MA 횡보, 가격 MA 근처
    Stage 2: 상승 (매수) - 가격 > MA, MA 상승
    Stage 3: 천장 (배분) - 가격 MA 근처에서 횡보, MA 둔화
    Stage 4: 하락 (금지) - 가격 < MA, MA 하락
    """
    if len(closes) < 150:  # 30주 ≈ 150 거래일
        return {"stage": None, "description": "데이터 부족"}

    ma30w = sum(closes[-150:]) / 150
    ma30w_prev = sum(closes[-160:-10]) / 150 if len(closes) >= 160 else ma30w
    ma_slope = (ma30w - ma30w_prev) / ma30w_prev * 100 if ma30w_prev != 0 else 0

    price = closes[-1]
    price_vs_ma = (price - ma30w) / ma30w * 100 if ma30w != 0 else 0

    if price_vs_ma > 5 and ma_slope > 0.5:
        stage = 2
        desc = "Stage 2 상승 (매수 적합)"
    elif price_vs_ma < -5 and ma_slope < -0.5:
        stage = 4
        desc = "Stage 4 하락 (매수 금지)"
    elif abs(price_vs_ma) <= 5 and abs(ma_slope) <= 0.5 and price < ma30w:
        stage = 1
        desc = "Stage 1 기저 (관망)"
    else:
        stage = 3
        desc = "Stage 3 천장 (주의)"

    return {
        "stage": stage,
        "description": desc,
        "ma30w": round(ma30w, 2),
        "price_vs_ma_pct": round(price_vs_ma, 2),
        "ma_slope_pct": round(ma_slope, 4),
    }


def detect_vcp(closes: list[float], volumes: list[float]) -> dict:
    """VCP (Volatility Contraction Pattern) 탐지 - Minervini

    연속적으로 변동폭이 줄어드는 패턴
    """
    if len(closes) < 60 or len(volumes) < 60:
        return {"detected": False, "reason": "데이터 부족"}

    # 최근 3개 구간의 변동폭 비교 (각 20일)
    ranges = []
    for i in range(3):
        start = -(60 - i * 20)
        end = -(40 - i * 20) if i < 2 else None
        segment = closes[start:end] if end else closes[start:]
        if segment:
            high = max(segment)
            low = min(segment)
            pct_range = (high - low) / low * 100 if low != 0 else 0
            ranges.append(pct_range)

    if len(ranges) < 3:
        return {"detected": False, "reason": "구간 부족"}

    # 변동폭이 연속 감소하면 VCP
    contracting = ranges[0] > ranges[1] > ranges[2]

    # 거래량도 감소 추세인지
    vol_avg_1 = sum(volumes[-60:-40]) / 20
    vol_avg_3 = sum(volumes[-20:]) / 20
    vol_contracting = vol_avg_3 < vol_avg_1

    detected = contracting and vol_contracting

    return {
        "detected": detected,
        "ranges": [round(r, 2) for r in ranges],
        "volume_contracting": vol_contracting,
        "description": "VCP 패턴 감지!" if detected else "VCP 미감지",
    }


def calc_all_technicals(closes: list[float], volumes: list[float] | None = None) -> dict:
    """모든 기술적 지표 일괄 계산"""
    result = {
        "rsi": calc_rsi(closes),
        "macd": calc_macd(closes),
        "bollinger": calc_bollinger_bands(closes),
        "moving_averages": calc_moving_averages(closes),
        "weinstein_stage": detect_weinstein_stage(closes),
    }
    if volumes:
        result["vcp"] = detect_vcp(closes, volumes)
    return result

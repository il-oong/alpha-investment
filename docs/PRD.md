# ALPHA Investment Platform — 제품 요구사항 명세서 (PRD)

| 항목 | 내용 |
|---|---|
| 문서 버전 | v1.0 |
| 작성일 | 2026-05-18 |
| 제품 코드명 | ALPHA |
| 페르소나 | JKP (James K. Park) — 전 Bridgewater 시니어 펀드매니저 |
| 대상 시장 | 한국(KOSPI/KOSDAQ), 미국(NYSE/NASDAQ) |
| 기술 스택 | FastAPI · Supabase(PostgreSQL) · Gemini 2.5 Flash · KIS Open API · APScheduler · Telegram Bot |

---

## 1. 개요

### 1.1 제품 한 줄 정의
**JKP 페르소나 기반 7개 AI 에이전트가 한·미 주식을 통합 분석하고, 매수·보유·매도 의견과 자동매매 신호를 제공하는 개인 투자 플랫폼.**

### 1.2 배경 및 문제 정의
- 개인 투자자는 매크로/뉴스/기술적/펀더멘털/수급/세력/미장 등 **다수 신호를 동시에 추적할 수 없다**.
- 기존 HTS·증권사 리포트는 **데이터만 제공**하고, "지금 사야 하나"에 대한 **통합 판단**이 없다.
- AI 분석 서비스는 **단일 모델 기반**이라 시장 국면 변화에 취약하다.
- 자동매매 도구는 안전장치가 부족해 **장 초반/마감 급변기에 손실**을 키운다.

### 1.3 솔루션 핵심
1. **7개 전문 에이전트 → JKP 통합 판단**: 매크로·뉴스·기술·펀더멘털·수급·세력·미장 신호를 종합점수(0~100)와 최종 액션으로 환원.
2. **5인 전설 트레이더 철학 가중치**: Livermore·O'Neil·Weinstein·Minervini·Lynch 5가지 스타일을 사용자가 슬라이더로 조정.
3. **스마트 타임 게이트 + 5단계 안전등급**: 위험 시간대(09:00~09:30, 15:00~15:30)에는 자동매매 자동 차단.
4. **하루 5회 정기 브리핑**: 텔레그램으로 미장 마감(06:00)·오전 전략(07:00)·점심 뉴스(12:00)·장마감 수급(15:30)·미장 시작(23:30) 발송.

### 1.4 목표 사용자
| 페르소나 | 설명 | 핵심 니즈 |
|---|---|---|
| 직장인 투자자 | 장중 모니터링 불가, 정기 알림 필요 | 텔레그램 브리핑, 손절 자동화 |
| 중급 트레이더 | 다중 신호를 직접 종합하기 부담 | 7개 에이전트 통합 점수, 매수·손절 지점 |
| 데이터 드리븐 투자자 | 가중치를 본인 스타일에 맞게 튜닝 | 트레이더 5인 가중치 슬라이더, 백테스트 |

---

## 2. 목표 및 성공 지표

### 2.1 비즈니스 목표 (6개월)
- MAU 1,000명, 유료 전환율 8%
- 텔레그램 브리핑 오픈율 60%+
- 분석 요청 → 매수 의사결정 전환율 25%+

### 2.2 제품 성공 지표 (KPI)
| 영역 | 지표 | 목표 |
|---|---|---|
| 분석 정확도 | JKP "매수" 추천 종목의 30일 평균 수익률 | 코스피 대비 +3%p |
| 안전성 | 자동매매 손절 실행 시 평균 손실폭 | -7% 이내 |
| 응답성 | 종목 즉시분석 API p95 응답시간 | < 6초 |
| 신뢰성 | 정기 브리핑 발송 성공률 | 99.5% |
| 사용성 | 알림 → 앱 진입 CTR | 40%+ |

### 2.3 Non-Goals (이번 단계에서 다루지 않음)
- 파생상품(선물/옵션) 분석
- 암호화폐 분석
- 다중 사용자/팀 협업 기능
- 백테스트 시뮬레이션 UI (Phase 4 이후)
- 모바일 네이티브 앱 (웹 우선)

---

## 3. 사용자 시나리오

### 3.1 시나리오 A — "출근길 5분 전략 브리핑"
> 07:00 직장인 사용자가 텔레그램에서 ALPHA 봇 메시지를 받는다.
> "오늘 KOSPI는 매크로 점수 62, 외인 수급 약세. 반도체 섹터 단기 약세 가능, 방어주 비중 확대 검토." 5줄 요약을 읽고 출근.

### 3.2 시나리오 B — "관심종목 즉시 분석"
> 사용자가 '삼성전자(005930)'를 입력 → 6초 후 화면에 종합점수 78점, 매수구간 71,000~72,500원, 목표가 78,000원(1차)/82,000원(2차), 손절가 68,500원, JKP 코멘트 "수급은 양호하나 매크로 약세 — 분할매수 권고" 표시.

### 3.3 시나리오 C — "자동 손절 알림"
> 보유종목이 손절가(-7%)에 도달 → Lv5 알림 발송: "삼성전자 손절선 도달, Red Zone 진입. 자동매매 비활성 상태 — 사용자 판단 필요." 카드형 알림에 [전량매도][분할매도][보유] 3-버튼 제공.

### 3.4 시나리오 D — "서킷브레이커 발동"
> 코스피 8% 하락 → 자동매매 STEP 1 신규매수 전면 중단 → STEP 2 Gemini가 원인 분석(일시적 vs 구조적) → STEP 3 대응 전략 제시 → STEP 4 사용자 최종 판단 요청. **자동 시장가 전량매도는 어떤 경우에도 실행하지 않는다.**

---

## 4. 기능 요구사항

### 4.1 7개 AI 에이전트 + JKP 통합

| ID | 에이전트 | 입력 | 출력 | 실행 주기 |
|---|---|---|---|---|
| AG-1 | **Macro Sentinel** | FRED 거시지표, VIX, 환율 | 매크로 점수, 시장 국면 판정 | 06:00 일 1회 |
| AG-2 | **News Scanner** | 매경·한경·WSJ·Bloomberg RSS | 종목 태깅, 감성점수(-100~100) | 30분 |
| AG-3 | **Quant Engine** | OHLCV (KIS / yfinance) | RSI/MACD/Stage/VCP, 기술점수 | 종목 요청 시 |
| AG-4 | **Fundamental AI** | 재무제표 (Alpha Vantage/KIS) | PER/PBR/PEG/CAN SLIM, 펀더점수 | 종목 요청 시 |
| AG-5 | **Flow Tracker** | 외인·기관 순매수 | 수급점수, 연속매수 일자 | 15:30 일 1회 |
| AG-6 | **Dark Pool Detector** | 거래량 이상치 | 세력 진입 여부, 신뢰도 | 종목 요청 시 |
| AG-7 | **US Sentinel** | S&P/Nasdaq/VIX | 미장 점수, 환율 영향 | 06:00 / 23:30 |
| AG-0 | **JKP Persona** | 7개 결과 종합 | 최종 액션, 매수구간, 목표가, 손절가, 종합점수 | on_demand |

#### 4.1.1 JKP 최종 출력 스키마
```json
{
  "final_action": "강력매수|매수|보유|관망|매도 준비|매도|강력매도",
  "confidence": 0-100,
  "buy_zone": { "entry_price": 71000, "additional_buy": 69500 },
  "target_price": { "target_1": 78000, "target_2": 82000 },
  "stop_loss": 68500,
  "risk_reward_ratio": 2.4,
  "position_size": "포트폴리오 비중 8%",
  "time_horizon": "단기|중기|장기",
  "key_catalysts": ["촉매1", "촉매2"],
  "key_risks": ["리스크1", "리스크2"],
  "monitoring_points": ["포인트1", "포인트2"],
  "jkp_comment": "JKP 한마디 (투자 원칙 기반 2~3문장)"
}
```

#### 4.1.2 종합 점수 공식
- `composite = w_tech·tech + w_fund·fund + w_flow·flow + w_macro·macro + w_news·news`
- 기본 가중치: 기술 25 / 펀더 20 / 수급 25 / 매크로 15 / 뉴스 15
- 사용자가 `user_settings`에서 트레이더 5인 가중치(합계 100)로 조정 가능

### 4.2 정기 브리핑 (텔레그램)

| 시간 | 브리핑 | 콘텐츠 | 채널 |
|---|---|---|---|
| 06:00 | 미장 마감 | US Sentinel 결과 5줄 요약 | Telegram |
| 07:00 | JKP 오전 전략 | 매크로 + 뉴스 종합 5줄 + 오늘의 워치리스트 | Telegram |
| 12:00 | 점심 뉴스 | News Scanner 핵심 뉴스 3건 | Telegram |
| 15:30 | 장마감 수급 | Flow Tracker 외인/기관 동향 | Telegram |
| 23:30 | 미장 시작 | US Sentinel 개장 시그널 | Telegram |

- 발송 실패 시 재시도 3회 (5분 / 15분 / 30분)
- 사용자별 ON/OFF 토글 (Phase 2)

### 4.3 알림 시스템 (5단계 Level)

| Lv | 명칭 | 채널 | 트리거 예시 |
|---|---|---|---|
| 1 | 정보 | 앱 내부 | 일별 점수 변동 |
| 2 | 권고 | Telegram | 매수 구간 진입 |
| 3 | 경고 | Telegram + 푸시 | 목표가 도달 / 외인 4일 연속 매도 |
| 4 | 긴급 | Telegram + 푸시 | 보유종목 -5% 도달 |
| 5 | 즉시손절 | Telegram + 푸시 (반복) | 손절가 도달 / 서킷브레이커 |

### 4.4 자동매매 시스템

#### 4.4.1 스마트 타임 게이트
| 시간대 | 위험도 | 자동매매 |
|---|---|---|
| 09:00~09:30 | danger | 차단 |
| 09:30~10:00 | caution | 매수만, 카톡 승인 |
| 10:00~14:30 | safe | 정상 운용 |
| 14:30~15:00 | caution | 매수만, 카톡 승인 |
| 15:00~15:30 | danger | 차단 |

#### 4.4.2 5단계 안전 등급
1. **Green Zone**: 전 조건 통과 → 완전 자동매매
2. **Yellow Zone**: 일부 경고 → 매수만 허용, 카톡 승인
3. **Orange Zone**: 신규 매수 금지, 손절만 자동
4. **Red Zone**: 자동매매 중단, 알림만
5. **Emergency**: 서킷브레이커 → 분석 후 **사용자 최종 판단** (자동 시장가 매도 금지)

#### 4.4.3 안전 한도 (기본값)
- 일일 거래 한도: 5,000,000원
- 단일 주문 한도: 1,000,000원
- 종목별 최대 비중: 30%
- 사용자가 `registered_accounts`에서 계좌별 오버라이드 가능

### 4.5 포트폴리오 관리
- 보유종목: 매수가/목표가1·2/손절가/현재 종합점수
- 관심종목: 추가/삭제/메모
- 종목별 개별 설정 오버라이드 (RSI 임계값, 손절률 등)

### 4.6 종목 즉시 분석
- 엔드포인트: `GET /api/v1/analysis/{ticker}?market=KR|US`
- 응답: JKP 통합 분석 (4.1.1 스키마)
- 보조 엔드포인트:
  - `/analysis/{ticker}/technical` — 빠른 기술적 분석만
  - `/analysis/{ticker}/fundamental` — 펀더멘털만

### 4.7 계좌 등록 & 검증
- 화이트리스트 방식 (등록된 계좌만 자동매매 가능)
- App Key / Secret은 Supabase에 암호화 저장
- 모의/실전 분리 (`is_real` 플래그)
- 첫 사용 시 1주만 매수 → 매도 테스트 (검증 통과 후 활성화)

---

## 5. 데이터 모델 (15개 테이블 — `migrations/001_initial_schema.sql` 기준)

| # | 테이블 | 핵심 컬럼 | 비고 |
|---|---|---|---|
| 1 | watchlist | user_id, ticker, market | RLS |
| 2 | daily_analysis | ticker, date, rsi, macd, stage, vcp_detected, score | UNIQUE(ticker, date) |
| 3 | market_snapshot | date, kospi, vix, usd_krw, fear_greed_index | 일 1회 |
| 4 | news_feed | title, source, sentiment_score, tickers[] | |
| 5 | alerts | user_id, ticker, level (1~5), channel | RLS |
| 6 | portfolio | user_id, ticker, qty, avg_buy_price, targets, stop_loss | RLS |
| 7 | agent_reports | agent_name, ticker, report (JSONB), score | 인덱스 (agent_name, created_at) |
| 8 | economic_calendar | event_name, event_date, importance | FOMC/CPI |
| 9 | sell_signals | user_id, ticker, signal_level, reason | RLS |
| 10 | user_settings | investment_style, 트레이더 5인 가중치 | RLS, UNIQUE(user_id) |
| 11 | ticker_settings | 종목별 임계값 오버라이드 | RLS |
| 12 | registered_accounts | broker, 암호화 키, 한도, verified | RLS, 화이트리스트 |
| 13 | account_order_log | account_id, order_type, status | 모든 주문 기록 |
| 14 | auto_trade_log | safety_level, time_zone, success, agent_scores | 실패 사유 포함 |
| 15 | time_slot_stats | time_slot, win_rate, avg_return | 시간대별 통계 |

---

## 6. API 사양 (Phase 1 구현 완료)

### 6.1 Analysis
- `GET /api/v1/analysis/{ticker}` — JKP 종합 분석
- `GET /api/v1/analysis/{ticker}/technical`
- `GET /api/v1/analysis/{ticker}/fundamental`

### 6.2 Briefing
- `GET /api/v1/briefing/morning` — 07:00 오전 전략
- `GET /api/v1/briefing/us-close` — 06:00 미장 마감
- `GET /api/v1/briefing/noon` — 12:00 점심 뉴스
- `GET /api/v1/briefing/market-close` — 15:30 장마감
- `GET /api/v1/briefing/us-open` — 23:30 미장 시작

### 6.3 Agents
- `GET /api/v1/agents/` — 에이전트 목록 & 상태
- `GET /api/v1/agents/{name}/report` — 최신 리포트
- `POST /api/v1/agents/{name}/run?ticker=XXXX` — 수동 실행

### 6.4 Portfolio
- `GET /api/v1/portfolio/holdings`
- `GET /api/v1/portfolio/watchlist`
- `POST /api/v1/portfolio/watchlist/{ticker}`
- `DELETE /api/v1/portfolio/watchlist/{ticker}`

### 6.5 Alerts
- `GET /api/v1/alerts/` — 알림 목록
- `POST /api/v1/alerts/read/{id}` — 읽음 처리

### 6.6 Trading
- `GET /api/v1/trading/status` — 자동매매 상태
- `GET /api/v1/trading/time-gate` — 현재 시간대 위험도
- `GET /api/v1/trading/safety-level` — 5단계 안전등급
- `GET /api/v1/trading/circuit-breaker` — 서킷브레이커 상태
- `GET /api/v1/trading/stats` — 시간대별 승률

---

## 7. 비기능 요구사항

### 7.1 성능
- 종목 즉시분석 p95 < 6초 (7개 에이전트 병렬 호출 + Gemini 1회)
- 정기 브리핑 발송 5분 이내 완료
- DB 조회 p95 < 200ms

### 7.2 보안
- App Key/Secret은 **Supabase Vault** 또는 AES-256 암호화 저장
- 모든 RLS(Row Level Security) 적용 — 사용자별 데이터 격리
- 자동매매는 화이트리스트 계좌만 허용
- 자동 시장가 전량매도는 **시스템적으로 금지** (코드 레벨)

### 7.3 신뢰성
- 텔레그램 발송 실패 시 3회 재시도 (지수 백오프)
- 외부 API(KIS·Gemini·FRED) 다운 시 graceful degradation (해당 에이전트 점수 = 50 fallback)
- Supabase 다운 시 캐시 기반 마지막 리포트 제공

### 7.4 관측성
- 모든 에이전트 실행은 `agent_reports`에 JSONB로 기록
- 자동매매 시도/성공/실패는 `auto_trade_log`
- 일별 KPI 대시보드: 분석 정확도 / 알림 발송률 / API 응답시간

### 7.5 한도 & 안전장치
- 일일 거래 한도, 단일 주문 한도, 종목 비중 모두 **DB 기반 강제 검증**
- 한도 초과 주문은 `account_order_log.status = 'rejected'`로 기록 (실행 금지)

---

## 8. 로드맵

### Phase 1 (현재 — 완료)
- [x] 7개 에이전트 + JKP 페르소나
- [x] 정기 브리핑 5회 (텔레그램)
- [x] 종목 즉시분석 API
- [x] 포트폴리오/관심종목 CRUD
- [x] 15개 테이블 마이그레이션
- [x] 스마트 타임 게이트 / 5단계 안전등급 정의 (모니터링만)

### Phase 2 (1~2개월)
- [ ] 프론트엔드 (Next.js) — 분석 카드, 가중치 슬라이더, 알림 리스트
- [ ] 사용자 인증 (Supabase Auth)
- [ ] 알림 ON/OFF 토글, 시간 커스터마이징
- [ ] 종목별 ticker_settings UI

### Phase 3 (3~4개월)
- [ ] 자동매매 활성화 (Green/Yellow Zone)
- [ ] KIS 실전 계좌 검증 플로우 (1주 매수→매도 테스트)
- [ ] 서킷브레이커 4단계 워크플로
- [ ] 카톡 승인 플로우 (Yellow Zone 매수)

### Phase 4 (5~6개월)
- [ ] 백테스트 시뮬레이터
- [ ] 트레이더 5인 가중치 자동 튜닝 (강화학습)
- [ ] 시간대별 승률 기반 진입 시점 추천
- [ ] 멀티 브로커 (키움 / 대신) 지원

---

## 9. 위험 요소 & 대응

| 위험 | 영향 | 대응 |
|---|---|---|
| Gemini API 비용 폭증 | 분석 1회당 7개 에이전트 호출 | 결과 캐싱(15분), 에이전트별 점수 fallback |
| KIS API 장애 | 자동매매 중단 | Red Zone 자동 전환, 사용자 알림 |
| 잘못된 자동 손절 | 사용자 손실 | 5단계 안전등급, **시장가 전량매도 금지** |
| 뉴스 RSS 차단 | News Scanner 0점 처리 | 다중 소스(매경·한경·WSJ·Bloomberg) |
| LLM 환각 (목표가/손절가) | 잘못된 의사결정 | JSON 스키마 강제 + 기술적 분석 결과 범위 검증 |
| 텔레그램 봇 차단 | 알림 미발송 | 앱 내부 알림 백업, 이메일 발송 옵션(Phase 2) |

---

## 10. 핵심 의존성

- **Supabase**: PostgreSQL + Auth + RLS
- **Gemini 2.5 Flash**: LLM 분석 (저비용 우선)
- **KIS Open API**: 한국 주식 시세/주문 (`https://openapi.koreainvestment.com:9443`)
- **Alpha Vantage**: 미국 재무 데이터
- **FRED API**: 거시경제 지표
- **yfinance**: 미국 주식 OHLCV
- **APScheduler**: 정기 브리핑 크론
- **Telegram Bot API**: 알림 채널

---

## 11. 핵심 설계 원칙 (JKP 5원칙)

1. **매크로 우선** — 거시경제가 먼저다. 매크로가 나쁘면 개별종목이 아무리 좋아도 보수적으로.
2. **수급 중시** — 외인/기관 흐름이 개인 판단보다 우선.
3. **규율** — 손절선은 반드시 지킨다. 예외 없음.
4. **단순함** — 복잡한 전략을 지양, 명확한 근거만 제시.
5. **리스크 퍼스트** — "얼마 벌 수 있나"보다 "얼마 잃을 수 있나"를 먼저.

---

## 12. 부록

### 12.1 트레이더 5인 철학
| 트레이더 | 핵심 개념 | 코드 반영 |
|---|---|---|
| Jesse Livermore | 피벗 포인트, 추세 추종 | Quant Engine — 추세 점수 |
| William O'Neil | CAN SLIM | Fundamental AI — EPS/매출 성장 |
| Stan Weinstein | Stage 1~4 분석 | Quant Engine — `stage` 컬럼 |
| Mark Minervini | VCP, SEPA | Quant Engine — `vcp_detected` |
| Peter Lynch | PEG, 미발굴 성장주 | Fundamental AI — PEG 점수 |

### 12.2 용어집
- **JKP**: James K. Park, 본 플랫폼의 페르소나 펀드매니저
- **VCP**: Volatility Contraction Pattern (변동성 수축)
- **CAN SLIM**: O'Neil의 7가지 성장주 선정 기준
- **Stage 분석**: Weinstein의 4단계 가격 사이클 분류
- **Dark Pool**: 비공개 거래소 (세력 거래 흔적)
- **Safety Level**: 자동매매 5단계 안전등급
- **Time Gate**: 시간대별 자동매매 차단 시스템

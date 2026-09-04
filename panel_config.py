"""Part 2 longitudinal 패널 수집 설정 — 날짜·endpoint 를 코드에서 분리.

`collect_panel.py` 가 이 파일을 읽는다. 실제 수집 승인 전에 여기 숫자를 사람이 검토한다.
근거: `endpoint_feasibility_probe.md` (소급 범위 실측), namu.wiki 하이퍼 버닝 / 버닝 비욘드 (이벤트 일정).
"""

# ── 공식 이벤트 일정 (2026-09-03 확인) ──────────────────────────────────
#   하이퍼 버닝 MAX = 1+4 레벨업, ~260 구간 / 버닝 BEYOND = 1+1 레벨업, 260~상한
EVENTS = {
    "ASSEMBLE":  dict(season="2025 여름", hb_start="2025-06-19", hb_end="2025-09-17",
                      beyond_end="2025-10-22", beyond_cap=270),
    "CROWN":     dict(season="2025 겨울", hb_start="2025-12-18", hb_end="2026-06-17",
                      beyond_end="2026-06-17", beyond_cap=270),   # 6개월 연속 — 비수기 없음
    "OVERDRIVE": dict(season="2026 여름", hb_start="2026-06-18", hb_end="2026-09-16",
                      beyond_end="2026-09-16", beyond_cap=280),   # 상한 270→280 확장
}

# ── basic 스냅샷 격자 ────────────────────────────────────────────────
#   tier="mvp"  : 상태 분류(Parker/Persistent/Reactivated/Dormant)에 필요한 최소 관측점
#   tier="full" : leading indicator·이벤트종료 리텐션 정밀화용 추가 관측점
#   role        : 사람이 읽는 의미 라벨. panel_basic.csv 에 그대로 기록됨.
#   기존 data/cohort_*.csv 의 2026-06-18~07-22 daily 는 재수집하지 않고 분석에서 병합.
SNAPSHOTS = [
    dict(role="assemble_pre",        date="2025-06-12", tier="mvp"),   # 2025 여름 직전 기준선
    dict(role="assemble_early",      date="2025-07-10", tier="full"),
    dict(role="assemble_hb_late",    date="2025-09-10", tier="full"),  # 하이퍼버닝 종료 직전
    dict(role="assemble_hb_end+7",   date="2025-09-24", tier="mvp"),   # HB 종료(09-17)+7
    dict(role="assemble_hb_end+28",  date="2025-10-15", tier="full"),
    dict(role="assemble_beyond_p14", date="2025-11-05", tier="full"),  # BEYOND 종료(10-22)+14
    dict(role="crown_pre",           date="2025-12-12", tier="mvp"),   # ASSEMBLE 안정 상태 = CROWN 직전
    dict(role="crown_mid",           date="2026-03-15", tier="mvp"),
    dict(role="overdrive_pre",       date="2026-06-12", tier="mvp"),   # ★ predictor 스냅샷 (2026 이벤트 前)
    dict(role="overdrive_late",      date="2026-08-20", tier="full"),
    dict(role="latest",              date="2026-09-02", tier="mvp"),   # T-1 최신
]

# ── 이벤트 종료 후 추적 (2026 OVERDRIVE, 종료 09-16 이후) ─────────────
#   "방학 이벤트 성장이 종료 후에도 남는가"의 직접 측정. 종료 후 별도 실행.
POST_EVENT_FOLLOWUP = [
    dict(role="overdrive_end+7",  date="2026-09-23", tier="followup"),
    dict(role="overdrive_end+14", date="2026-09-30", tier="followup"),
    dict(role="overdrive_end+28", date="2026-10-14", tier="followup"),
]

# ── endpoint ────────────────────────────────────────────────────────
#   tier="basic"  : 레벨 궤적 → 상태 분류
#   tier="invest" : 전투력/HEXA/심볼/장비/유니온 → leading indicator (Stage 2 에서만)
ENDPOINTS = {
    "basic":           dict(path="/character/basic",            tier="basic",  earliest="2023-12-22"),
    "stat":            dict(path="/character/stat",             tier="invest", earliest="2023-12-22"),
    "hexamatrix":      dict(path="/character/hexamatrix",       tier="invest", earliest="2023-12-22"),
    "hexamatrix-stat": dict(path="/character/hexamatrix-stat",  tier="invest", earliest="2025-06-19"),
    "symbol":          dict(path="/character/symbol-equipment", tier="invest", earliest="2023-12-22"),
    "item-equipment":  dict(path="/character/item-equipment",   tier="invest", earliest="2023-12-22"),
    "union":           dict(path="/user/union",                 tier="invest", earliest="2023-12-22"),
}

# invest endpoint 를 받을 시점 — outcome(2026-07+ 성장) 보다 앞선 pre-event 시점만.
#   시간순서 엄수: 이 날짜들 이후에 형성된 HEXA/장비는 predictor 로 쓰지 않는다.
INVEST_MILESTONES = ["2025-06-12", "2025-12-12", "2026-06-12"]

# ── Stage 2 Pilot (~260명) — investment state 검증 ─────────────────
#   목적: 관측된 progression 중 major burning 지원에 의한 성장과, 지원 종료 이후에도
#         관측되는 progression 을 구분할 feature/state 설계가 가능한가.
#   4축 해석 frame (locked):
#     Level  = grind/time-oriented progression      (EXP 쿠폰으로 오염 → post-event Δ 위주)
#     HEXA   = character resource investment        (Sol Erda/Fragment. 거래 구매 가능 → 접속 아님)
#     Symbol = long-horizon progression participation(일일/장기형 시스템 지속 참여 proxy. 로그인빈도와 동일시 안 함)
#     CP     = resulting specification growth
#     Union  = account-level context
#   해석 주의: post-event Δ 는 "major burning 지원 종료 이후에도 관측되는 progression" 이지
#             pure voluntary behavior 가 아니다 (평시 이벤트샵·Sunday Maple·보유 재화 존재).
#   Persistent 판정: HEXA Δ>0 OR Symbol Δ>0 를 즉시 Persistent 로 hard-code 하지 않는다.
#             trajectory(min meaningful change / 변화 관측 interval 수 / post_slope / breadth)
#             분포를 pilot 후 확인해 threshold 결정. (raw core 배열은 그대로 보존.)
PILOT_ENDPOINTS = ["basic", "stat", "hexamatrix", "symbol", "union"]  # item-equipment, hexamatrix-stat 제외
#   본 수집은 2 wave 로 분리 (B_post56 이 2026-11-11 이라 한 번에 못 받음):
#     Wave 1 (2026-10-15 이후): A_* 3개 + B_event_end/post7/post14/post28  → 약 9,120 콜
#     Wave 2 (2026-11-12 이후): B_post56 만                                → 약 1,425 콜
#   `--tier pilot` 그대로 재실행하면 그 시점에 조회 가능한 날짜만 자동 수집(나머지는 T-1 초과로 skip).
PILOT_MILESTONES = [
    # Phase A — retrospective context (누적 수준 + 시즌 반복 성장 여부. event/voluntary 분리 불가)
    dict(role="A_assemble_pre",   date="2025-06-12", tier="pilot"),
    dict(role="A_crown_pre",      date="2025-12-12", tier="pilot"),
    dict(role="A_overdrive_pre",  date="2026-06-12", tier="pilot"),  # OVERDRIVE 직전 baseline
    # Phase B — 분리 측정 (OVERDRIVE 종료 2026-09-16 이후 = 관측창 내 유일한 무-버닝 구간)
    dict(role="B_event_end",      date="2026-09-15", tier="pilot"),  # 종료 직전(T-1)  ┐ Wave 1
    dict(role="B_post7",          date="2026-09-23", tier="pilot"),  #                 │
    dict(role="B_post14",         date="2026-09-30", tier="pilot"),  #                 │
    dict(role="B_post28",         date="2026-10-14", tier="pilot"),  #                 ┘
    dict(role="B_post56",         date="2026-11-11", tier="pilot"),  # 연장 — 저강도 성장 관측력  ← Wave 2
]

# ── API 물리적 한계 (probe 실측) ───────────────────────────────────
API_MIN_DATE = "2023-12-22"
API_MAX_LAG_DAYS = 1          # 오늘-1 까지만 조회 가능

# ── 표본 pool ──────────────────────────────────────────────────────
COHORT_FILES = ["approach", "at260", "past260", "burnend", "climb"]
DATA_DIR = "data"

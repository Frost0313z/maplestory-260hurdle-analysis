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

# ── API 물리적 한계 (probe 실측) ───────────────────────────────────
API_MIN_DATE = "2023-12-22"
API_MAX_LAG_DAYS = 1          # 오늘-1 까지만 조회 가능

# ── 표본 pool ──────────────────────────────────────────────────────
COHORT_FILES = ["approach", "at260", "past260", "burnend", "climb"]
DATA_DIR = "data"

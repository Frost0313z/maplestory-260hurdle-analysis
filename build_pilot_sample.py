"""Stage 2 Pilot 표본 추출 — data/panel_basic.csv 의 레벨 궤적에서 PROVISIONAL label 을 붙여
행동이 명확한 캐릭터만 stratified sampling → data/pilot_targets.csv.

⚠️ 여기서 붙이는 label(Dormant/Parker/Persistent/Reactivated)은 임시다.
   pilot 수집(stat/hexamatrix/symbol/union) 후 4축 frame(Level/HEXA/Symbol/CP)과
   post-event trajectory 분포를 보고 재정의한다. 이 스크립트는 "수집 대상 선정"만 한다.

레벨 궤적 6시점: 2025-06-12 / 09-24 / 12-12, 2026-03-15 / 06-12 / 09-02  (= Stage 1 mvp 격자)
구간(seg) 0..4 = 위 인접 시점 간 Δlevel. 이벤트 구간 = {0: ASSEMBLE, 4: OVERDRIVE}.
"""
from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).parent / "data"
SRC = DATA / "panel_basic.csv"
OUT = DATA / "pilot_targets.csv"
DATES = ["2025-06-12", "2025-09-24", "2025-12-12", "2026-03-15", "2026-06-12", "2026-09-02"]
EVENT_SEG, BETWEEN_SEG = {0, 4}, {1, 2, 3}
SEED = 42
QUOTA = {"Dormant": 80, "Seasonal_Parker": None, "Persistent_cand": None, "Reactivated": 70}
NEW_QUOTA = 25   # event_period_new (2025-06-12 미존재) — 별도 세그먼트, 분석에서 분리


def load() -> tuple[dict, dict]:
    lv: dict[str, dict] = defaultdict(dict)
    coh: dict[str, str] = {}
    with SRC.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            coh[r["ocid"]] = r["cohort"]
            lv[r["ocid"]][r["date"]] = int(r["level"]) if r["level"] else None
    return lv, coh


def seq(d: dict) -> list:
    return [d.get(x) for x in DATES]


def segs(s: list) -> list:
    return [(s[i + 1] - s[i]) if s[i] is not None and s[i + 1] is not None else None
            for i in range(5)]


def classify(s: list) -> str | None:
    """PROVISIONAL. 명확한 케이스만 라벨, 애매하면 None(표본 제외)."""
    if s[0] is None:
        return "event_period_new"
    g = segs(s)
    known = [v for v in g if v is not None]
    if not known:
        return None
    lv_0612 = s[4]
    hi255 = (lv_0612 or 0) >= 255
    grew = [i for i, v in enumerate(g) if (v or 0) >= 2]

    if sum(known) == 0 and hi255:
        return "Dormant"                       # 전 구간 Δlevel = 0
    if len(grew) >= 3 and any(i in BETWEEN_SEG for i in grew) and hi255:
        return "Persistent_cand"               # ≥3 구간 성장 + 비이벤트 구간 ≥1 포함
    if any((g[i] or 0) >= 3 for i in EVENT_SEG) and all((g[i] or 0) <= 1 for i in BETWEEN_SEG) and hi255:
        return "Seasonal_Parker"               # 이벤트 구간만 성장, 시즌 사이 정체
    if (g[0] or 0) <= 1 and (g[1] or 0) <= 1 and any((g[i] or 0) >= 5 for i in (2, 3, 4)):
        return "Reactivated"                   # 초반 2구간 연속 정체 → 이후 단일 구간 버스트
    return None


def main() -> None:
    lv, coh = load()
    pools: dict[str, list[str]] = defaultdict(list)
    for oc, d in lv.items():
        lab = classify(seq(d))
        if lab:
            pools[lab].append(oc)

    rng = random.Random(SEED)
    picked: list[tuple[str, str]] = []
    for lab, ocs in pools.items():
        ocs_sorted = sorted(ocs)                      # 결정적
        rng.shuffle(ocs_sorted)
        if lab == "event_period_new":
            take = ocs_sorted[:NEW_QUOTA]
        else:
            q = QUOTA.get(lab)
            take = ocs_sorted if q is None else ocs_sorted[:q]
        picked += [(oc, lab) for oc in take]

    # 중복 방지 (한 ocid 가 두 라벨에 오면 안 됨 — classify 가 단일 반환이라 구조상 없음, 방어적 확인)
    seen = set()
    rows = []
    for oc, lab in picked:
        if oc in seen:
            continue
        seen.add(oc)
        levels = lv[oc]
        rows.append(dict(ocid=oc, provisional_label=lab, cohort=coh[oc],
                         **{f"lv_{x}": (levels.get(x) if levels.get(x) is not None else "")
                            for x in DATES}))

    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ocid", "provisional_label", "cohort"]
                                        + [f"lv_{x}" for x in DATES])
        w.writeheader()
        w.writerows(rows)

    print(f"pool 크기 (명확 케이스): { {k: len(v) for k, v in sorted(pools.items())} }")
    print(f"추출 {len(rows)} 명 → {OUT}")
    print(f"  label별: {dict(Counter(r['provisional_label'] for r in rows))}")
    for lab in sorted(set(r["provisional_label"] for r in rows)):
        cc = Counter(r["cohort"] for r in rows if r["provisional_label"] == lab)
        print(f"    {lab:18} {dict(cc)}")
    dup = len(picked) - len(rows)
    print(f"  중복 제거: {dup}   결측 레벨 칸: "
          f"{sum(1 for r in rows for x in DATES if r[f'lv_{x}'] == '')}")


if __name__ == "__main__":
    main()

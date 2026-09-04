"""Retrospective EDA — API 호출 0. panel_basic.csv + pilot_targets.csv + cohort_climb.csv 만 사용.

목적: Phase B 에서 검증할 leading indicator 후보를 좁힌다. provisional label 을 "증명"하지 않는다.
핵심 질문: 이벤트 기간 큰 ΔLevel 자체가 장기 progression 신호가 아닐 수 있고,
          성장의 지속성/분산이 더 나은 신호일 수 있는가.

label 생성 규칙(build_pilot_sample.classify)은 §1 에서 그대로 출력하고,
규칙에 직접 포함된 차이(definition-implied)와 추가 관측(additional)을 구분한다.
"""
from __future__ import annotations

import csv
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MILES = ["2025-06-12", "2025-09-24", "2025-12-12", "2026-03-15", "2026-06-12", "2026-09-02"]
SEG_NAME = ["seg0 ASSEMBLE(25여름)", "seg1 25가을", "seg2 CROWN초", "seg3 CROWN말", "seg4 OVERDRIVE(26여름)"]
EVENT_SEG, BETWEEN_SEG = {0, 4}, {1, 2, 3}


# ── 규칙 재출력 (label leakage 판정 기준) ───────────────────────────
RULES = """\
build_pilot_sample.classify() — PROVISIONAL label 규칙 (6 milestone, seg0..4 = 인접 간 Δlevel)
  EVENT_SEG={0,4} (ASSEMBLE, OVERDRIVE)  BETWEEN_SEG={1,2,3}
  Dormant         : s[0]존재 & 전 구간 Δ합=0 & lv(2026-06-12)>=255
  Persistent_cand : (Δ>=2 인 구간 수) >= 3  &  그중 >=1개가 BETWEEN_SEG  &  lv>=255
  Seasonal_Parker : EVENT_SEG 중 Δ>=3 인 구간 >=1  &  BETWEEN_SEG 3구간 모두 Δ<=1  &  lv>=255
  Reactivated     : seg0<=1 & seg1<=1 & (seg2|seg3|seg4 중 Δ>=5)
"""

DEFINITION_IMPLIED = """\
Parker vs Persistent_cand 비교에서 '규칙상 당연한' 차이 (= 새 발견 아님):
  - Persistent 는 'Δ>=2 구간 수 >= 3' + '그중 최소 1개가 시즌 사이(BETWEEN)' 가 정의.
    => n_active_intervals(Δ>=2) 가 Persistent >= 3, between-season 성장 존재 는 정의상 강제.
  - Parker 는 'BETWEEN 3구간 모두 Δ<=1' + 'EVENT 구간 중 Δ>=3 하나 이상' 이 정의.
    => Parker 의 between-season 성장 ~0, event 구간에 Δ>=3 하나 존재 는 정의상 강제.
  - 둘 다 lv(2026-06-12) >= 255.
규칙에 안 들어간 추가 관측(= 볼 가치 있음):
  - event-period ΔLevel 의 '크기' (Parker 가 Persistent 보다 더 큰가?)
  - max_interval_growth 절대값, burst_ratio(max/total), std(interval Δ), total_growth 크기
  - 성장이 어느 시즌(seg0 vs seg4)에 몰렸나
  - 같은 event-growth 수준에서 Parker/Persistent 가 갈리나 (matched)
  - Persistent 의 between 성장이 임계 부근(Δ2~3)인지 실질적(Δ10+)인지
"""


def load_levels() -> tuple[dict, dict]:
    lv: dict[str, dict] = defaultdict(dict)
    coh: dict[str, str] = {}
    with (DATA / "panel_basic.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            coh[r["ocid"]] = r["cohort"]
            lv[r["ocid"]][r["date"]] = int(r["level"]) if r["level"] else None
    return lv, coh


def load_labels() -> dict:
    lab: dict[str, str] = {}
    with (DATA / "pilot_targets.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            lab[r["ocid"]] = r["provisional_label"]
    return lab


def char_metrics(seq: list) -> dict | None:
    """seq = 6개 레벨(또는 None). interval 지표 계산. total_growth=0 안전 처리."""
    segs = [(seq[i + 1] - seq[i]) if seq[i] is not None and seq[i + 1] is not None else None
            for i in range(5)]
    known = [(i, d) for i, d in enumerate(segs) if d is not None]
    if not known:
        return None
    deltas = [d for _, d in known]
    first = next(v for v in seq if v is not None)
    last = next(v for v in reversed(seq) if v is not None)
    total = last - first
    mx = max(deltas)
    mx_seg = max(known, key=lambda x: x[1])[0]
    event_growth = sum(d for i, d in known if i in EVENT_SEG)
    between_growth = sum(d for i, d in known if i in BETWEEN_SEG)
    return dict(
        start_level=first, end_level=last, total_growth=total,
        n_intervals_known=len(known),
        max_interval_growth=mx, max_interval_seg=mx_seg,
        n_active_ge2=sum(1 for d in deltas if d >= 2),
        n_active_ge1=sum(1 for d in deltas if d >= 1),
        n_flat=sum(1 for d in deltas if d <= 0),
        std_interval=round(st.pstdev(deltas), 2) if len(deltas) > 1 else 0.0,
        burst_ratio=round(mx / total, 3) if total > 0 else None,
        event_growth=event_growth, between_growth=between_growth,
        seg0_assemble=segs[0], seg4_overdrive=segs[4],
    )


def summ(label, rows, keys):
    print(f"\n  [{label}] n={len(rows)}")
    for k in keys:
        vals = [r[k] for r in rows if r.get(k) is not None]
        if not vals:
            print(f"    {k:24} (전부 None)")
            continue
        vals_s = sorted(vals)
        med = st.median(vals_s)
        p25 = vals_s[max(0, int(len(vals_s) * .25) - 0)]
        p75 = vals_s[min(len(vals_s) - 1, int(len(vals_s) * .75))]
        print(f"    {k:24} median={med:>7.2f}  p25={p25:>6.2f} p75={p75:>6.2f}  "
              f"min={min(vals_s):>5.1f} max={max(vals_s):>6.1f}  mean={st.mean(vals):>6.2f}")


def main() -> None:
    lv, coh = load_levels()
    lab = load_labels()
    print("=" * 78)
    print("§1  LABEL 규칙 재출력")
    print("=" * 78)
    print(RULES)
    print(DEFINITION_IMPLIED)

    # ── §2-3  Parker vs Persistent_cand per-char ──────────────────
    per_char = []
    for oc, L in lab.items():
        if L not in ("Seasonal_Parker", "Persistent_cand"):
            continue
        seq = [lv[oc].get(d) for d in MILES]
        m = char_metrics(seq)
        if m is None:
            continue
        m.update(ocid=oc, label=L, cohort=coh[oc],
                 analysis_group="parker_vs_persistent",
                 levels="|".join(str(x) if x is not None else "" for x in seq))
        per_char.append(m)

    KEYS = ["start_level", "total_growth", "event_growth", "between_growth",
            "max_interval_growth", "burst_ratio", "std_interval",
            "n_active_ge2", "n_active_ge1", "n_flat"]
    print("=" * 78)
    print("§2-3  Parker(49) vs Persistent_cand(61) — 전체")
    print("=" * 78)
    park = [r for r in per_char if r["label"] == "Seasonal_Parker"]
    pers = [r for r in per_char if r["label"] == "Persistent_cand"]
    summ("Seasonal_Parker", park, KEYS)
    summ("Persistent_cand", pers, KEYS)
    print("\n  최대 성장 구간 분포 (max_interval_seg):")
    print(f"    Parker     : {dict(Counter(SEG_NAME[r['max_interval_seg']] for r in park))}")
    print(f"    Persistent : {dict(Counter(SEG_NAME[r['max_interval_seg']] for r in pers))}")

    # ── §4A  Parker 가 이벤트 기간 더 크게 성장하나 ──────────────
    print("\n" + "=" * 78)
    print("§4A  이벤트 기간 성장 크기 비교  (event_growth = seg0+seg4)")
    print("=" * 78)
    pe = sorted(r["event_growth"] for r in park)
    se = sorted(r["event_growth"] for r in pers)
    print(f"  Parker     event_growth: median {st.median(pe)}  mean {st.mean(pe):.1f}  범위 {pe[0]}~{pe[-1]}")
    print(f"  Persistent event_growth: median {st.median(se)}  mean {st.mean(se):.1f}  범위 {se[0]}~{se[-1]}")
    print(f"  → Parker median {'>' if st.median(pe) > st.median(se) else '<='} Persistent median")

    # ── §4C  matched: 비슷한 event_growth 끼리 ───────────────────
    print("\n" + "=" * 78)
    print("§4C  event_growth 버킷별 matched descriptive (가장 중요)")
    print("=" * 78)
    buckets = [(0, 1), (2, 3), (4, 6), (7, 10), (11, 20), (21, 999)]
    print(f"  {'event_growth':>14} | {'grp':10} | n | between_growth med | burst_ratio med | total_growth med | n_active_ge2 med")
    for lo, hi in buckets:
        for grp, rows in (("Parker", park), ("Persistent", pers)):
            sel = [r for r in rows if lo <= r["event_growth"] <= hi]
            if not sel:
                continue
            bg = st.median([r["between_growth"] for r in sel])
            br = [r["burst_ratio"] for r in sel if r["burst_ratio"] is not None]
            tg = st.median([r["total_growth"] for r in sel])
            na = st.median([r["n_active_ge2"] for r in sel])
            print(f"  {f'{lo}-{hi}':>14} | {grp:10} | {len(sel):>2} | {bg:>17.1f} | "
                  f"{(st.median(br) if br else float('nan')):>15.3f} | {tg:>16.1f} | {na:>15.1f}")

    # ── §5  cohort-stratified ────────────────────────────────────
    print("\n" + "=" * 78)
    print("§5  cohort 내부 Parker vs Persistent (n 작으면 결론 금지)")
    print("=" * 78)
    for c in ("at260", "burnend", "climb", "past260", "approach"):
        cp = [r for r in park if r["cohort"] == c]
        cs = [r for r in pers if r["cohort"] == c]
        if not cp and not cs:
            continue
        print(f"\n  cohort={c}  Parker n={len(cp)}  Persistent n={len(cs)}")
        if cp:
            print(f"    Parker     event_growth med {st.median([r['event_growth'] for r in cp]):.1f} | "
                  f"between med {st.median([r['between_growth'] for r in cp]):.1f} | "
                  f"burst med {st.median([r['burst_ratio'] for r in cp if r['burst_ratio'] is not None] or [float('nan')]):.3f}")
        if cs:
            print(f"    Persistent event_growth med {st.median([r['event_growth'] for r in cs]):.1f} | "
                  f"between med {st.median([r['between_growth'] for r in cs]):.1f} | "
                  f"burst med {st.median([r['burst_ratio'] for r in cs if r['burst_ratio'] is not None] or [float('nan')]):.3f}")

    # ── §6  climb 260 case study ────────────────────────────────
    print("\n" + "=" * 78)
    print("§6  climb — final-260(49) vs 261+(5) case study  (n=5 → 통계 결론 금지)")
    print("=" * 78)
    clr = list(csv.DictReader((DATA / "cohort_climb.csv").open(encoding="utf-8-sig", newline="")))
    by = defaultdict(list)
    for r in clr:
        if not r["error_code"] and r["level"]:
            by[r["character_name"]].append(
                (r["date"], int(r["level"]), float(r["exp_rate"] or 0),
                 int(r["combat_power"]) if r["combat_power"] else None))
    for k in by:
        by[k].sort()
    ANCHOR_END_OFF = 34
    from datetime import date
    A = date(2026, 6, 18)
    case_rows = []
    for nm, s in by.items():
        levels = [x[1] for x in s]
        if max(levels) < 260:
            continue
        i260 = next(i for i, x in enumerate(s) if x[1] >= 260)
        d260, _, er260, _ = s[i260]
        off = (date.fromisoformat(d260) - A).days
        final_lv, final_er = s[-1][1], s[-1][2]
        cps = [x[3] for x in s if x[3] is not None]
        cp_delta = (cps[-1] - cps[0]) if len(cps) >= 2 else None
        grp = "reach_261plus" if final_lv >= 261 else "final_260"
        case_rows.append(dict(ocid="", character_name=nm, analysis_group="climb_260_casestudy",
                              label=grp, cohort="climb",
                              first_260_offset=off, exp_rate_at_260=round(er260, 2),
                              obs_days_after_260=ANCHOR_END_OFF - off,
                              end_level=final_lv, final_exp_rate=round(final_er, 2),
                              cp_delta_5snap=cp_delta))
    for grp in ("final_260", "reach_261plus"):
        g = [r for r in case_rows if r["label"] == grp]
        print(f"\n  [{grp}] n={len(g)}")
        for k in ("first_260_offset", "exp_rate_at_260", "obs_days_after_260", "end_level", "final_exp_rate"):
            v = sorted(r[k] for r in g)
            print(f"    {k:20} median={st.median(v):>7.2f}  범위 {v[0]}~{v[-1]}")
        cpd = [r["cp_delta_5snap"] for r in g if r["cp_delta_5snap"] is not None]
        if cpd:
            print(f"    cp_delta_5snap       median={st.median(sorted(cpd)):>10.0f}  범위 {min(cpd)}~{max(cpd)}  (n={len(cpd)})")
    for r in sorted((r for r in case_rows if r["label"] == "reach_261plus"), key=lambda x: x["first_260_offset"]):
        print(f"    261+ 사례: 도달 D+{r['first_260_offset']:>2} exp_rate {r['exp_rate_at_260']:>5}% "
              f"관측{r['obs_days_after_260']:>2}일 → final Lv{r['end_level']} ({r['final_exp_rate']}%) "
              f"cpΔ={r['cp_delta_5snap']}")

    # ── summary CSV ────────────────────────────────────────────
    out = DATA / "retrospective_eda_summary.csv"
    cols = ["analysis_group", "label", "cohort", "ocid", "character_name", "levels",
            "start_level", "end_level", "total_growth", "event_growth", "between_growth",
            "max_interval_growth", "max_interval_seg", "burst_ratio", "std_interval",
            "n_active_ge2", "n_active_ge1", "n_flat", "n_intervals_known",
            "seg0_assemble", "seg4_overdrive",
            "first_260_offset", "exp_rate_at_260", "obs_days_after_260",
            "final_exp_rate", "cp_delta_5snap"]
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in per_char + case_rows:
            w.writerow(r)
    print(f"\n→ {out}  ({len(per_char)} + {len(case_rows)} rows)")


if __name__ == "__main__":
    main()

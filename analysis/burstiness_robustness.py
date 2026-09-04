"""Burstiness Robustness Check — API 호출 0. panel_basic.csv + pilot_targets.csv 만.

질문: burst_ratio(=maxΔ/totalΔ) 하나에서만 Parker/Persistent 차이가 나는가, 아니면
      대체 concentration 산식·최소 성장 필터·cohort 내부에서도 유지되는가.
circularity: label 규칙이 Persistent 는 'Δ>=2 구간 >=3', Parker 는 'BETWEEN 3구간 Δ<=1' 을
      강제 → n_active_ge2 는 정의상 완전 분리(Persistent>=3, Parker<=2). 모든 concentration
      지표는 '성장이 몇 개 구간에 퍼졌나' 의 단조함수라 이 분리를 물려받는다. 여기서는 그
      정도를 정량화한다.

레벨은 단조 비감소 → interval Δ_i >= 0. 음수 interval 없음(있었다면 0 clip + flag).
total_growth == 0 → 모든 concentration = None, 지표 비교에서 제외(개수만 보고).
"""
from __future__ import annotations

import csv
import math
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MILES = ["2025-06-12", "2025-09-24", "2025-12-12", "2026-03-15", "2026-06-12", "2026-09-02"]
SEG = ["seg0", "seg1", "seg2", "seg3", "seg4"]
EVENT_SEG = {0, 4}


def load():
    lv = defaultdict(dict)
    coh = {}
    with (DATA / "panel_basic.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            coh[r["ocid"]] = r["cohort"]
            lv[r["ocid"]][r["date"]] = int(r["level"]) if r["level"] else None
    lab = {}
    with (DATA / "pilot_targets.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            lab[r["ocid"]] = r["provisional_label"]
    return lv, coh, lab


def metrics(seq):
    d = [(seq[i + 1] - seq[i]) if seq[i] is not None and seq[i + 1] is not None else None
         for i in range(5)]
    kd = [x for x in d if x is not None]
    if not kd:
        return None
    d0 = [max(0, x) for x in kd]                 # 음수 clip (레벨 데이터엔 없음)
    total = sum(d0)
    first = next(v for v in seq if v is not None)
    last = next(v for v in reversed(seq) if v is not None)
    out = dict(
        total_growth=last - first,
        event_growth=sum(x for i, x in enumerate(d) if x is not None and i in EVENT_SEG),
        between_growth=sum(x for i, x in enumerate(d) if x is not None and i in {1, 2, 3}),
        n_active_ge2=sum(1 for x in d0 if x >= 2),
        n_active_ge1=sum(1 for x in d0 if x >= 1),
        seg_deltas=d,
    )
    if total <= 0:
        for k in ("top1_share", "top2_share", "hhi", "disp_entropy", "conc_entropy", "gap12"):
            out[k] = None
        return out
    s = sorted(d0, reverse=True)
    out["top1_share"] = round(s[0] / total, 3)
    out["top2_share"] = round((s[0] + s[1]) / total, 3)
    out["hhi"] = round(sum((x / total) ** 2 for x in d0), 3)
    ps = [x / total for x in d0 if x > 0]
    H = -sum(p * math.log(p) for p in ps)
    out["disp_entropy"] = round(H / math.log(5), 3)          # 0=집중, 1=완전 분산(5구간)
    out["conc_entropy"] = round(1 - H / math.log(5), 3)
    out["gap12"] = s[0] - s[1]
    return out


def med(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]
    return round(st.median(v), 3) if v else None


CONC = ["top1_share", "top2_share", "hhi", "conc_entropy", "gap12"]


def block(title, park, pers, keys=("total_growth", "event_growth", "between_growth", *CONC, "n_active_ge2")):
    print(f"\n{title}   Parker n={len(park)}  Persistent n={len(pers)}")
    hdr = "  " + "metric".ljust(15) + "Parker".rjust(10) + "Persistent".rjust(12)
    print(hdr)
    for k in keys:
        print(f"  {k:15}{str(med(park, k)):>10}{str(med(pers, k)):>12}")


def main():
    lv, coh, lab = load()
    rows = []
    for oc, L in lab.items():
        if L not in ("Seasonal_Parker", "Persistent_cand"):
            continue
        m = metrics([lv[oc].get(d) for d in MILES])
        if not m:
            continue
        m.update(ocid=oc, label=L, cohort=coh[oc],
                 start_level=next(v for v in [lv[oc].get(d) for d in MILES] if v is not None),
                 levels="|".join(str(lv[oc].get(d) or "") for d in MILES))
        rows.append(m)
    park = [r for r in rows if r["label"] == "Seasonal_Parker"]
    pers = [r for r in rows if r["label"] == "Persistent_cand"]

    print("=" * 80)
    print("§1  대체 concentration 산식 (전체)")
    print("=" * 80)
    print("  top1_share = maxΔ/total | top2_share = (top2합)/total | hhi = Σ(Δi/total)^2")
    print("  conc_entropy = 1 - H/ln5 (1=완전집중) | gap12 = maxΔ - 2ndΔ")
    print(f"  total_growth==0 (지표 None): Parker {sum(1 for r in park if r['top1_share'] is None)} "
          f"/ Persistent {sum(1 for r in pers if r['top1_share'] is None)}")
    block("전체", park, pers)
    # 각 산식이 같은 방향인가
    print("\n  방향 확인 (Parker median > Persistent median 이면 '집중도 Parker↑'):")
    for k in CONC:
        p, s = med(park, k), med(pers, k)
        print(f"    {k:15} Parker {p} vs Persistent {s}  → {'Parker 더 집중' if p > s else 'Persistent 더 집중 또는 동률'}")

    print("\n" + "=" * 80)
    print("§2  최소 성장량 필터 (작은 total 이 concentration 을 기계적으로 올리나)")
    print("=" * 80)
    for thr in (0, 5, 10, 20):
        pk = [r for r in park if r["total_growth"] >= thr]
        ps = [r for r in pers if r["total_growth"] >= thr]
        print(f"\n  total_growth >= {thr}")
        block(f"  ≥{thr}", pk, ps, keys=("total_growth", *CONC, "n_active_ge2"))

    print("\n" + "=" * 80)
    print("§3  cohort 내부")
    print("=" * 80)
    for c in ("at260", "burnend", "climb", "past260", "approach"):
        pk = [r for r in park if r["cohort"] == c]
        ps = [r for r in pers if r["cohort"] == c]
        if not pk and not ps:
            continue
        block(f"cohort={c}", pk, ps)
        if c == "burnend":
            print("\n  --- burnend 개별 (매칭 가장 좋음) ---")
            for r in sorted(pk + ps, key=lambda x: (x["label"], -x["total_growth"])):
                print(f"    {r['label'][:11]:11} start{r['start_level']:>4} "
                      f"lv[{r['levels']}] totΔ{r['total_growth']:>3} evΔ{r['event_growth']:>3} "
                      f"btwΔ{r['between_growth']:>3} top1{r['top1_share']} hhi{r['hhi']} "
                      f"nact≥2={r['n_active_ge2']}")

    print("\n" + "=" * 80)
    print("§3b  circularity 정량화 — n_active_ge2 로 조건부")
    print("=" * 80)
    print("  Persistent 는 정의상 n_active_ge2>=3, Parker 는 <=2 → 겹치지 않음.")
    for r in rows:
        pass
    for lo, grp in ((park, "Parker"), (pers, "Persistent")):
        by_n = defaultdict(list)
        for r in lo:
            by_n[r["n_active_ge2"]].append(r)
        for n in sorted(by_n):
            g = by_n[n]
            print(f"  {grp:10} n_active_ge2={n}: cnt={len(g):>2}  top1 med={med(g,'top1_share')}  "
                  f"hhi med={med(g,'hhi')}  conc_entropy med={med(g,'conc_entropy')}")
    print("  → n_active_ge2 만으로 두 그룹이 완전 분리되므로, concentration 지표가 label 대비")
    print("    '추가 분리력' 을 주는지는 이 라벨 집합에서는 판정 불가 (circular).")

    print("\n" + "=" * 80)
    print("§4  matched pairs — 같은 cohort + event Δ 근접(±3) + start level 근접(±8)")
    print("=" * 80)
    pairs = []
    for a in pers:
        for b in park:
            if a["cohort"] != b["cohort"]:
                continue
            if abs(a["event_growth"] - b["event_growth"]) > 3:
                continue
            if abs(a["start_level"] - b["start_level"]) > 8:
                continue
            pairs.append((abs(a["event_growth"] - b["event_growth"]),
                          abs(a["start_level"] - b["start_level"]), a, b))
    pairs.sort(key=lambda x: (x[0], x[1]))
    seen_p, seen_k, shown = set(), set(), []
    for _, _, a, b in pairs:
        if a["ocid"] in seen_p or b["ocid"] in seen_k:
            continue
        seen_p.add(a["ocid"]); seen_k.add(b["ocid"]); shown.append((a, b))
        if len(shown) >= 10:
            break
    print(f"  찾은 쌍 {len(shown)} (Persistent 1개는 한 번만 사용)")
    for i, (a, b) in enumerate(shown, 1):
        print(f"\n  쌍{i}  cohort={a['cohort']}  (evΔ P={a['event_growth']} K={b['event_growth']}, "
              f"start P={a['start_level']} K={b['start_level']})")
        print(f"    Persistent lv[{a['levels']}] segΔ{a['seg_deltas']}  totΔ{a['total_growth']} "
              f"btwΔ{a['between_growth']} top1{a['top1_share']} hhi{a['hhi']}")
        print(f"    Parker     lv[{b['levels']}] segΔ{b['seg_deltas']}  totΔ{b['total_growth']} "
              f"btwΔ{b['between_growth']} top1{b['top1_share']} hhi{b['hhi']}")

    out = DATA / "burstiness_robustness_summary.csv"
    cols = ["label", "cohort", "ocid", "levels", "start_level", "total_growth", "event_growth",
            "between_growth", "n_active_ge1", "n_active_ge2",
            "top1_share", "top2_share", "hhi", "disp_entropy", "conc_entropy", "gap12"]
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"\n→ {out}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()

"""Part 2 — 2025~2026 longitudinal 패널 수집. `collect.py` 와 완전히 독립 (그 파일은 불변).

무엇: 기존 코호트 CSV의 ocid 에 대해 과거 시점 스냅샷을 모아 시즌 간 성장 궤적을 복원한다.
     상태 분류(Parker/Persistent/Reactivated/Dormant)와 leading indicator 분석의 원천.

설계 원칙
  - 날짜·endpoint 는 panel_config.py (코드에서 분리, 사람이 검토).
  - classification / feature engineering 로직은 여기 없음. raw 스냅샷만 보존.
  - (ocid, date, endpoint) 단위 재개. 정상 수집(ok) 또는 확정 실패(empty/http_400/http_404)
    조합은 재호출하지 않음. 일시 실패(429/5xx/timeout)만 다음 실행에서 재시도.
  - --dry-run 으로 호출 없이 표본·날짜·endpoint 구성과 예상 호출량을 먼저 출력.

사용 예
  python collect_panel.py --dry-run --sampling stratified --per-cohort 150 --tier mvp --endpoints basic
  python collect_panel.py --dry-run --sampling random --n 750 --tier full --endpoints all
  python collect_panel.py --sampling list --list-file data/stage2_targets.txt --endpoints invest
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests

import panel_config as cfg

BASE = "https://open.api.nexon.com/maplestory/v1"
REQ_SLEEP = 0.25
TIMEOUT = 10
BACKOFF = [1, 2, 4, 8]
DATA_DIR = Path(__file__).parent / cfg.DATA_DIR

PANEL_BASIC = DATA_DIR / "panel_basic.csv"          # 평면: 레벨 궤적
PANEL_STATUS = DATA_DIR / "panel_status.csv"        # 모든 (ocid,date,ep) 시도의 결과 코드
RAW_JSONL = lambda ep: DATA_DIR / f"panel_raw_{ep}.jsonl"   # invest endpoint raw 보존

BASIC_COLUMNS = ["cohort", "ocid", "date", "role", "level", "exp", "exp_rate", "error_code"]
STATUS_COLUMNS = ["ocid", "date", "endpoint", "http_status", "outcome", "ts"]

# outcome 값: ok | empty | http_400 | http_404 | http_429_giveup | http_5xx_giveup | timeout
TERMINAL = {"ok", "empty", "http_400", "http_404"}      # 재호출 안 함
RETRYABLE = {"http_429_giveup", "http_5xx_giveup", "timeout"}

_call_count = 0


# ── API ────────────────────────────────────────────────────────────
def _load_dotenv() -> None:
    env = Path(__file__).parent / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _api_key() -> str:
    _load_dotenv()
    key = os.environ.get("NXOPEN_API_KEY")
    if not key:
        sys.exit("NXOPEN_API_KEY 없음 — .env 또는 환경변수로 설정하세요.")
    return key


def _get(path: str, params: dict) -> tuple[int, dict]:
    """(http_status, body). 네트워크 예외는 (0, {"__timeout__": True})."""
    global _call_count
    headers = {"x-nxopen-api-key": _api_key()}
    attempt = 0
    while True:
        _call_count += 1
        try:
            r = requests.get(f"{BASE}{path}", params=params, headers=headers, timeout=TIMEOUT)
        except requests.RequestException:
            time.sleep(REQ_SLEEP)
            if attempt < 1:
                attempt += 1
                continue
            return 0, {"__timeout__": True}
        time.sleep(REQ_SLEEP)
        if r.status_code == 200:
            try:
                return 200, r.json()
            except ValueError:
                return 200, {}
        if r.status_code in (429,) or r.status_code >= 500:
            if attempt < len(BACKOFF):
                time.sleep(BACKOFF[attempt])
                attempt += 1
                continue
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, {}


# ── 응답 → outcome 판정 (endpoint_feasibility_probe.md §2) ─────────
_EMPTY_KEYS = {
    "basic": "character_level",
    "stat": "final_stat",
    "hexamatrix": "character_hexa_core_equipment",
    "hexamatrix-stat": "character_hexa_stat_core",
    "symbol": "symbol",
    "item-equipment": "item_equipment",
    "union": "union_level",
}


def classify(ep: str, status: int, body: dict) -> str:
    if status == 0 or body.get("__timeout__"):
        return "timeout"
    if status == 200:
        v = body.get(_EMPTY_KEYS[ep])
        if v is None or v == [] or v == "":
            return "empty"
        return "ok"
    if status == 400:
        return "http_400"
    if status == 404:
        return "http_404"
    if status == 429:
        return "http_429_giveup"
    if status >= 500:
        return "http_5xx_giveup"
    return f"http_{status}"


def parse_combat_power(final_stat) -> int | None:
    for s in final_stat or []:
        if s.get("stat_name") == "전투력":
            try:
                return int(s["stat_value"])
            except (ValueError, TypeError, KeyError):
                return None
    return None


# ── 표본 ───────────────────────────────────────────────────────────
def load_pool() -> list[tuple[str, str]]:
    """[(cohort, ocid)] — 코호트 CSV 등장 순서, ocid 중복 시 첫 코호트 유지."""
    seen, pool = set(), []
    for name in cfg.COHORT_FILES:
        p = DATA_DIR / f"cohort_{name}.csv"
        if not p.exists():
            continue
        with p.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                oc = r.get("ocid") or ""
                if oc and oc not in seen:
                    seen.add(oc)
                    pool.append((name, oc))
    return pool


def sample(pool, method: str, *, n: int, per_cohort: int, seed: int,
           list_file: str | None) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    if method == "list":
        # 줄 목록. CSV(헤더 + 여러 컬럼)면 첫 컬럼(ocid) 사용, 'ocid' 헤더 줄은 건너뜀.
        raw = [x.strip() for x in Path(list_file).read_text(encoding="utf-8-sig").splitlines() if x.strip()]
        wanted = [ln.split(",")[0].strip() for ln in raw if ln.split(",")[0].strip().lower() != "ocid"]
        by_oc = {oc: (c, oc) for c, oc in pool}
        # list-file 은 ocid 또는 character_name 둘 다 허용 (name 은 cohort CSV 로 역매핑)
        name2oc = {}
        for name in cfg.COHORT_FILES:
            p = DATA_DIR / f"cohort_{name}.csv"
            if p.exists():
                with p.open(encoding="utf-8-sig", newline="") as f:
                    for r in csv.DictReader(f):
                        if r.get("ocid"):
                            name2oc[r["character_name"]] = r["ocid"]
        out = []
        for w in wanted:
            oc = w if w in by_oc else name2oc.get(w)
            if oc and oc in by_oc:
                out.append(by_oc[oc])
        return out
    if method == "random":
        p = pool[:]
        rng.shuffle(p)
        return p[:n]
    if method == "stratified":
        buckets: dict[str, list] = {}
        for c, oc in pool:
            buckets.setdefault(c, []).append((c, oc))
        out = []
        for c, items in buckets.items():
            rng.shuffle(items)
            out.extend(items[:per_cohort])
        return out
    sys.exit(f"unknown sampling method: {method}")


# ── task 생성 ──────────────────────────────────────────────────────
def today_max() -> date:
    return date.today() - timedelta(days=cfg.API_MAX_LAG_DAYS)


def build_snapshots(tier: str) -> list[dict]:
    if tier == "pilot":
        return list(cfg.PILOT_MILESTONES)
    if tier == "followup":
        return list(cfg.POST_EVENT_FOLLOWUP)
    tiers = {"mvp": {"mvp"}, "full": {"mvp", "full"}}
    if tier not in tiers:
        sys.exit(f"unknown tier: {tier} (mvp|full|followup|pilot)")
    return [s for s in cfg.SNAPSHOTS if s["tier"] in tiers[tier]]


def endpoint_set(which: str) -> list[str]:
    if which == "pilot":
        return list(cfg.PILOT_ENDPOINTS)
    if which == "basic":
        return ["basic"]
    if which == "invest":
        return [e for e, m in cfg.ENDPOINTS.items() if m["tier"] == "invest"]
    if which == "all":
        return list(cfg.ENDPOINTS)
    # 콤마 구분 명시 리스트
    eps = [e.strip() for e in which.split(",") if e.strip()]
    for e in eps:
        if e not in cfg.ENDPOINTS:
            sys.exit(f"unknown endpoint: {e}")
    return eps


def date_ok(ep: str, d: str) -> bool:
    return cfg.API_MIN_DATE <= d <= today_max().isoformat() and cfg.ENDPOINTS[ep]["earliest"] <= d


def make_tasks(chars, snapshots, eps, tier) -> list[dict]:
    """basic → 선택된 tier 의 모든 snapshot 날짜.
    invest endpoint → mvp/full tier 는 INVEST_MILESTONES(pre-event), followup/pilot tier 는 snapshot 날짜."""
    if tier in ("followup", "pilot"):
        invest_dates = [(s["date"], s["role"]) for s in snapshots]
    else:
        invest_dates = [(d, "milestone") for d in cfg.INVEST_MILESTONES]
    tasks = []
    for ep in eps:
        dates = [(s["date"], s["role"]) for s in snapshots] if ep == "basic" else invest_dates
        for d, role in dates:
            if not date_ok(ep, d):
                continue
            for c, oc in chars:
                tasks.append(dict(cohort=c, ocid=oc, date=d, role=role, endpoint=ep))
    return tasks


# ── 재개 상태 ──────────────────────────────────────────────────────
def load_done() -> set[tuple[str, str, str]]:
    """(ocid, date, endpoint) → 확정 완료(ok/empty/http_400/http_404) 조합."""
    done = set()
    if PANEL_STATUS.exists():
        with PANEL_STATUS.open(encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                if r["outcome"] in TERMINAL:
                    done.add((r["ocid"], r["date"], r["endpoint"]))
    return done


def _append(path: Path, columns, rows):
    new = not path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        if new:
            w.writeheader()
        w.writerows(rows)


def _append_jsonl(path: Path, obj):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ── dry-run 출력 ──────────────────────────────────────────────────
def print_plan(args, chars, snapshots, eps, tasks, done):
    print("=" * 72)
    print("PANEL 수집 계획 (검토용) — 아직 API 호출 안 함" if args.dry_run else "PANEL 수집 시작")
    print("=" * 72)
    print(f"\n[표본]  method={args.sampling}  seed={args.seed}")
    by_c: dict[str, int] = {}
    for c, _ in chars:
        by_c[c] = by_c.get(c, 0) + 1
    print(f"  코호트별: {by_c}   총 {len(chars)} 캐릭터")

    print(f"\n[날짜 격자]  tier={args.tier}")
    for s in snapshots:
        print(f"  {s['date']}  {s['role']:22} ({s['tier']})")
    mx = today_max().isoformat()
    print(f"  * 조회 가능 상한(T-1) = {mx} / 하한 = {cfg.API_MIN_DATE}")

    inv_dates = [s["date"] for s in snapshots] if args.tier in ("followup", "pilot") else cfg.INVEST_MILESTONES
    print(f"\n[endpoint]  {eps}")
    for ep in eps:
        m = cfg.ENDPOINTS[ep]
        cand = [s["date"] for s in snapshots] if ep == "basic" else inv_dates
        skipped = [d for d in cand if not date_ok(ep, d)]
        note = f"  earliest={m['earliest']}"
        if skipped:
            note += f"  → 제외 날짜(범위밖): {skipped}"
        print(f"  {ep:16}{note}")

    print(f"\n[호출량 추정]")
    todo = [t for t in tasks if (t['ocid'], t['date'], t['endpoint']) not in done]
    print(f"  전체 task            : {len(tasks):,}")
    print(f"  이미 완료(재개 스킵) : {len(tasks) - len(todo):,}")
    print(f"  이번 실행 호출 예상   : {len(todo):,}   (~{len(todo) * REQ_SLEEP / 60:.0f}분 @ {REQ_SLEEP}s/call)")
    per_ep: dict[str, int] = {}
    for t in todo:
        per_ep[t["endpoint"]] = per_ep.get(t["endpoint"], 0) + 1
    print(f"  endpoint별           : {per_ep}")

    print(f"\n[출력 파일]")
    if "basic" in eps:
        print(f"  {PANEL_BASIC}          (평면, basic)")
    print(f"  {PANEL_STATUS}         (모든 시도의 outcome 코드)")
    for ep in eps:
        if ep != "basic":
            print(f"  {RAW_JSONL(ep)}   (raw JSON 보존)")
    print("=" * 72)


# ── 메인 ──────────────────────────────────────────────────────────
def run(args):
    DATA_DIR.mkdir(exist_ok=True)
    pool = load_pool()
    if not pool:
        sys.exit("data/cohort_*.csv 없음 — 먼저 collect.py 산출물이 있어야 함.")
    chars = sample(pool, args.sampling, n=args.n, per_cohort=args.per_cohort,
                   seed=args.seed, list_file=args.list_file)
    if not chars:
        sys.exit("표본이 비었음 — 인자 확인.")
    snapshots = build_snapshots(args.tier)
    eps = endpoint_set(args.endpoints)
    tasks = make_tasks(chars, snapshots, eps, args.tier)
    done = load_done()

    print_plan(args, chars, snapshots, eps, tasks, done)
    if args.dry_run:
        return
    if not args.yes:
        ans = input("\n실제 수집을 진행합니다. 계속하려면 'yes' 입력: ").strip().lower()
        if ans != "yes":
            print("취소됨.")
            return

    todo = [t for t in tasks if (t["ocid"], t["date"], t["endpoint"]) not in done]
    basic_buf, status_buf = [], []
    for i, t in enumerate(todo, 1):
        ep, oc, d = t["endpoint"], t["ocid"], t["date"]
        status, body = _get(cfg.ENDPOINTS[ep]["path"], {"ocid": oc, "date": d})
        outcome = classify(ep, status, body)
        status_buf.append(dict(ocid=oc, date=d, endpoint=ep, http_status=status,
                               outcome=outcome, ts=int(time.time())))
        if ep == "basic":
            # 일시 실패(RETRYABLE)는 다음 실행에서 재처리되므로 panel_basic 에 쓰지 않는다
            # (안 그러면 resume 시 같은 (ocid,date) 가 두 번 append 됨). 확정 실패(http_400/404)는 남긴다.
            if outcome not in RETRYABLE:
                lvl = body.get("character_level") if outcome in ("ok", "empty") else None
                basic_buf.append(dict(cohort=t["cohort"], ocid=oc, date=d, role=t["role"],
                                      level=lvl, exp=body.get("character_exp"),
                                      exp_rate=body.get("character_exp_rate"),
                                      error_code="" if outcome == "ok" else outcome))
        elif outcome in ("ok", "empty"):
            rec = {"ocid": oc, "date": d, "role": t["role"], "cohort": t["cohort"],
                   "outcome": outcome, "endpoint": ep, "json": body}
            if ep == "stat":
                rec["combat_power"] = parse_combat_power(body.get("final_stat"))
            _append_jsonl(RAW_JSONL(ep), rec)

        if i % 50 == 0 or i == len(todo):
            if basic_buf:
                _append(PANEL_BASIC, BASIC_COLUMNS, basic_buf); basic_buf = []
            _append(PANEL_STATUS, STATUS_COLUMNS, status_buf); status_buf = []
            print(f"  [{i:,}/{len(todo):,}]  누적 콜 {_call_count:,}   last={ep} {d} {outcome}")

        if args.budget and _call_count >= args.budget:
            print(f"\n예산({args.budget}) 도달 — 중단. 다시 실행하면 이어서.")
            break

    if basic_buf:
        _append(PANEL_BASIC, BASIC_COLUMNS, basic_buf)
    if status_buf:
        _append(PANEL_STATUS, STATUS_COLUMNS, status_buf)

    # 남은 일시 실패 요약
    retry_left = 0
    if PANEL_STATUS.exists():
        with PANEL_STATUS.open(encoding="utf-8-sig", newline="") as f:
            last: dict[tuple, str] = {}
            for r in csv.DictReader(f):
                last[(r["ocid"], r["date"], r["endpoint"])] = r["outcome"]
        retry_left = sum(1 for v in last.values() if v in RETRYABLE)
    print(f"\n총 API 호출: {_call_count:,}   재시도 남음(일시 실패): {retry_left:,}")
    print("완료." if retry_left == 0 else "일부 일시 실패 — 다시 실행하면 그 조합만 재시도.")


def main():
    ap = argparse.ArgumentParser(description="Part 2 longitudinal 패널 수집")
    ap.add_argument("--sampling", choices=["stratified", "random", "list"], default="stratified")
    ap.add_argument("--n", type=int, default=750, help="random 표본 크기")
    ap.add_argument("--per-cohort", type=int, default=150, help="stratified 코호트당 표본")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--list-file", help="sampling=list 일 때 ocid 또는 character_name 줄 목록")
    ap.add_argument("--tier", choices=["mvp", "full", "followup", "pilot"], default="mvp")
    ap.add_argument("--endpoints", default="basic",
                    help="basic | invest | all | pilot | 콤마구분(stat,union,...)")
    ap.add_argument("--budget", type=int, default=0, help="이번 실행 최대 호출 수 (0=무제한)")
    ap.add_argument("--dry-run", action="store_true", help="호출 없이 계획만 출력")
    ap.add_argument("--yes", action="store_true", help="확인 프롬프트 건너뜀")
    run(ap.parse_args())


if __name__ == "__main__":
    main()

"""넥슨 오픈 API로 레벨대별 코호트의 일간 소급 스냅샷을 수집한다.

설계: 실측으로 계획문서 코호트를 재정의 (계획문서 "설계 변경 2", 스펙 §3/§6).
  - 랭킹 page↔레벨 실측 매핑으로 260 허들 주변 4개 레벨대 코호트 고정
  - 앵커일(2026-06-18)부터 DAILY_DAYS 일간 매일 레벨 스냅샷 = 시계열
  - 전투력(stat)은 비용이 커서 STAT_OFFSETS 날짜에만
실행: NXOPEN_API_KEY 설정 후  `python collect.py`
  개발단계 일 1,000콜 한도 → 여러 날 나눠 실행. 앵커일이 과거 고정이라 데이터 불변.
  이미 수집된 (캐릭터, 날짜) 행은 건너뛴다 (재개 가능, 행 단위로 즉시 append).
"""
from __future__ import annotations

import csv
import os
import sys
import time
import random
from datetime import date, timedelta
from pathlib import Path

import requests

# Windows 콘솔(cp949)에서도 로그가 안 깨지도록. 수집이 몇 시간 돌므로 예외로 죽지 않게.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# ---- 수집 파라미터 (스펙 §3.1) --------------------------------------------
BASE = "https://open.api.nexon.com/maplestory/v1"
REQ_SLEEP = 0.25
TIMEOUT = 10
MAX_RETRY = 3
BACKOFF = [1, 2, 4]
RANDOM_SEED = 42
# live_ (정식) 키는 한도가 넉넉 → 전체 수집(~12,000콜)을 1회에 완주. 안전 상한으로만 사용.
# test_ (개발단계) 키면 1000 으로 낮추고 여러 날 나눠 실행.
DAILY_CALL_BUDGET = 15000
DATA_DIR = Path(__file__).parent / "data"

RANKING_WORLD_TYPE = 0          # 실측 확인 완료: 0=일반 서버
ANCHOR = "2026-06-18"          # 여름 성장 이벤트 시작일 = 시계열 앵커
DAILY_DAYS = 25               # D+0 .. D+24 매일 basic
STAT_OFFSETS = [0, 8, 16, 24]  # 전투력은 이 오프셋에만
SAMPLE_N = 100               # 코호트당 표본

# 실측 랭킹 page↔레벨 (2026-06-18, world_type=0). page N = 랭킹 (N-1)*200+1 .. N*200
COHORTS = [
    dict(name="approach", page=21000, target_level=251, desc="허들 접근 (260 미만)"),
    dict(name="at260",    page=15000, target_level=260, desc="260 정체 플래토 (rank ~3M)"),
    dict(name="past260",  page=10000, target_level=262, desc="260 직후"),
    dict(name="burnend",  page=2500,  target_level=281, desc="버닝 BEYOND 종료 지점"),
]

CSV_COLUMNS = ["cohort", "character_name", "ocid", "date",
               "level", "exp", "exp_rate", "combat_power", "error_code"]

_call_count = 0
_ocid_cache: dict[str, str | None] = {}


# ---- 순수 헬퍼 (네트워크 없음 — test_collect.py) -------------------------
def daily_dates(anchor: str, n: int) -> list[str]:
    a = date.fromisoformat(anchor)
    return [(a + timedelta(days=i)).isoformat() for i in range(n)]


def stat_dates(anchor: str, offsets: list[int]) -> list[str]:
    a = date.fromisoformat(anchor)
    return [(a + timedelta(days=o)).isoformat() for o in offsets]


def filter_ranking(rows: list[dict], lo: int, hi: int) -> list[str]:
    return [r["character_name"] for r in rows if lo <= r["ranking"] <= hi]


def page_rank_range(page: int) -> tuple[int, int]:
    return (page - 1) * 200 + 1, page * 200


def parse_combat_power(final_stat: list[dict] | None) -> int | None:
    for s in final_stat or []:
        if s.get("stat_name") == "전투력":
            try:
                return int(s["stat_value"])
            except (ValueError, TypeError, KeyError):
                return None
    return None


def classify_http_error(status: int) -> str:
    if status == 404:
        return "http_404"
    if status == 429:
        return "http_429_giveup"
    return "http_5xx_giveup"


def sample_cohort(names: list[str], cohort_name: str, n: int | None = None) -> list[str]:
    """코호트명으로 seed 분기 → 코호트 간 독립·재현 가능 (스펙 §3.2)."""
    n = SAMPLE_N if n is None else n
    rng = random.Random(f"{RANDOM_SEED}-{cohort_name}")
    return rng.sample(names, min(n, len(names)))


# 다음 실행에서 재시도할 일시적 실패 (할당량·서버·타임아웃). 이 행은 저장하지 않는다.
RETRYABLE_ERRORS = {"http_429_giveup", "http_5xx_giveup", "timeout"}


# ---- API ---------------------------------------------------------------
def _api_key() -> str:
    _load_dotenv()
    key = os.environ.get("NXOPEN_API_KEY")
    if not key:
        sys.exit("NXOPEN_API_KEY 없음 — .env 파일(.env.example 참고) 또는 환경변수로 설정하세요.")
    return key


def _load_dotenv() -> None:
    env = Path(__file__).parent / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _get(path: str, params: dict) -> dict:
    """GET + 재시도 규약 (스펙 §2). 성공: JSON dict. 실패: {"__error__": code}."""
    global _call_count
    url = f"{BASE}{path}"
    headers = {"x-nxopen-api-key": _api_key()}
    attempt = 0
    timeout_retry_left = 1
    while True:
        _call_count += 1
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        except requests.Timeout:
            time.sleep(REQ_SLEEP)
            if timeout_retry_left > 0:
                timeout_retry_left -= 1
                continue
            return {"__error__": "timeout"}
        time.sleep(REQ_SLEEP)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 404:
            return {"__error__": "http_404"}
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt < MAX_RETRY:
                time.sleep(BACKOFF[min(attempt, len(BACKOFF) - 1)])
                attempt += 1
                continue
            return {"__error__": classify_http_error(resp.status_code)}
        return {"__error__": f"http_{resp.status_code}"}


def get_ocid(name: str) -> str | None:
    if name in _ocid_cache:
        return _ocid_cache[name]
    data = _get("/id", {"character_name": name})
    ocid = None if "__error__" in data else data.get("ocid")
    _ocid_cache[name] = ocid
    return ocid


def get_basic(ocid: str, date_str: str) -> dict:
    data = _get("/character/basic", {"ocid": ocid, "date": date_str})
    if "__error__" in data:
        return {"error_code": data["__error__"]}
    return {"level": data.get("character_level"),
            "exp": data.get("character_exp"),
            "exp_rate": data.get("character_exp_rate")}


def get_combat_power(ocid: str, date_str: str) -> tuple[int | None, str | None]:
    data = _get("/character/stat", {"ocid": ocid, "date": date_str})
    if "__error__" in data:
        return None, data["__error__"]
    cp = parse_combat_power(data.get("final_stat"))
    return (cp, None) if cp is not None else (None, "stat_key_missing")


class RankingUnavailable(Exception):
    """랭킹 슬라이스를 못 받음 (보통 일 한도). 해당 코호트만 건너뛰고 다음 날 재개."""


def fetch_ranking_slice(cohort: dict) -> list[str]:
    lo, hi = page_rank_range(cohort["page"])
    data = _get("/ranking/overall",
                {"date": ANCHOR, "world_type": RANKING_WORLD_TYPE, "page": cohort["page"]})
    if "__error__" in data:
        raise RankingUnavailable(f"[{cohort['name']}] 랭킹 조회 실패: {data['__error__']}")
    names = filter_ranking(data.get("ranking", []), lo, hi)
    lvls = {r["character_level"] for r in data.get("ranking", [])}
    if not names:
        raise RankingUnavailable(f"[{cohort['name']}] 랭킹 슬라이스 0명 — page 확인")
    print(f"  랭킹 page {cohort['page']}: {len(names)}명, 레벨 {sorted(lvls)} "
          f"(목표 {cohort['target_level']})")
    return names


# ---- 수집 (행 단위 즉시 append, 재개 가능) ------------------------------
def _row(cohort, name, ocid, date_str, *, level=None, exp=None, exp_rate=None,
         combat_power=None, error_code=None) -> dict:
    return dict(cohort=cohort["name"], character_name=name, ocid=ocid, date=date_str,
               level=level, exp=exp, exp_rate=exp_rate,
               combat_power=combat_power, error_code=error_code)


def _load_done(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {(r["character_name"], r["date"]) for r in csv.DictReader(f)}


def _append_rows(path: Path, rows: list[dict]) -> None:
    new = not path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if new:
            w.writeheader()
        w.writerows(rows)


def collect_cohort(cohort: dict) -> bool:
    """수집 진행. 더 할 게 있으면(중단됨) False, 이 코호트 완료면 True."""
    out = DATA_DIR / f"cohort_{cohort['name']}.csv"
    done = _load_done(out)
    names = sample_cohort(fetch_ranking_slice(cohort), cohort["name"])
    ddates = daily_dates(ANCHOR, DAILY_DAYS)
    sdates = set(stat_dates(ANCHOR, STAT_OFFSETS))
    remaining = sum((nm, d) not in done for nm in names for d in ddates)
    print(f"  {cohort['name']}: {len(names)}명 × {len(ddates)}일, 미수집 {remaining}행")
    if remaining == 0:
        return True

    for i, nm in enumerate(names, 1):
        pending = [d for d in ddates if (nm, d) not in done]
        if not pending:
            continue
        ocid = get_ocid(nm)
        buf: list[dict] = []
        for d in pending:
            if ocid is None:
                buf.append(_row(cohort, nm, "", d, error_code="ocid_failed"))
                continue
            basic = get_basic(ocid, d)
            cp, cp_err = (None, None)
            if d in sdates and "error_code" not in basic:
                cp, cp_err = get_combat_power(ocid, d)
            buf.append(_row(cohort, nm, ocid, d,
                            level=basic.get("level"), exp=basic.get("exp"),
                            exp_rate=basic.get("exp_rate"), combat_power=cp,
                            error_code=basic.get("error_code") or cp_err))
        keep = [r for r in buf if r["error_code"] not in RETRYABLE_ERRORS]
        _append_rows(out, keep)   # 캐릭터 1명 끝날 때마다 디스크 반영 (일시 실패 행은 보류)
        gap = len(buf) - len(keep)
        print(f"  [{i:3}/{len(names)}] {nm}: +{len(keep)}행"
              f"{f' (보류 {gap})' if gap else ''}  (누적 콜 {_call_count})")
        if gap or _call_count >= DAILY_CALL_BUDGET:
            print("\n한도/일시실패 감지 — 중단. 다음 날 다시 실행하면 이어서 수집.")
            return False
    return True


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    stopped = False
    for cohort in COHORTS:
        print(f"수집: {cohort['name']} — {cohort['desc']}")
        try:
            done_ok = collect_cohort(cohort)
        except RankingUnavailable as e:
            print(f"  {e} — 이 코호트는 건너뜀 (다음 실행에서 재시도)")
            stopped = True
            break
        if not done_ok or _call_count >= DAILY_CALL_BUDGET:
            stopped = True
            break

    print(f"\n총 API 호출 수: {_call_count}")
    expected = SAMPLE_N * DAILY_DAYS
    incomplete = [c["name"] for c in COHORTS
                  if len(_load_done(DATA_DIR / f"cohort_{c['name']}.csv")) < expected * 0.98]
    if stopped or incomplete:
        print(f"미완료: {incomplete or '(한도 도달)'} — 내일 다시 `python collect.py` 실행.")
    else:
        print("모든 코호트 수집 완료.")


if __name__ == "__main__":
    main()

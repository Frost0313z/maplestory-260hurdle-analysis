"""넥슨 오픈 API로 4개 코호트 × 5체크포인트 캐릭터 스냅샷을 수집한다.

스펙: 메이플스토리_이벤트분석_스펙문서.md  §2(API·재시도), §3(구조), §4.1(CSV)
실행: NXOPEN_API_KEY 환경변수 설정 후  `python collect.py`
     끊기면 다시 실행 → 완성된 data/cohort_*.csv 는 건너뛴다.
"""
from __future__ import annotations

import os
import sys
import time
import random
from datetime import date, timedelta
from pathlib import Path

import requests
import pandas as pd

# ---- 상수 (스펙 §3.1) --------------------------------------------------------
BASE = "https://open.api.nexon.com/maplestory/v1"
REQ_SLEEP = 0.25            # 요청 간 간격. 개발 한도 5회/초 아래(초당 4회)
TIMEOUT = 10
MAX_RETRY = 3              # 429/5xx 재시도 횟수
BACKOFF = [1, 2, 4]        # 지수 백오프(초)
RANDOM_SEED = 42
SAMPLE_N = 22
DAILY_CALL_BUDGET = 1000
DATA_DIR = Path(__file__).parent / "data"

# TODO(verify): 전체 통합 랭킹 파라미터 — 첫 실행 시 1건 실호출로 확인 (스펙 §2)
RANKING_WORLD_TYPE = 0     # 0=일반 서버, 1=리부트

CHECKPOINT_OFFSETS = [1, 3, 7, 14, 30]   # D+N

COHORTS = [
    dict(name="b_event", anchor_date="2026-06-18", ranking_page=3000,
         rank_lo=599_801, rank_hi=600_000, expected_level=250),
    dict(name="b_off", anchor_date="2026-05-01", ranking_page=3000,
         rank_lo=599_548, rank_hi=599_747, expected_level=248),
    dict(name="c1", anchor_date="2026-06-18", ranking_page=300,
         rank_lo=59_801, rank_hi=60_000, expected_level=281),
    dict(name="c2", anchor_date="2026-06-18", ranking_page=10000,
         rank_lo=1_999_801, rank_hi=2_000_000, expected_level=200),
]

CSV_COLUMNS = ["cohort", "character_name", "ocid", "checkpoint", "date",
               "level", "exp", "exp_rate", "combat_power", "error_code"]

_call_count = 0   # ponytail: 모듈 전역 카운터. 단일 스레드 스크립트라 충분


# ---- 순수 헬퍼 (네트워크 없음 — test_collect.py 대상) -----------------------
def checkpoints(anchor_date: str) -> list[tuple[str, str]]:
    """앵커일 → [("D+1", "2026-06-19"), ("D+3", ...), ...]"""
    a = date.fromisoformat(anchor_date)
    return [(f"D+{n}", (a + timedelta(days=n)).isoformat()) for n in CHECKPOINT_OFFSETS]


def filter_ranking(rows: list[dict], lo: int, hi: int) -> list[str]:
    """랭킹 응답에서 lo <= ranking <= hi 인 character_name 만."""
    return [r["character_name"] for r in rows if lo <= r["ranking"] <= hi]


def parse_combat_power(final_stat: list[dict] | None) -> int | None:
    """스탯 응답의 final_stat 리스트에서 '전투력' 값(int)을 뽑는다."""
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


def sample_cohort(names: list[str], cohort_name: str) -> list[str]:
    """코호트명으로 seed 를 분기해 무작위 SAMPLE_N 명 추출 (스펙 §3.2).

    코호트별 seed 분기 → 코호트 간 표본이 서로 독립이면서 재현 가능.
    """
    rng = random.Random(f"{RANDOM_SEED}-{cohort_name}")
    return rng.sample(names, min(SAMPLE_N, len(names)))


# ---- API 호출 -------------------------------------------------------------
def _load_dotenv() -> None:
    """같은 폴더의 .env 를 os.environ 에 채운다 (이미 설정된 값은 건드리지 않음)."""
    env = Path(__file__).parent / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _api_key() -> str:
    _load_dotenv()
    key = os.environ.get("NXOPEN_API_KEY")
    if not key:
        sys.exit("NXOPEN_API_KEY 없음 — .env 파일(.env.example 참고) 또는 환경변수로 설정하세요.")
    return key


def _get(path: str, params: dict) -> dict:
    """GET + 재시도 규약 (스펙 §2).

    성공: 응답 JSON(dict). 실패: {"__error__": <code>}.
    - 429 / 5xx  : 1→2→4초 백오프로 최대 MAX_RETRY 회, 이후 give up
    - 404        : 즉시 포기
    - Timeout    : 1회 재시도 후 포기
    """
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
        return {"__error__": f"http_{resp.status_code}"}   # 기타 4xx: 재시도 무의미


def get_ocid(name: str) -> str | None:
    data = _get("/id", {"character_name": name})
    return None if "__error__" in data else data.get("ocid")


def get_basic(ocid: str, date_str: str) -> dict:
    """→ {"level","exp","exp_rate"} 또는 {"error_code": ...}"""
    data = _get("/character/basic", {"ocid": ocid, "date": date_str})
    if "__error__" in data:
        return {"error_code": data["__error__"]}
    return {"level": data.get("character_level"),
            "exp": data.get("character_exp"),
            "exp_rate": data.get("character_exp_rate")}


def get_combat_power(ocid: str, date_str: str) -> tuple[int | None, str | None]:
    """→ (전투력, error_code). 성공 시 (int, None), 실패 시 (None, code)."""
    data = _get("/character/stat", {"ocid": ocid, "date": date_str})
    if "__error__" in data:
        return None, data["__error__"]
    cp = parse_combat_power(data.get("final_stat"))
    return (cp, None) if cp is not None else (None, "stat_key_missing")


def fetch_ranking_slice(cohort: dict) -> list[str]:
    """앵커일 랭킹 page 1콜 → rank_lo~rank_hi 구간의 캐릭터명 리스트."""
    data = _get("/ranking/overall", {
        "date": cohort["anchor_date"],
        "world_type": RANKING_WORLD_TYPE,
        "page": cohort["ranking_page"],
    })
    if "__error__" in data:
        sys.exit(f"[{cohort['name']}] 랭킹 조회 실패: {data['__error__']}")
    names = filter_ranking(data.get("ranking", []), cohort["rank_lo"], cohort["rank_hi"])
    if not names:
        sys.exit(f"[{cohort['name']}] 랭킹 슬라이스 0명 — page/구간/날짜 확인")
    return names


# ---- 수집 --------------------------------------------------------------
def _row(cohort: dict, name: str, ocid: str, checkpoint: str, date_str: str, *,
         level=None, exp=None, exp_rate=None, combat_power=None, error_code=None) -> dict:
    return dict(cohort=cohort["name"], character_name=name, ocid=ocid,
               checkpoint=checkpoint, date=date_str, level=level, exp=exp,
               exp_rate=exp_rate, combat_power=combat_power, error_code=error_code)


def collect_cohort(cohort: dict) -> pd.DataFrame:
    """22명 × 5체크포인트. 각 시점 basic + stat 2콜. long-format DataFrame."""
    names = sample_cohort(fetch_ranking_slice(cohort), cohort["name"])
    cps = checkpoints(cohort["anchor_date"])
    rows: list[dict] = []
    for i, nm in enumerate(names, 1):
        ocid = get_ocid(nm)
        if ocid is None:
            rows += [_row(cohort, nm, "", label, d, error_code="ocid_failed")
                     for label, d in cps]
            print(f"  [{i:2}/{len(names)}] {nm}: ocid 실패")
            continue
        for label, d in cps:
            basic = get_basic(ocid, d)
            cp, cp_err = get_combat_power(ocid, d)
            rows.append(_row(cohort, nm, ocid, label, d,
                             level=basic.get("level"), exp=basic.get("exp"),
                             exp_rate=basic.get("exp_rate"), combat_power=cp,
                             error_code=basic.get("error_code") or cp_err))
        print(f"  [{i:2}/{len(names)}] {nm}: ok")
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    for cohort in COHORTS:
        out = DATA_DIR / f"cohort_{cohort['name']}.csv"
        if out.exists():
            print(f"skip {out.name} (이미 존재)")
            continue
        print(f"수집: {cohort['name']} (anchor {cohort['anchor_date']})")
        df = collect_cohort(cohort)
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print(f"  → {out.name}: {len(df)}행, 실패 {df['error_code'].notna().sum()}행")
    print(f"\n총 API 호출 수: {_call_count}")
    if _call_count > DAILY_CALL_BUDGET:
        print(f"경고: 개발단계 일 한도 {DAILY_CALL_BUDGET} 초과 — 다음 날 이어서 실행")


if __name__ == "__main__":
    main()

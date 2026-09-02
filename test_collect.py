"""collect.py 순수 헬퍼 자체 점검 — 네트워크·API 키 불필요.

실행:  python test_collect.py
"""
import collect


def test_daily_dates():
    ds = collect.daily_dates("2026-06-18", 25)
    assert len(ds) == 25
    assert ds[0] == "2026-06-18"
    assert ds[1] == "2026-06-19"
    assert ds[-1] == "2026-07-12"


def test_stat_dates():
    assert collect.stat_dates("2026-06-18", [0, 8, 16, 24]) == [
        "2026-06-18", "2026-06-26", "2026-07-04", "2026-07-12"]


def test_page_rank_range():
    assert collect.page_rank_range(1) == (1, 200)
    assert collect.page_rank_range(3000) == (599_801, 600_000)
    assert collect.page_rank_range(15000) == (2_999_801, 3_000_000)


def test_filter_ranking():
    rows = [{"ranking": r, "character_name": f"c{r}"} for r in range(595, 605)]
    assert collect.filter_ranking(rows, 599, 601) == ["c599", "c600", "c601"]
    assert collect.filter_ranking(rows, 700, 800) == []


def test_parse_combat_power():
    fs = [{"stat_name": "STR", "stat_value": "999"},
          {"stat_name": "전투력", "stat_value": "12345678"}]
    assert collect.parse_combat_power(fs) == 12345678
    assert collect.parse_combat_power([]) is None
    assert collect.parse_combat_power(None) is None
    assert collect.parse_combat_power([{"stat_name": "전투력", "stat_value": None}]) is None


def test_classify_http_error():
    assert collect.classify_http_error(404) == "http_404"
    assert collect.classify_http_error(429) == "http_429_giveup"
    assert collect.classify_http_error(503) == "http_5xx_giveup"


def test_sample_cohort_deterministic_and_independent():
    names = [f"user{i}" for i in range(1000)]
    a = collect.sample_cohort(names, "at260", n=300)
    assert a == collect.sample_cohort(names, "at260", n=300)     # 재현 가능
    assert a != collect.sample_cohort(names, "approach", n=300)  # 코호트 간 독립
    assert len(a) == 300
    assert set(a).issubset(names)
    assert len(set(a)) == len(a)                                 # 중복 없음


def test_sample_cohort_prefix_stable():
    """n 을 키워도 앞 n 명은 그대로 → 증분 수집 가능."""
    names = [f"user{i}" for i in range(1000)]
    small = collect.sample_cohort(names, "at260", n=100)
    big = collect.sample_cohort(names, "at260", n=300)
    assert big[:100] == small


def test_sample_cohort_dedup_and_small_pool():
    assert len(collect.sample_cohort(["a", "b", "a"], "x", n=10)) == 2   # 중복 제거


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")

"""collect.py 순수 헬퍼 자체 점검 — 네트워크·API 키 불필요.

실행:  python test_collect.py
"""
import collect


def test_checkpoints():
    cps = collect.checkpoints("2026-06-18")
    assert [c[0] for c in cps] == ["D+1", "D+3", "D+7", "D+14", "D+30"]
    assert cps[0][1] == "2026-06-19"
    assert cps[-1][1] == "2026-07-18"


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
    names = [f"user{i}" for i in range(200)]
    a = collect.sample_cohort(names, "b_event")
    assert a == collect.sample_cohort(names, "b_event")   # 재현 가능
    assert a != collect.sample_cohort(names, "c2")        # 코호트 간 독립
    assert len(a) == collect.SAMPLE_N
    assert set(a).issubset(names)                          # 부분집합
    assert len(set(a)) == len(a)                           # 중복 없음


def test_sample_cohort_small_pool():
    assert len(collect.sample_cohort(["a", "b"], "x")) == 2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")

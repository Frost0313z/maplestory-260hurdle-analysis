# Burstiness Robustness Check

작성: 2026-09-04 · API 호출 **0** · 입력: `data/panel_basic.csv`, `data/pilot_targets.csv`
코드: `analysis/burstiness_robustness.py` · 수치: `data/burstiness_robustness_summary.csv`
선행: `docs/retrospective_eda_findings.md`

**질문**: `burst_ratio = maxΔ/totalΔ` 하나에서만 Parker/Persistent 차이가 나는가, 아니면
대체 산식·최소 성장 필터·cohort 내부에서도 유지되는가. 그리고 그 차이가 **label 규칙의
재표현(circular)인가 독립 신호인가.**

표본: `Seasonal_Parker` n=49, `Persistent_cand` n=61. 레벨은 단조 비감소 → interval Δ ≥ 0,
음수 구간 없음. `total_growth == 0` 인 캐릭터: 양 그룹 0명 (지표 None 처리 규칙만 명시).

---

## §1 대체 concentration 산식 — 5개 전부 같은 방향

median, 전체:

| 산식 | Parker | Persistent | 방향 |
|---|---|---|---|
| `top1_share` (maxΔ/total) | **1.00** | 0.50 | Parker 집중 |
| `top2_share` (top2합/total) | 1.00 | 0.815 | Parker 집중 |
| `hhi` (Σ(Δi/total)²) | **1.00** | 0.382 | Parker 집중 |
| `conc_entropy` (1 − H/ln5) | 1.00 | 0.359 | Parker 집중 |
| `gap12` (maxΔ − 2ndΔ, 절대) | 5 | 4 | ~동률 (정규화 안 됨) |

→ **정규화된 집중도 산식 5개 중 4개가 동일 방향·큰 격차.** `gap12`(절대 격차)만 분리 실패 —
정규화 안 하면 신호가 사라진다는 뜻.

## §2 최소 성장량 필터 — 작은 total 이 원인이 아님

| 필터 | Parker n | Persistent n | Parker top1 | Persistent top1 | Parker hhi | Persistent hhi |
|---|---|---|---|---|---|---|
| total ≥ 0 | 49 | 61 | 1.00 | 0.50 | 1.00 | 0.382 |
| total ≥ 5 | 41 | 61 | 1.00 | 0.50 | 1.00 | 0.382 |
| total ≥ 10 | 24 | 56 | 1.00 | 0.50 | 1.00 | 0.405 |
| total ≥ 20 | 14 | 43 | 1.00 | 0.556 | 1.00 | 0.436 |

- total ≥ 10 에서 두 그룹 median total_growth 가 32 vs 31 로 **거의 같아져도** 집중도 격차 유지.
- total ≥ 20 (14명) 인 Parker 도 `top1_share` = 1.00 — **20~116 레벨을 단일 구간에서 올리고
  나머지 1년간 평탄한 캐릭터가 14명.**
- → "작은 total 이 concentration 을 기계적으로 올린다" 는 아티팩트는 **기각.** 지표는 안정적.

## §3 cohort 내부 — 방향 유지, burnend 는 격차 축소

| cohort | Parker n | Pers n | Parker ev/btw/top1/hhi | Persistent ev/btw/top1/hhi |
|---|---|---|---|---|
| at260 | 26 | 19 | 10 / 0 / 1.00 / 1.00 | 2 / 27 / 0.50 / 0.442 |
| **burnend** | **12** | **13** | **4.5 / 1 / 0.775 / 0.653** | **5 / 7 / 0.375 / 0.281** |
| climb | 3 | 27 | (n=3) 7 / 0 / 0.991 | 5 / 33 / 0.558 / 0.412 |
| past260 | 8 | 2 | 13 / 0.5 / 0.97 | (n=2) 20.5 / 15.5 / 0.508 |

- **burnend (n=12/13, 매칭 최상)**: `event_growth` 4.5 ≈ 5 로 **동일**한데 `top1_share` 0.775 vs
  0.375, `between_growth` 1 vs 7. 이벤트 기간 성장이 같아도 궤적 shape 이 갈린다.
- burnend Parker `top1_share` 는 0.775 (1.0 아님) — "한 시즌 몰빵" 은 저레벨 cohort(at260/climb)
  에서 가장 날카롭고 burnend 에서는 무뎌진다.

## §3b circularity 정량화 — **이게 핵심**

label 규칙: Persistent = `Δ≥2 구간 수 ≥ 3`, Parker = `BETWEEN 3구간 Δ≤1` → `n_active_ge2` 가
**정의상 완전 분리** (Persistent ≥ 3, Parker ≤ 2, 겹침 0).

| 그룹 | n_active_ge2 | cnt | top1 med | hhi med | conc_entropy med |
|---|---|---|---|---|---|
| Parker | 1 | 43 | 1.00 | 1.00 | 1.00 |
| Parker | 2 | 6 | 0.662 | 0.504 | 0.472 |
| Persistent | 3 | 41 | 0.545 | 0.436 | 0.416 |
| Persistent | 4 | 15 | 0.387 | 0.297 | 0.191 |
| Persistent | 5 | 5 | 0.333 | 0.235 | 0.052 |

- **`top1_share` 는 `n_active_ge2` 의 거의 결정적 함수** (활성 구간 1개 → 1.0, 5개 → 0.33).
- `n_active_ge2` 가 이미 두 그룹을 **완전 분리**하고, 모든 concentration 지표는 그 단조함수다.
- **→ 이 라벨 집합에서 concentration 은 label 규칙 대비 "추가 분리력" 을 주지 않는다.
  circular.** 경계에서도 (Parker n=2 → top1 0.66) vs (Persistent n=3 → top1 0.55) 로 가까워,
  지표 자체가 아니라 규칙의 `≥3` 컷이 분리한다.

## §4 matched pairs (같은 cohort + eventΔ ±3 + startLv ±8, 10쌍)

10쌍 모두 동일 패턴 — Persistent 는 3~4구간 분산(btwΔ 4~10), Parker 는 1구간(대개 seg0), btwΔ 0~2.
**이는 label 정의가 그대로 나타난 것** (Parker: BETWEEN Δ≤1, Persistent: BETWEEN Δ≥2 하나 이상).

정의로 설명 안 되는 관측 = **같은 event 성장에서 total 성장이 2배 차이**:

| 쌍 | cohort | eventΔ (P=K) | Persistent totΔ | Parker totΔ |
|---|---|---|---|---|
| 4 | at260 | 5 | 10 | 5 |
| 5 | climb | 5 | 10 | 5 |
| 7 | burnend | 4 | 11 | 4 |
| 10 | burnend | 2~3 | 12 | 3 |

→ **event-window ΔLevel 은 캐릭터의 15개월 total 성장을 거의 예측하지 못한다** (같은 event 성장,
total 은 2~4배 차이). 추가분은 전부 시즌 사이 구간에서 옴.

---

## descriptive signature vs candidate leading indicator

| 구분 | 항목 | 상태 |
|---|---|---|
| **Historical descriptive signature** (이 라벨 집합, 부분 circular) | growth concentration (top1_share / hhi / conc_entropy), `n_active_ge2`, between-season 성장 존재 여부 | label 생성 규칙에 일부 포함. 독립 predictive feature 로 부르지 않음 |
| **Candidate leading indicator** (Phase B prospective outcome 으로 검증) | ① OVERDRIVE-창 + post-event 궤적의 concentration (level 아닌 **HEXA/Symbol/CP**) | 미검증 |
| | ② `ΔLevel_event` 를 **null/음(−)** 예측자로 (양의 예측력 없음 가설) | 미검증 |
| | ③ pre-OVERDRIVE 시점의 historical between-season 성장 **크기**(연속값) | 미검증 |
| | ④ 260 도달 timing + 도달 시 exp_rate (climb case, n=5 가설) | 미검증 |

concentration 산식은 5개가 서로 일치하므로, ①이 Phase B 에서 유효하다면 **산식 선택은 취약점이
아니다** — 단 그건 라벨에 대한 발견이 아니라 Phase B 를 위한 robustness 확인이다.

---

## H1 / H2 / H3 평가 (현재 데이터 기준)

### H1. 이벤트 기간 성장량이 클수록 장기 progression 가능성이 높다 → **Not Supported**

- Parker `event_growth` median 9 > Persistent 5 (mean 19.8 vs 7.8).
- matched pairs: event 성장 같을 때 Persistent total 이 2~4배 (§4).
- burnend 내부: event_growth 4.5 ≈ 5 로 동일한데 두 그룹이 갈림 (§3).
- → 이벤트 기간 성장량은 "여러 시즌 progression" 라벨과 양의 관계가 없고, 오히려 큰 단일 이벤트
  성장은 Parker 쪽에 몰린다. (한계: "장기 progression 가능성" 은 provisional label 로 대리한 것,
  prospective outcome 아님.)

### H2. 성장량이 특정 시즌에 집중될수록 Seasonal Parker → **Partially Supported (대부분 circular)**

- 5개 concentration 산식 전부 같은 방향, 최소 성장 필터·cohort 내부에서도 유지 (§1·§2·§3) →
  **descriptive signature 로는 견고.**
- 그러나 `n_active_ge2` 가 label 정의상 두 그룹을 완전 분리하고 모든 concentration 지표가 그
  단조함수 (§3b) → **이 라벨 집합에서는 규칙의 재표현.** label 을 넘어선 독립 discriminator 인지
  여기서 판정 불가.
- "Partially" = 신호가 formula-robust 하고 방향이 일관되나, circularity 때문에 독립성 미확인.

### H3. 여러 시즌/비이벤트 구간에서 반복 progression 한 캐릭터는 **향후에도** progression 유지 → **검증 불가 (Cannot be evaluated)**

- 앞부분("여러 시즌 반복 progression")은 `Persistent_cand` 정의 자체 → circular.
- 뒷부분("향후에도 유지")은 **2026-09-16 이후 prospective outcome 이 필요**한데 아직 없음
  (Phase B 미수집).
- → H3 는 Phase B outcome 수집 전까지 어느 방향으로도 평가하지 않는다.

---

## 한계

- 세 가설 모두 provisional label 로 정의된 두 그룹의 **pre-outcome 기술통계**. label 이 level
  trajectory 로만 생성되어 concentration·breadth 와 구조적으로 얽혀 있음.
- HEXA/Symbol/CP 미반영 → Low-intensity Persistent 는 이 분석에 안 잡힘.
- cohort 내부 n: at260 26/19, burnend 12/13 외에는 한쪽 ≤ 3 → 유의성 주장 안 함.
- 진짜 leading indicator 여부는 Phase B(2026-09-16 이후) post-event outcome 으로만 판정.

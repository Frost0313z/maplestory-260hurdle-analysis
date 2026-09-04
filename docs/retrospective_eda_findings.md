# Retrospective EDA — Parker vs Persistent (provisional label) + climb 260 case study

작성: 2026-09-04 · API 호출 **0** · 입력: `data/panel_basic.csv`, `data/pilot_targets.csv`, `data/cohort_climb.csv`
코드: `analysis/retrospective_eda.py` · 수치: `data/retrospective_eda_summary.csv`

**목적**: provisional label 을 증명하는 게 아니라, **Phase B 에서 검증할 leading indicator 후보를 좁힌다.**
표본: `Seasonal_Parker` n=49, `Persistent_cand` n=61 (전부 lv(2026-06-12) ≥ 255).

> ⚠️ 인과 표현 금지. Parker/Persistent 는 sampling 용 provisional label 이며 outcome 이 아니다.

---

## 0. Label 규칙과 leakage 경계

`build_pilot_sample.classify()` (6 milestone, seg0..4 = 인접 간 Δlevel, EVENT={0,4}=ASSEMBLE/OVERDRIVE):

- **Persistent_cand** = (Δ≥2 인 구간 수) ≥ 3 **&** 그중 ≥1개가 시즌 사이(BETWEEN={1,2,3}) **&** lv≥255
- **Seasonal_Parker** = EVENT 구간 중 Δ≥3 하나 이상 **&** BETWEEN 3구간 모두 Δ≤1 **&** lv≥255

**Definition-implied (규칙상 당연 — 새 발견 아님)**
- Persistent 의 `n_active_ge2 ≥ 3`, `between_growth > 0`
- Parker 의 `between_growth ≈ 0` (구간당 ≤1 × 3), `n_active_ge2 ≤ 2`, EVENT 구간에 Δ≥3 존재
- `n_flat` 차이 (위의 여집합)

**Additional observed (규칙에 없음 — 볼 가치 있음)**
- event-period 성장의 **크기** (Parker vs Persistent)
- `burst_ratio` = max_interval_growth / total_growth 의 **정도**
- `std_interval`, `total_growth`, `start_level`
- 성장이 몰린 **시즌** (seg0 vs seg2/3 vs seg4)
- 같은 event_growth 에서 두 그룹이 **공존**하는지 (matched)
- Persistent 의 between 성장이 **임계 부근(Δ2~3)인지 실질적(Δ10+)인지**

---

## 1. 전체 비교 (median)

| metric | Parker n=49 | Persistent n=61 | 분류 |
|---|---|---|---|
| start_level | **255** | **230** | additional |
| total_growth (15개월 net) | 9 | **30** | additional |
| **event_growth (seg0+seg4)** | **9** | **5** | **additional** |
| between_growth (seg1+2+3) | 0 | 22 | 방향=implied / **크기=additional** |
| max_interval_growth | 6 | 15 | additional |
| **burst_ratio (max/total)** | **1.00** (IQR 0.83–1.0) | **0.50** (IQR 0.40–0.60) | 방향 일부 implied / **정도=additional** |
| std_interval | 2.33 | **5.53** | additional (예상과 반대) |
| n_active_ge2 | 1 | 3 | **definition-implied** |
| n_flat | 4 | 1 | **definition-implied** |

### 최대 성장 구간 (max_interval_seg) — additional

- **Parker**: seg0 ASSEMBLE(2025여름) 41/49, seg4 OVERDRIVE(2026여름) 8/49 → 거의 전부 **한 번의 여름 버스트**
- **Persistent**: seg3 CROWN말 21, seg0 14, seg2 14, seg1 10, seg4 2 → **분산**, 최대 구간이 겨울(CROWN)인 경우가 많음
- **두 그룹 모두 seg4(현재 OVERDRIVE)에서 최대 성장한 경우는 드묾** (합쳐 10/110)

---

## 2. 핵심 결과별 Observed / Interpretation / Limitation / Hypothesis

### 결과 A — 이벤트 기간 성장 크기: Parker > Persistent

- **Observed Fact**: `event_growth` median Parker 9 vs Persistent 5 (mean 19.8 vs 7.8, max 116 vs 48).
  버킷별로도(§3) 21+ 대형 성장 구간은 Parker 13명 / Persistent 7명.
- **Interpretation**: "이벤트 기간에 가장 크게 성장한 캐릭터"와 "여러 시즌 progression 을 유지한
  캐릭터"는 겹치지 않는 경향. 큰 단일 이벤트 ΔLevel 은 오히려 이후 정체(Parker)와 함께 관측됨.
- **Limitation**: Parker 의 `start_level`(255)이 Persistent(230)보다 높아 시작 지점이 다름.
  Parker 의 큰 event_growth 에는 한 ASSEMBLE 창에서 200→260+ 를 태운 사례가 섞임. outcome
  (이벤트 종료 후 지속 여부)은 아직 미관측 — Parker 가 실제로 이탈했는지 확인 안 됨.
- **Hypothesis for Phase B**: `ΔLevel_event` 의 절대 크기는 post-event progression 의 **양(+) 신호가
  아니다**. 오히려 크기가 클수록 post-event Δ(level/HEXA/Symbol/CP)가 낮을 수 있다 → Phase B 에서
  `ΔLevel_OVERDRIVE` 와 `post-event Δ` 의 관계 부호를 확인.

### 결과 B — 성장 집중도(burst_ratio): Parker ≈ 1.0, Persistent ≈ 0.5

- **Observed Fact**: Parker 의 성장은 단일 구간에 거의 100% 집중(median 1.00, IQR 0.83–1.0).
  Persistent 는 최대 구간이 전체의 절반(median 0.50, IQR 0.40–0.60).
- **Interpretation**: Parker = 한 시즌 몰빵형, Persistent = 여러 구간 분산형. 집중도(1 − breadth)가
  두 그룹을 가르는 축.
- **Limitation**: Persistent 정의가 "Δ≥2 구간 ≥3" 이므로 burst_ratio < 1 은 **부분적으로 규칙 강제**.
  단 정확한 값(0.5 근처, 좁은 IQR)과 Parker 의 1.0 쏠림은 규칙이 지정하지 않음.
- **Hypothesis for Phase B**: OVERDRIVE 기간 + post-event 구간에서 progression 이 **한 시점에
  집중되는지 여러 시점에 분산되는지**(level 뿐 아니라 HEXA/Symbol/CP 각각)가 post-event 지속의
  후보 신호. burst_ratio 를 Phase B trajectory(09-15/+7/+14/+28)에 재적용해 검증.

### 결과 C — matched (같은 event_growth 에서도 갈리는가)

- **Observed Fact** (§3 표): event_growth 2–3 / 4–6 / 7–10 / 11–20 / 21+ **모든 버킷에 Parker·
  Persistent 가 공존**. 같은 버킷에서 Parker `between_growth` median = **0 (전 버킷)**,
  Persistent = 10 ~ 34. Parker `burst_ratio` 0.86–1.0, Persistent 0.35–0.68.
  또한 event_growth **0–1 버킷에 Persistent 7명** (이벤트 창에서 전혀 안 컸는데 시즌 사이
  total median 27 성장) — Parker 는 이 버킷에 존재 불가(규칙).
- **Interpretation**: event-period 성장량만으로는 두 패턴을 구분하지 못한다. 구분은 **시즌 사이
  성장 유무·크기**에서 온다.
- **Limitation**: "Parker between=0 vs Persistent between>0" 라는 **방향 자체는 label 정의가 강제**
  (Parker: BETWEEN Δ≤1, Persistent: BETWEEN Δ≥2 하나 이상). 이 §의 additional 부분은 (1) 두
  그룹이 모든 event_growth 버킷에 공존한다는 사실, (2) Persistent 의 between 크기가 임계(2~3)가
  아니라 median 10–34 로 **실질적**이라는 점.
- **Hypothesis for Phase B**: pre-OVERDRIVE feature 로 "직전 비이벤트 구간(seg1~3)에서 성장했는가 +
  얼마나"(panel_basic 로 이미 계산 가능)를 넣고, post-event progression 과의 관계를 확인.

### 결과 D — cohort 내부 (confounding 통제)

- **Observed Fact**:
  - `at260`: Parker n=26 (event 10 / between 0 / burst 1.0) vs Persistent n=19 (event 2 / between 27 / burst 0.5) — 큰 대비.
  - `burnend`: Parker n=12 (event **4.5** / between 1 / burst 0.78) vs Persistent n=13 (event **5.0** / between 7 / burst 0.38) — **event_growth 사실상 동일**, burst·between 만 다름.
  - `climb`: Parker n=3(결론 불가) vs Persistent n=27 (event 5 / between 33 / burst 0.56).
  - `past260`: n=8 / 2 (결론 불가).
- **Interpretation**: `burnend`(n=12/13, 매칭 양호)에서 두 그룹의 이벤트 기간 성장이 같아도
  집중도·시즌 사이 성장이 갈린다 → 결과 A(event 크기)는 cohort 교란 가능성이 있고, 결과 B/C
  (집중도·breadth)가 cohort 내부에서도 유지된다.
- **Limitation**: cohort 별 n 이 작음(최대 26). `climb`·`past260` 는 한쪽 그룹 n≤3 이라 비교 불가.
- **Hypothesis for Phase B**: leading indicator 검증은 cohort 를 통제 변수로 넣고, **집중도/breadth**
  를 우선 후보로. event 크기는 cohort 교란 의심이라 단독 후보로 올리지 않음.

### 결과 E — climb 260 case study (n=49 vs n=5, hypothesis 전용)

- **Observed Fact**:

  | | final_260 (n=49) | reach_261+ (n=5) |
  |---|---|---|
  | first_260 도달 offset (median) | D+23 | D+15 |
  | 260 도달 시 exp_rate (median) | 1.15% | **46.2%** |
  | 260 이후 관측 가능 일수 (median) | 11 | 19 |
  | final exp_rate (median) | 1.81% | 17.0% |
  | CP Δ (5 snapshot, median) | −3,307 (≈0, 범위 ±5.3M) | +197,854 (범위 −0.2M ~ +10.9M) |

  개별 261+ 5건: 3건은 260 도달 시 exp_rate 46–67%(경계를 "여세로" 통과), 2건은 낮은 exp_rate
  이지만 관측일 19/6일 확보. 최대 CP 증가(+10.9M)는 D+3 도달 → Lv265 사례.
- **Interpretation**: 261 로 넘어간 소수는 (a) 260 에 **더 일찍** 도달해 관측 창이 길고, (b) 260
  도달 시점에 이미 레벨 내 진행도가 높아(momentum) 경계에서 멈추기보다 통과, (c) CP 가 (+) 방향.
  final_260 는 도달 시·관측 종료 시 모두 exp_rate ≈ 1–2%, CP ≈ 무변동.
- **Limitation**: **n=5. 통계적 결론 절대 불가.** final_260 의 exp_rate_at_260 범위도 0–56.7 로
  일부는 높음. CP 는 8일 간격 5 snapshot 뿐이라 리롤/장비 해제 노이즈 큼(범위 ±5M).
- **Hypothesis for Phase B**: OVERDRIVE 기간 260 도달 캐릭터에 대해 **도달 timing** 과 **도달 시
  exp_rate(레벨 내 momentum)** 가 post-event level·investment 성장의 후보 신호. (Phase B 는
  09-15 스냅샷 + daily(Part1) 로 도달일·exp_rate 확보 가능.)

---

## 3. 예상 밖 결과 (요약)

1. **Persistent 의 interval-Δ 분산이 Parker보다 크다** (std 5.53 vs 2.33). "Persistent = 완만·꾸준"
   이라는 그림은 틀림. 큰 스윙이 여러 번 있는 형태. **분산(std)이 아니라 집중도(burst_ratio)가
   두 그룹을 가른다** → Phase B 에서 "low variance = persistent" 지표는 만들지 않는다.
2. **가장 크게 이벤트 버스트한 캐릭터가 Parker** (event_growth 9 vs 5). 사용자 가설
   "peak event growth ≠ long-term progression" 과 방향이 일치.
3. **burnend 내부에서는 event_growth 가 동일**(4.5 vs 5). cohort 를 고정하면 이벤트 크기의
   변별력이 사라지고 집중도·breadth 만 남음.
4. **event_growth 0–1 인 Persistent 7명** — 두 이벤트 창에서 레벨을 전혀 안 올렸는데 시즌 사이
   총 27레벨(median) 성장. "성장이 이벤트 밖에서만 일어나는" 인구가 실재.
5. **두 그룹 모두 현재 OVERDRIVE(seg4)에서 최대 성장한 경우가 거의 없음** (10/110). Phase B 의
   OVERDRIVE-창 ΔLevel 은 대부분 작을 것 → level 이 아니라 HEXA/Symbol/CP 궤적에 burst/breadth
   지표를 적용해야 함.

---

## 4. Phase B leading indicator 후보 (관측된 차이가 있는 것만, 우선순위)

| 순위 | 후보 | 근거 (관측) | Phase B 검증 방법 |
|---|---|---|---|
| **1** | **growth concentration / burstiness** — `max_Δ / total_Δ` 를 level + HEXA + Symbol + CP 각각에 | Parker burst 1.0 vs Persistent 0.5, burnend 내부에서도 유지(0.78 vs 0.38), std 로는 안 갈림 | 09-15/+7/+14/+28 trajectory 로 endpoint별 burst_ratio 계산, post-event Δ 지속과의 관계 |
| **2** | **historical growth breadth** — 직전 비이벤트 구간(seg1~3) 성장 여부·크기 (panel_basic, 계산 완료) | Persistent between median 22 (임계 아님), event_growth 0–1 Persistent 7명 | pre-OVERDRIVE feature 로 고정, post-event progression 과 부호 확인. 방향은 label-implied 이므로 **연속 크기**로만 사용 |
| **3** | **event-period growth magnitude as NULL/negative signal** — `ΔLevel_OVERDRIVE` | Parker event_growth > Persistent (9 vs 5), 단 cohort 교란 의심(burnend 에서 동일) | cohort 통제 후 `ΔLevel_event` ↔ `post-event Δ` 부호. **양의 예측력 없음** 가설을 반증하는 형태로 |
| **4** | **260 arrival timing + arrival exp_rate (momentum)** — OVERDRIVE 260 도달자 한정 | climb case: 261+ 는 도달 D+15 / exp_rate 46% vs final_260 D+23 / 1.15% (n=5, 가설만) | Phase B daily + 09-15 로 도달일·도달 시 exp_rate 계산, post-event level/HEXA/Symbol Δ 와 대조 |
| — (보류) | start_level / burn lifecycle 위치 | Parker 255 vs Persistent 230 | cohort 와 공선 의심 → 통제 변수로만, 단독 후보 아님 |
| — (제외) | interval-Δ 표준편차, `n_active` 원 카운트, `between>0` 이진 | std 는 방향 반대, 나머지는 label 정의 그대로 | 사용 안 함 |

---

## 5. 한계 (공통)

- provisional label 은 2025-06 ~ 2026-06 **레벨 궤적만**으로 정의됨. HEXA/Symbol/CP 미반영 →
  Low-intensity Persistent(레벨 정체 + 자원 투자 지속)는 현재 Persistent_cand 에 안 잡힘.
- outcome(2026-09-16 이후 progression)은 **아직 미관측**. 위 결과는 전부 pre-outcome 기술통계.
- Parker/Persistent 는 각각 pool 49 전량 / 61 전량이라 표본 확장 불가. cohort-stratified n 은 최대 26.
- climb case study n=5 → hypothesis generation 전용, 어떤 비율·유의성도 주장하지 않음.
- 레벨은 EXP 쿠폰 지급으로 오염 → event-window ΔLevel 자체가 "자발적 grind" 를 뜻하지 않음.

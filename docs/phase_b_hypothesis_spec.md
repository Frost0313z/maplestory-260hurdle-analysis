# Phase B — Leading Indicator Hypothesis Spec

작성: 2026-09-04 · 선행: `docs/retrospective_eda_findings.md`, `docs/burstiness_robustness.md`
상태: **수집 전 spec.** Phase B(2026-09-16 이후) 데이터로 검증. API 호출 없음.

---

## 0. Retrospective 1차 결론 (고정)

| 가설 | 결론 |
|---|---|
| **H1** 이벤트 기간 성장량이 클수록 장기 progression 가능성이 높다 | **Not Supported** — Parker(event_growth median 9) > Persistent(5), matched pair 에서 같은 event 성장에 total 2~4배, burnend 내부 동일 |
| **H2** 성장이 특정 시즌에 집중될수록 Seasonal Parker | **Descriptive signature 이나 circularity 로 독립 예측력 미확인** — concentration 산식 5개 방향 일치·필터/cohort robust 하나, `n_active_ge2` 가 label 정의상 두 그룹 완전 분리, 모든 concentration 지표가 그 단조함수 |
| **H3** 여러 시즌/비이벤트 구간 반복 progression → **향후에도** 유지 | **Prospective outcome 전까지 검증 불가** — 앞부분은 `Persistent_cand` 정의 자체(circular), "향후에도" 는 Phase B outcome 필요 |

→ retrospective level-only 분석은 여기서 종료. **concentration/burstiness 는 historical descriptive
signature 로만 보존하고 predictive feature 로 확정하지 않는다.** (Phase B trajectory 에 재적용해
*후보* 로만 검증 — 아래 C1.)

---

## 1. Outcome 정의 (provisional, operational)

Open API 로 로그인/접속 미관측 → "retained user" 대신 **post-event progression retained** 를 쓴다.
"post-event" = **major burning 지원(OVERDRIVE HB MAX + BEYOND, 2026-09-16) 종료 이후** 이며
pure voluntary 가 아니다 (평시 이벤트샵·Sunday Maple·보유 재화 존재).

관측 창: `T0 = 2026-09-15`(종료 직전), 이후 `+7 / +14 / +28`(Wave 1), `+56`(Wave 2).
4축 (frame locked): **Level** = grind/time · **HEXA** = character resource investment(거래 가능 →
접속 아님) · **Symbol** = 장기/일일형 progression 참여 proxy · **CP** = 전환 결과. **Union** = 계정 context.

축별 변수 (모든 threshold 는 분포 확인 후 결정 — 여기서 고정 안 함):

| 기호 | 정의 |
|---|---|
| `X_pre` | X at 2026-06-12 (OVERDRIVE 직전 baseline) |
| `dX_event` | X(T0) − X_pre |
| `dX_post_early` | X(+28) − X(T0) |
| `dX_post_full` | X(+56) − X(T0) |
| `n_post_intervals_moved` | {T0→+7, +7→+14, +14→+28, +28→+56} 중 ΔX > min_meaningful_change 인 구간 수 |
| `post_slope` | X 의 T0/+7/+14/+28/+56 5점 OLS 기울기 |
| `persistence_ratio` | `dX_post_full` / max(`dX_event`, ε) |

- `X_HEXA` = `total_core_level` (Σ hexa_core_level, **hexa_core_name key 기반 diff**; `active_core_count` 은 장착 변동으로 노이즈라 사용 안 함)
- `X_Symbol` = 심볼 레벨 합 (아케인+어센틱)
- `X_CP` = 전투력. reroll/장비 해제로 음수 스파이크 → winsorize 또는 `note` 플래그, 원값 보존
- `X_Level` = 캐릭터 레벨

**Outcome 후보**
- **O1 (composite)** — post-event progression retained: `n_post_intervals_moved ≥ 2` **또는** `post_slope > 0` 를 {HEXA, Symbol, CP} 중 ≥1축에서 충족. (단일 transient bump 배제 목적)
- **O2 (axis-specific 연속)** — `dX_post_full` 각각 (HEXA / Symbol / CP / Level)
- **O3 (persistence ratio)** — 축별 `persistence_ratio`
- **O4 (categorical state)** — High-intensity Persistent / Low-intensity Persistent / Seasonal Parker / Dormant-Churn-like. `dLevel_post` 낮음 + `dHEXA_post` 또는 `dSymbol_post` 유의 → Low-intensity Persistent. threshold 는 O2 분포 후.

**분석 성격**: 전부 associational/descriptive. causal 아님. pilot 285 는 provisional-label
stratified(무작위 아님) → base rate 는 모집단 대표 아님. `event_period_new` 25 는 별도 세그먼트,
260명과 합산 안 함.

---

## 2. Leading Indicator 후보

### C1 — post-event HEXA/Symbol/CP progression persistence (우선순위 1)

| 항목 | 내용 |
|---|---|
| **feature 정의** | 초기 post-event 창(T0 → +14)에서 축 X ∈ {HEXA total_core_level, Symbol 레벨합, CP} 별: `dX_post_early2w = X(+14) − X(T0)`; `n_moved_early = {T0→+7, +7→+14}` 중 ΔX>min 인 구간 수; `post_slope_early = X(T0/+7/+14) OLS 기울기`. Level 은 대조축으로 동일 계산. |
| **예상 방향** | (+) — 초기 2주에 HEXA 또는 Symbol 이 ≥1구간 이상 움직인 캐릭터가 `+56` 시점 O1 충족 확률 높음. Level 만 움직이고 HEXA/Symbol flat 이면 O1 확률 낮음 (Seasonal Parker 쪽). |
| **필요 endpoint** | `stat`, `hexamatrix`(raw core 배열), `symbol` — feature·outcome 모두. `basic`(Level 대조). |
| **필요 milestone** | `2026-06-12`(persistence_ratio 분모), **`T0=2026-09-15`, `+7`, `+14`** (feature), `+28`·`+56`(outcome). |
| **confound / limitation** | ① HEXA 코어 수는 장착 변동 → name-key diff 필수, `total_core_level` 만. ② Sol Erda Fragment 거래 구매 가능 → HEXA Δ = resource investment(접속 아님). ③ Symbol 일일 하드캡 → 구간당 Δ 상한 존재, 큰 점프는 매일 참여 또는 잔여 셀렉터 사용. ④ CP 리롤 노이즈(±수백만). ⑤ **circularity 위험**: O1 이 +28~+56 의 HEXA/Symbol/CP 를 쓰므로 feature 는 **T0→+14 로, outcome 은 +28→+56 로 시간 분리**. ⑥ +14 는 저강도 성장의 측정 바닥 근처 → +56 으로 보완. |
| **검증 outcome** | O1(+56 composite), O2(축별 `dX_post_full`), O4(state). C1 feature(초기 2주) → outcome(+28~+56) 방향·순위상관. |

### C2 — pre-OVERDRIVE between-season growth magnitude (우선순위 2)

| 항목 | 내용 |
|---|---|
| **feature 정의** | panel_basic 6 milestone 에서 pre-OVERDRIVE 궤적: `pre_total_growth = level(2026-06-12) − level(2025-06-12)`; `n_pre_intervals_grew = {seg0..seg3}` 중 Δlevel≥2 구간 수; `pre_nonevent_growth = seg1(2025-09-24→12-12) Δ` (관측창 내 유일하게 버닝 없는 구간). **연속값으로 사용** (binary `between>0` 은 label-circular 라 금지). 선택: Phase A invest 스냅샷으로 `pre_HEXA_growth`, `pre_symbol_growth`(2025-06-12 → 2026-06-12). |
| **예상 방향** | (+) — pre-OVERDRIVE 에 여러 구간/큰 폭으로 성장한 캐릭터가 post-event O1 충족 확률 높음. 단 provisional label 과 얽혀 있어 **label 을 분석 단위로 쓰지 않고** pilot 5군 + `event_period_new` 를 pool 해 연속 feature 대 outcome 으로 본다. |
| **필요 endpoint** | `basic`(이미 보유, panel_basic). 투자 breadth 옵션: Phase A 의 `stat`/`hexamatrix`/`symbol`. |
| **필요 milestone** | Phase A: `2025-06-12`, `2025-12-12`, `2026-06-12` (+ panel_basic 의 `2025-09-24`, `2026-03-15`). |
| **confound / limitation** | ① **CROWN(2025-12-18~2026-06-17)이 6개월 연속 이벤트** → seg2/seg3 성장은 CROWN 버닝이지 organic 아님. 관측창 내 "순수 비이벤트" 는 seg1(≈8주) 뿐 → `pre_nonevent_growth` 신뢰구간 넓음. ② `pre_total_growth`·`n_pre_intervals_grew` 는 `Persistent_cand` 정의와 구조적 중복 → label-free pool 분석 필수, label 계수는 통제. ③ survivorship: pilot 은 2026-06 까지 랭킹 도달한 캐릭터 → pre-growth 높은 쪽 과대. ④ EXP 쿠폰으로 pre-growth 자체가 event-supported. |
| **검증 outcome** | O1, O2(pre-growth 연속값 → `dX_post_full`), O4. cohort·start_level 통제. |

### C3 — 260 arrival timing + arrival exp_rate (우선순위 3)

| 항목 | 내용 |
|---|---|
| **feature 정의** | OVERDRIVE 기간 260 을 **처음 넘긴** 캐릭터 한정: `first_260_offset` = 2026-06-18 로부터 일수; `exp_rate_at_260` = 첫 260 관측 시 레벨 내 진행도 %; `days_observed_after_260` = 관측창 끝 − first_260_date; `cp_dir_early` = 260 도달 직후 CP 방향(+/0/−). |
| **예상 방향** | (+) — 더 이른 260 도달 · 도달 시 높은 exp_rate(경계를 momentum 으로 통과) · CP (+) 방향인 캐릭터가 261+ 도달 및 post-260 HEXA/Symbol 성장 확률 높음. **climb case study n=5 기반 hypothesis** (통계 결론 아님). |
| **필요 endpoint** | `basic`(도달일·exp_rate — **일단위 필요**), `stat`(CP). post-260 투자: `hexamatrix`, `symbol`. |
| **필요 milestone** | climb: 기존 daily `2026-06-18 ~ 07-22` + CP 5 offset (보유). pilot: milestone(09-15/+7/…)은 도달일 포착엔 성김 → **주 substrate 는 climb cohort(300명, daily)**. |
| **confound / limitation** | ① 261+ n=5 (기존 데이터) → Phase B 로도 크게 안 늘 가능성(Part 1: post-255 랭킹 인구는 이벤트 중에도 대부분 정지). ② `exp_rate_at_260` 이 도달 timing 과 교란 (일단위 granularity 로 늦게 잡히면 이미 레벨 내 진행). ③ climb CP 는 8일 간격 5 snapshot → 리롤 노이즈 ±5M. ④ "arrival" 은 260 미만 → 통과한 self-selected 소수만. OVERDRIVE 시작 시 이미 260 인 pilot 대다수엔 적용 불가. |
| **검증 outcome** | 261+ 도달(level), post-260 `dHEXA`/`dSymbol`/`dCP`, arrivers 한정 O1. **hypothesis generation 유지, 비율·유의성 주장 금지.** |

### C4 — event-period ΔLevel 은 positive predictor 가 아닐 수 있다 (null/negative, 우선순위 4)

| 항목 | 내용 |
|---|---|
| **feature 정의** | `dLevel_OVERDRIVE = level(2026-09-15) − level(2026-06-12)`. 보조: `dLevel_event_hist` = ASSEMBLE/CROWN 이벤트 구간 level 증가 합 (panel_basic). |
| **예상 방향** | **null 또는 (−).** falsify 대상 명제: "큰 event-window ΔLevel → 높은 post-event progression". retrospective 상 Parker(event 성장 큼)가 정체 쪽 → cohort 통제 후 `dLevel_OVERDRIVE` 의 O1/O2 에 대한 계수 부호 ≤ 0 또는 비유의 예상. |
| **필요 endpoint** | `basic`(feature). outcome 측: `stat`/`hexamatrix`/`symbol`. |
| **필요 milestone** | `2026-06-12`, `2026-09-15` (feature); `+28`, `+56` (outcome). |
| **confound / limitation** | ① **cohort 교란**: burnend 내부에선 event_growth 가 두 label 간 동일했음(4.5 vs 5), at260 에선 큰 차이 → cohort·start_level 통제 필수. ② EXP 쿠폰 오염 → `dLevel_OVERDRIVE` 는 "이벤트가 얼마나 밀어줬나" 의 노이즈 있는 proxy. ③ retrospective 상 seg4 최대 성장 캐릭터 10/110 뿐 → pilot 내 `dLevel_OVERDRIVE` 분산 작음 → 검정력 낮음. ④ provisional label selection. |
| **검증 outcome** | O1, O2 — `dLevel_OVERDRIVE` ↔ post-event Δ 의 상관/계수가 **0 이하 또는 비유의** 임을 보이는 형태 (positive predictor 반증). |

---

## 3. 확정하지 않는 것 (descriptive signature 로만 유지)

| 항목 | 사유 |
|---|---|
| retrospective **concentration / burstiness** (`top1_share`, HHI, `conc_entropy`, `gap12`) | `n_active_ge2` 가 provisional label 을 정의상 완전 분리, 모든 산식이 그 단조함수 → circular. `docs/burstiness_robustness.md` 참고. **단** Phase B trajectory(투자 축)에 재계산한 `post_slope`·`n_post_intervals_moved` 는 C1 의 일부로 후보 유지 |
| `std(interval Δ)` | Persistent 가 오히려 큼 — 방향이 스토리와 반대. 사용 안 함 |
| `n_active` 원 카운트, `between_growth > 0` 이진 | provisional label 규칙 그대로 |

---

## 4. 데이터 상태 (후보별)

| 후보 | 이미 보유 | Wave 1 (2026-10-15+) 필요 | Wave 2 (2026-11-12+) 필요 |
|---|---|---|---|
| C1 | — | `stat`/`hexamatrix`/`symbol` @ T0/+7/+14/+28 (285명) | 동 @ +56 |
| C2 | `basic` 궤적 (panel_basic) | `stat`/`hexamatrix`/`symbol` @ Phase A 3시점 (투자 breadth 옵션) | — |
| C3 | climb daily level + CP 5snap | (pilot 겹침분) `basic`/`stat` @ post-event | — |
| C4 | `basic` @ 2026-06-12 (panel_basic) | `basic` @ T0(=09-15) + outcome endpoint | outcome @ +56 |

호출 추정 (앞서 확정): Wave 1 ≈ 9,120 · Wave 2 ≈ 1,425. 실제 수집은 별도 승인.

---

## 5. 공통 한계

- pilot 285 = provisional-label stratified, 무작위 아님 → 비율·base rate 모집단 대표 아님.
- outcome O1~O4 threshold 는 Wave 1 분포 확인 후 결정 (지금 고정 안 함).
- `+28`(4주) 은 HEXA/Symbol 저강도 성장의 측정 바닥 근처 — `+56` 이 주 판정 시점, `+28` 은 초기 신호.
- Level 은 EXP 쿠폰 오염 → post-event 구간이 event-window 보다 낫지만 "pure voluntary" 아님.
- 전 분석 associational. causal language 금지. `event_period_new` 25 는 분리 유지.

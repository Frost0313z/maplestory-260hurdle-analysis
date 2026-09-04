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

## 0.5 분석 단위 — 2-layer framework (Character ≠ Account)

메이플스토리는 유니온(리전) 때문에 **한 계정에서 여러 캐릭터를 육성**하는 것이 정상 progression 구조다.
따라서 OCID 기반 분석에서 **"버닝 캐릭터가 260에서 멈춤" ≠ "유저가 게임에서 이탈함"** 이다.
같은 계정에서 본캐/다른 부캐 성장, union level 상승이 있으면 그 캐릭터는 Parker 여도 **계정 전체
progression 은 유지** 중일 수 있다.

| Layer | 정의 | Phase B 측정 |
|---|---|---|
| **L1 · Character-level Progression Retention** | 이벤트에서 육성한 **그 캐릭터**가 종료 후에도 progression 을 지속하는가 | Level / HEXA / Symbol / CP (§1) — 4축 frame 유지 |
| **L2 · Account-level Progression Retention Context** | 그 캐릭터가 파킹돼도 **계정 전체** progression 이 유지되는가 | **proxy only**: `union_level`, `union_artifact_level`. 실제 login retention·account churn 직접 측정 **불가** (§6 feasibility) |

L2 는 항상 **proxy** 로 표기한다. Open API 로 접속 로그·계정 churn·다른 캐릭터 목록을 볼 수 없다(§6).

### 용어 수정 (이 spec 및 이후 문서에 적용)

- **Seasonal Parker** = "실패/이탈" 이 **아니다**. = *"해당 캐릭터의 event 이후 progression 이 크게
  감소하거나 정지한 상태"* (character-scoped 서술).
- **260 결과 표현**: ~~"91%가 260에서 이탈"~~ → *"260 도달 캐릭터의 91%에서 관측기간 내 해당
  캐릭터의 261+ level progression 이 관측되지 않았다."* 이들이 다른 캐릭터를 플레이했는지, 계정이
  비활성화됐는지는 현재 데이터로 알 수 없다. (climb 49/54 결과 자체는 유지.)

### Exploratory business questions (추가)

- **BQ-x1**: Seasonal Parker 중, 해당 캐릭터는 멈췄지만 **account-level progression(proxy)은 지속**
  되는 집단이 존재하는가?
- **BQ-x2 (상위)**: 성장 이벤트의 장기 전환을 평가할 때, **이벤트 캐릭터의 지속 육성**과 **계정 전체
  progression 활성화**를 구분해야 하는가?
- 제약: 내부 이벤트 목적·KPI 미상 → "넥슨의 목적은 account activation 이다" 같은 causal/intention
  claim 금지. 관측된 유저 행동 수준으로만 기술한다.

---

## 1. Outcome 정의 — Layer 1 (Character-level, provisional, operational)

Open API 로 로그인/접속 미관측 → "retained user" 대신 **post-event progression retained** 를 쓴다.
"post-event" = **major burning 지원(OVERDRIVE HB MAX + BEYOND, 2026-09-16) 종료 이후** 이며
pure voluntary 가 아니다 (평시 이벤트샵·Sunday Maple·보유 재화 존재).

관측 창: `T0 = 2026-09-15`(종료 직전), 이후 `+7 / +14 / +28`(Wave 1), `+56`(Wave 2).
4축 (frame locked, **Layer 1 = character-level**): **Level** = grind/time · **HEXA** = character
resource investment(거래 가능 → 접속 아님) · **Symbol** = 장기/일일형 progression 참여 proxy ·
**CP** = 전환 결과. **Union 은 Layer 2** 로 분리 (§1B).

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
- **O4 (categorical state)** — Layer 1 축(character): High-intensity Persistent / Low-intensity
  Persistent / Seasonal Parker / Dormant-like. `dLevel_post` 낮음 + `dHEXA_post` 또는 `dSymbol_post`
  유의 → Low-intensity Persistent. threshold 는 O2 분포 후.
- **O4b (Parker × account layer, exploratory)** — O4 에서 Seasonal Parker 로 분류된 캐릭터를 L2
  proxy 로 분기 (§1B):
  - Character Parker **+ account proxy 정지** → **Dormant / Churn-like candidate**
  - Character Parker **+ account proxy 지속** → **Portfolio Rotation candidate** — 버닝 캐릭터는
    파킹했으나 계정 내 다른 progression 으로 이동했을 *가능성*. **candidate 로만.** Union 변화만으로
    확정하지 않는다 (다른 캐릭터 행동 직접 확인 불가, §6).

**분석 성격**: 전부 associational/descriptive. causal 아님. pilot 285 는 provisional-label
stratified(무작위 아님) → base rate 는 모집단 대표 아님. `event_period_new` 25 는 별도 세그먼트,
260명과 합산 안 함.

---

## 1B. Account-level Progression Retention Context — Layer 2 (proxy only)

Open API 로 접속·계정 churn·다른 캐릭터를 볼 수 없으므로(§6), **캐릭터 ocid 로 얻는 유일한
계정 단위 신호 = Union aggregate**. 이를 "account context/control" 에서 한 단계 확장해 **account-level
progression 의 보조 proxy** 로 사용 가능성을 검토한다 (확정 아님).

| L2 변수 | 정의 | endpoint |
|---|---|---|
| `union_pre` / `union_post` | `union_level` at 2026-06-12 / +28 / +56 | `/user/union` (ocid 입력) |
| `dUnion_post` | `union_level(+56) − union_level(T0)` | 〃 |
| `union_artifact_pre/post`, `dUnionArtifact_post` | `union_artifact_level` 궤적 (아티팩트 AP 는 느린 계정 투자 sink) | `/user/union` 응답 필드 |

**exploratory 조합 (Phase B)** — threshold hard-code 금지, 분포 확인 후 결정:

| 분류 | character progression | union progression |
|---|---|---|
| **A. Character Persistent** | ↑ | (무관) |
| **B. Character Parker + Account-active candidate** | ≈ 0 | `dUnion_post` > meaningful threshold |
| **C. Character Parker + Account-dormant candidate** | ≈ 0 | `dUnion_post` ≈ 0 |

**한계**: `union_level` flat ≠ account churn. Union 8000+ 등 이미 높은 수준에서는 부캐 레벨이 잘 안
올라도(브레이크포인트 포화) 플레이할 수 있다 → Union flat 은 "계정 성장 신호 없음" 이지 "이탈"
아님. `dUnion_post > 0` 은 계정 내 *어떤* 캐릭터가 레벨을 올렸거나 아티팩트 EXP 를 썼다는 coarse
증거일 뿐, 어느 캐릭터인지·얼마나 활발한지는 알 수 없다.

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

### C5 — account-level progression proxy (Union) 로 Parker 분기 (Layer 2, exploratory)

| 항목 | 내용 |
|---|---|
| **feature 정의** | `dUnion_post = union_level(+56) − union_level(T0)`; `dUnionArtifact_post`; `union_pre` (포화도 통제용). §1B A/B/C 조합. |
| **예상 방향** | character progression ≈ 0 (Seasonal Parker) 인 집단 안에서 `dUnion_post` 분포가 **이봉(bimodal)** 이면 Portfolio Rotation candidate 와 Dormant-like candidate 가 분리됨을 시사. 단봉이면 분리 신호 없음. |
| **필요 endpoint** | `/user/union` (ocid 입력). 선택: `/user/union-artifact` (아티팩트 AP). |
| **필요 milestone** | `2026-06-12`, `T0=2026-09-15`, `+28`, `+56`. |
| **confound / limitation** | ① `union_level` 은 계정 aggregate — 어느 캐릭터가 기여했는지 불명, **분석 대상 캐릭터 자신의 레벨 상승도 포함**될 수 있음(이 캐릭터가 260→260 이면 기여 0 이라 순수 "다른 곳" 신호에 가깝지만 완전 분리는 아님). ② Union flat ≠ churn (포화). ③ `union_level` 상한 근처(≈8500) 캐릭터는 변화 폭 작음 → `union_artifact_level` 보조. ④ 표본: Parker 로 분류될 pilot 수가 O4 확정 후에야 정해짐. ⑤ **login/account churn 직접 측정 아님 — 전부 proxy.** |
| **검증 outcome** | O4b (Parker → Portfolio Rotation candidate vs Dormant-like candidate). BQ-x1. **candidate 라벨만, 확정 금지.** |

---

## 3. 확정하지 않는 것 (descriptive signature 로만 유지)

| 항목 | 사유 |
|---|---|
| retrospective **concentration / burstiness** (`top1_share`, HHI, `conc_entropy`, `gap12`) | `n_active_ge2` 가 provisional label 을 정의상 완전 분리, 모든 산식이 그 단조함수 → circular. `docs/burstiness_robustness.md` 참고. **단** Phase B trajectory(투자 축)에 재계산한 `post_slope`·`n_post_intervals_moved` 는 C1 의 일부로 후보 유지 |
| `std(interval Δ)` | Persistent 가 오히려 큼 — 방향이 스토리와 반대. 사용 안 함 |
| `n_active` 원 카운트, `between_growth > 0` 이진 | provisional label 규칙 그대로 |

---

## 4. 데이터 상태 (후보별)

| 후보 | Layer | 이미 보유 | Wave 1 (2026-10-15+) 필요 | Wave 2 (2026-11-12+) 필요 |
|---|---|---|---|---|
| C1 | L1 | — | `stat`/`hexamatrix`/`symbol` @ T0/+7/+14/+28 (285명) | 동 @ +56 |
| C2 | L1 | `basic` 궤적 (panel_basic) | `stat`/`hexamatrix`/`symbol` @ Phase A 3시점 (투자 breadth 옵션) | — |
| C3 | L1 | climb daily level + CP 5snap | (pilot 겹침분) `basic`/`stat` @ post-event | — |
| C4 | L1 | `basic` @ 2026-06-12 (panel_basic) | `basic` @ T0(=09-15) + outcome endpoint | outcome @ +56 |
| C5 | L2 | — | `/user/union` @ 2026-06-12 / T0 / +28 (285명) — 기존 PILOT_ENDPOINTS 에 `union` 포함됨 | `/user/union` @ +56 |

호출 추정 (앞서 확정, `union` 포함): Wave 1 ≈ 9,120 · Wave 2 ≈ 1,425. 실제 수집은 별도 승인.

---

## 5. 공통 한계

- pilot 285 = provisional-label stratified, 무작위 아님 → 비율·base rate 모집단 대표 아님.
- outcome O1~O4 threshold 는 Wave 1 분포 확인 후 결정 (지금 고정 안 함).
- `+28`(4주) 은 HEXA/Symbol 저강도 성장의 측정 바닥 근처 — `+56` 이 주 판정 시점, `+28` 은 초기 신호.
- Level 은 EXP 쿠폰 오염 → post-event 구간이 event-window 보다 낫지만 "pure voluntary" 아님.
- **Layer 2 는 전부 proxy**: login retention·account churn·portfolio rotation 을 직접 관측하지 못한다(§6).
  Union 신호로는 "계정에 성장 활동이 있었다/없었다" 의 coarse 방향만, candidate 라벨만.
- 전 분석 associational. causal/intention claim 금지. `event_period_new` 25 는 분리 유지.

---

## 6. Account portfolio tracking feasibility (API 호출 없이 조사)

**질문**: 캐릭터 OCID 로 동일 계정의 다른 캐릭터·계정 식별자·과거 계정 캐릭터 목록을 추적할 수 있는가.

### 근거 1 — 우리가 실제로 받은 응답 (definitive)

`collect.py` / `collect_panel.py` 가 쓰는 엔드포인트와 smoke test raw dump(`data/panel_raw_*.jsonl`):

| 엔드포인트 | 입력 | 응답에 계정 식별자 | 응답에 캐릭터 목록 |
|---|---|---|---|
| `/maplestory/v1/id` | `character_name` | 없음 (`ocid` 만 반환) | 없음 |
| `/maplestory/v1/character/basic` | `ocid` (+`date`) | **없음** (world/class/gender/name/level/exp…) | 없음 |
| `/maplestory/v1/character/stat` · `/hexamatrix` · `/symbol-equipment` | `ocid` (+`date`) | **없음** (smoke dump 확인) | 없음 |
| `/maplestory/v1/user/union` | **`ocid`** (+`date`) | **없음** (`union_level`/`union_grade`/`union_artifact_level` 만, smoke dump 확인) | 없음 |
| `/maplestory/v1/ranking/overall` | `date`/`world_type`/`page` | 없음 | 이름·레벨만 (ocid 조차 없음) |

→ 우리가 호출하는 모든 엔드포인트는 **캐릭터 단위**이고, 응답 어디에도 account id 필드가 없다.
`/user/union` 도 경로만 `user` 이지 입력은 ocid, 반환은 그 캐릭터가 속한 계정의 **union 집계값**뿐
(계정 id·부캐 목록 없음).

### 근거 2 — API 설계 (schema 지식, 잔여 불확실성 표시)

- 넥슨 오픈 API(메이플)는 **캐릭터명 → ocid → 캐릭터 데이터** 흐름의 공개 데이터 API다. 임의
  캐릭터의 ocid 에서 계정을 역식별하는 공개 경로는 없다.
- `/maplestory/v1/character/list` 형태의 엔드포인트가 존재하더라도, 그것은 **API 키를 발급한
  넥슨 계정 본인의 캐릭터 목록**(OAuth 성격)으로 알려져 있다. 임의 타 캐릭터의 계정 로스터
  열거에는 쓸 수 없고, `date` 소급도 없다(현재 로스터). — 공개 문서 원문을 이번에 로드하지
  못해 이 항목은 "확인된 설계상 그렇게 동작" 수준으로 표기하며, **결론은 바뀌지 않는다**
  (우리 키/흐름으로는 타 계정 포트폴리오 접근 불가).

### 결론

| 질문 | 답 |
|---|---|
| OCID 로 동일 계정의 다른 캐릭터 목록 조회 | **불가** |
| OCID → account identifier 역식별 | **불가** (어떤 응답에도 계정 id 없음) |
| 다른 캐릭터들의 basic/stat progression 연결 | **불가** (연결 키 없음) |
| 과거 date 기준 계정 캐릭터 목록 | **불가** (그런 파라미터·엔드포인트 없음) |
| `/user/union` 이 쓰는 식별자 | **`ocid`** (계정 id 아님). 반환은 union 집계값만 |
| 계정 단위로 얻을 수 있는 것 | `union_level`, `union_grade`, `union_artifact_level` — 그 캐릭터 ocid 한 건으로 얻는 **집계 proxy**. 어느 부캐가 기여했는지 불명 |

→ **Layer 2 (account-level) 는 Union 집계 proxy 하나로만 근사 가능**하며, Portfolio Rotation 은
확정 불가·candidate 전용이다. 이 한계는 spec 전반(§0.5·§1B·§5·C5)에 반영됨.
새 계정 데이터 확보에는 별도 인증 범위 확대가 필요 (이번 범위 밖).

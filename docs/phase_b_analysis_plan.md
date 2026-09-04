# Phase B — Analysis Plan (FROZEN)

Freeze: 2026-09-04 · 선행: `docs/phase_b_hypothesis_spec.md`, `docs/retrospective_eda_findings.md`,
`docs/burstiness_robustness.md`, `endpoint_feasibility_probe.md`
상태: **동결.** 이 문서의 Research Question / Outcomes / Hypotheses / Features / State 정의 /
Decision rules 는 Wave 1 수집 전에 확정된 것이며, 결과를 보고 사후에 바꾸지 않는다
(threshold 만 명시된 규칙에 따라 분포에서 결정).

---

## 1. Primary Research Question

> **여름 성장 이벤트에서 성장한 캐릭터 중 어떤 캐릭터가 주요 버닝 지원 종료 이후에도 의미 있는
> progression 을 지속하는가?**

분석 단위 = **캐릭터 (OCID panel)**. "주요 버닝 지원 종료" = OVERDRIVE 하이퍼 버닝 MAX + 버닝
BEYOND 종료 (2026-09-16).

---

## 2. Outcomes

### 2.1 Primary — Post-event Character Progression Retention

관측 축 4개 (Layer 1, character-level): **Level · HEXA · Symbol · Combat Power(CP)**.

**단순 Δ > 0 을 Persistent 로 정의하지 않는다.** `+7 / +14 / +28 / +56` trajectory 에서 아래
5가지를 산출한 뒤, meaningful threshold 와 state 를 **데이터 분포 기반**으로 설계한다:

| 차원 | 정의 (축 X 별) |
|---|---|
| progression **existence** | 어떤 post interval 에서든 ΔX > `min_meaningful_change_X` (임계는 +28 분포에서 결정) |
| progression **magnitude** | `dX_post_28 = X(+28) − X(T0)`, `dX_post_56 = X(+56) − X(T0)` (T0 = 2026-09-15) |
| progression **breadth** | `n_axes_progressed_post` = {HEXA, Symbol, CP} 중 `dX_post_56` 가 meaningful 인 축 수 |
| **number of active intervals** | `n_post_intervals_moved_X` = {T0→+7, +7→+14, +14→+28, +28→+56} 중 ΔX meaningful 인 구간 수 |
| progression **persistence** | `post_slope_X` = X 의 5점(T0/+7/+14/+28/+56) OLS 기울기 · `persistence_ratio_X` = `dX_post_56` / max(`dX_event_X`, ε), `dX_event_X` = X(T0) − X(2026-06-12) |

> "meaningful" 은 축마다 다르고, Wave 1(+28) 분포의 noise floor / 낮은 분위에서 정한다. 이 문서에서
> 수치로 고정하지 않는다 (§8 Decision rules).

### 2.2 Secondary — Account-level Progression Context (Union, proxy only)

Union 은 **account retention 직접 측정치가 아니다.** account-level progression 의 proxy 로만 쓴다.
반드시 **baseline Union level 과 ΔUnion 을 함께** 사용한다.

| 변수 | 정의 |
|---|---|
| `union_pre` | `union_level` at 2026-06-12 |
| `dUnion_post_28 / _56` | `union_level(+28 / +56) − union_level(T0)` |
| `union_artifact_pre`, `dUnionArtifact_post` | `union_artifact_level` 궤적 (느린 계정 투자 sink) |

- **먼저** `union_pre` 구간별(예: <4000 / 4000–6000 / 6000–8000 / 8000+) `dUnion_post` 분포를
  확인한다. 구간별 참조 분포 없이 절대 임계로 판정하지 않는다.
- **high-Union 캐릭터에서 `dUnion_post = 0` 을 inactivity/churn 으로 해석하지 않는다** (브레이크포인트
  포화로 부캐 레벨이 잘 안 올라도 플레이 가능).

---

## 3. Prospective Hypotheses (pre-registered)

| ID | 가설 | 사전 등록된 판정 기준 (Wave 2 이후) |
|---|---|---|
| **H1** | Event-period ΔLevel alone 은 post-event progression retention 에 대해 **약하거나 양의 예측력이 없다** | `dLevel_OVERDRIVE` (= level(2026-09-15) − level(2026-06-12)) 와 composite post progression 간 Spearman ρ 를 cohort 층별 계산. ρ ≤ 0 이거나 95% bootstrap CI 가 0 포함 → **H1 지지**. ρ > 0 & CI 가 0 배제가 ≥2 cohort → H1 반증(=양의 예측력 있음) |
| **H2** | Pre-event / historical between-season progression **magnitude** 는 future post-event progression 과 **연관** 있다 | label-free pool(285 + event_period_new 25)에서 `pre_total_growth_level` 및 `n_pre_intervals_grew` 와 composite post progression 간 ρ. cohort·start_level 통제. CI 가 0 배제 & 방향 (+) → **연관 지지**. provisional label 을 공변량으로 넣은/뺀 두 버전 모두 보고 (circularity 투명화) |
| **H3** | Arrival momentum (260 도달 timing + 도달 시 exp_rate) 는 이후 progression 과 **연관될 수 있다** | **descriptive only.** climb daily substrate. 각 arm n ≥ 20 이 아니면 Supported/Not 판정 안 하고 방향 + 개별 사례만 보고 |
| **H4** | Post-event progression **breadth (HEXA/Symbol/CP)** 는 low-intensity persistent 캐릭터를 true character parker 와 level 단독보다 잘 구분한다 | `dLevel_post ≈ 0` 인 캐릭터 부분집합에서, `n_axes_progressed_post ≥ 1 & 해당 축 post_slope > 0 & n_post_intervals_moved ≥ 2` 를 만족하는 subgroup 크기 · 궤적을 level-only 분류와 비교. subgroup 이 `dLevel_post ≈ 0` 집단의 non-trivial 비중(≈≥15%)이고 궤적이 뚜렷이 다르면 → **H4 지지** |
| **H5** (exploratory) | 일부 Character Parker 는 Union 을 통해 account-level progression 신호를 보일 수 있다 | **존재 가능성 탐색.** Character Parker 로 분류된 캐릭터 중 `dUnion_post_56` 가 자신의 `union_pre` 밴드 75분위 초과 & 절대 하한 초과인 캐릭터 수 보고. "존재 가능성" 표현만, **Portfolio Rotation 증명 아님** |

---

## 4. Features

### 4.1 Post-event trajectory (Layer 1) — 축 X ∈ {Level, HEXA_total_core_level, Symbol_level_sum, CP}

`X_pre`(2026-06-12), `X_T0`(2026-09-15), `X_+7/+14/+28/+56`, `dX_event`, `dX_post_28`, `dX_post_56`,
`n_post_intervals_moved_X`, `post_slope_X`, `persistence_ratio_X`, `n_axes_progressed_post`.

- `HEXA` = Σ `hexa_core_level`, **`hexa_core_name` key 기반 diff** (코어 장착 변동 → `active_core_count` 사용 안 함).
- `Symbol` = 아케인 + 어센틱 레벨 합.
- `CP` = 전투력. 리롤/장비 해제 음수 스파이크 → winsorize 또는 `note` 플래그, 원값 보존.

### 4.2 Pre-event / historical (panel_basic + Phase A invest)

- `pre_total_growth_level` = level(2026-06-12) − level(2025-06-12)
- `n_pre_intervals_grew` = seg0..seg3 중 Δlevel ≥ 2 구간 수
- `pre_nonevent_growth_level` = seg1 Δ (2025-09-24→12-12) — **CROWN 6개월 연속이라 순수 비이벤트 구간은 이것뿐, CI 넓음**
- `pre_HEXA_growth`, `pre_symbol_growth` = 2025-06-12 → 2026-06-12 (Phase A 스냅샷, 옵션)
- `dLevel_OVERDRIVE` = level(2026-09-15) − level(2026-06-12)   [H1]

### 4.3 Arrival (climb daily substrate + pilot 겹침분)

- `first_260_offset` (2026-06-18 기준일), `exp_rate_at_260`, `days_observed_after_260`, `cp_dir_early`

### 4.4 Account context (Layer 2, Union)

- `union_pre`, `dUnion_post_28/_56`, `union_artifact_pre`, `dUnionArtifact_post`
- 파생: `union_pre` 밴드, 밴드별 `dUnion_post` 분위

### 4.5 확정하지 않는 것 (descriptive signature only)

retrospective concentration/burstiness (`top1_share`, HHI, `conc_entropy`, `gap12`),
`std(interval Δ)`, raw `n_active` 카운트, `between_growth > 0` 이진.
→ provisional label 을 정의상 재표현하므로 predictive feature 아님 (`docs/burstiness_robustness.md`).
단 **post-event 투자축 궤적**의 `post_slope` / `n_post_intervals_moved` 는 §4.1 에 포함(별개 개념).

---

## 5. State Definitions (PROVISIONAL — truth label 아님)

Phase B outcome(+28/+56)을 보기 전까지 어떤 provisional state 도 정답 라벨로 쓰지 않는다.
아래 정의는 +28/+56 분포로 threshold 를 채운 뒤 **candidate 분류**로만 사용한다.

| state | character 축 | account 축 (context) |
|---|---|---|
| **High-intensity Character Persistent** | `dLevel_post` meaningful **&** ≥1 of HEXA/Symbol/CP progressed, breadth ≥ 2, slope > 0 | — |
| **Low-intensity Character Persistent** | `dLevel_post ≈ 0` **이지만** ≥1 of HEXA/Symbol/CP 가 `slope > 0 & n_intervals ≥ 2` | — |
| **Seasonal Character Parker** | `dX_event > 0` (OVERDRIVE 중 성장) **이나** post 4축 모두 ≈ 0 | — |
| **Dormant-like Character** | `dX_event ≈ 0` **&** post 4축 모두 ≈ 0 | `dUnion_post ≈ 0` (context) |
| **Portfolio Rotation candidate** (exploratory only) | Character Parker / Dormant-like on character 축 | **`dUnion_post` 가 `union_pre` 밴드 참조 분포 대비 상위** → *가능성* 표시. 확정 아님 |
| **Reactivated Character** (retrospective dimension) | Phase A: 장기 정체 후 특정 시즌 버스트. post-event state 와 **직교 축**, 상호배타 아님 | — |

- `event_period_new` 25 는 별도 세그먼트, 위 분류·모비율 추정에 합산하지 않음.

---

## 6. Timeline

| 시점 | 작업 |
|---|---|
| 2026-09-04 (freeze) | 이 계획 동결. parser/resume/error smoke test **완료** (16캐릭터·192콜, commit `d6a8639` — stat/hexamatrix/symbol/union 파서·empty 구분·resume 확인). 추가 smoke 불필요 |
| 2026-09-16 | OVERDRIVE 종료 |
| **Wave 1**: 2026-10-15 이후 | `collect_panel.py --sampling list --list-file data/pilot_targets.csv --tier pilot --endpoints pilot` — Phase A(2025-06-12 / 2025-12-12 / 2026-06-12) invest + Wave 1 post(2026-09-15 / 09-23 / 09-30 / 10-14), 285명. **≈ 9,120 콜.** Phase A basic 는 Stage 1 에서 수집됨(재호출 0) |
| +28 checkpoint | 10-14 데이터 확보 → §8 Decision rules (분포·임계·예비 O4) |
| **Wave 2**: 2026-11-12 이후 | 동 명령 재실행 → `2026-11-11` (+56) 만 자동 수집. **≈ 1,425 콜** |
| +56 분석 | 최종 state 분류 + H1~H5 판정 + `docs/pilot_findings.md`. 전체 1,958 확장 여부 결정 |

추가 대규모 API 호출은 Wave 1/2 승인 시에만. 지금은 없음.

---

## 7. Confounds

| # | confound | 처리 |
|---|---|---|
| C-1 | **Event support 오염** — 버닝이 코어 젬스톤·솔 에르다/조각·심볼·EXP 쿠폰을 레벨별 지급 | post-event 창(주요 버닝 종료 후)으로 feature/outcome 을 옮김. 단 "pure voluntary" 아님(§9 L-6) |
| C-2 | **Cohort 교란** — cohort 별 랭킹 깊이·start_level·전투력 상이. burnend 내부에선 event_growth 가 label 간 동일, at260 에선 큰 차이 | 모든 H 검정 cohort 층화 + start_level 통제 |
| C-3 | **Provisional label ↔ feature circularity** — pre-growth breadth / concentration 이 label 정의와 중복 | label-free pool 분석, label 공변량 유무 양쪽 보고 |
| C-4 | **CROWN 6개월 연속 이벤트** — 2025-12~2026-06 에 "비이벤트" 구간 없음 | `pre_nonevent_growth` 는 seg1(8주)만, CI 넓음 명시 |
| C-5 | **CP 노이즈** — 리롤·장비 해제로 ±수백만 | winsorize / note 플래그, 원값 보존 |
| C-6 | **HEXA 코어 장착 변동** — 코어 수 14→10 등 | `hexa_core_name` key diff, `total_core_level` 만 |
| C-7 | **Symbol 일일 하드캡** — 구간당 Δ 상한, 잔여 셀렉터 늦게 사용 가능 | Δ 를 상한 대비로 해석, 급점프 플래그 |
| C-8 | **Selection** — pilot 285 = provisional-label stratified, 무작위 아님 | 비율·base rate 를 모집단으로 일반화 안 함. 카운트 위주 보고 |
| C-9 | **Survivorship** — pilot 은 2026-06 까지 랭킹 도달한 캐릭터 | pre-growth 높은 쪽 과대 명시 |
| C-10 | **Outcome–feature 시간 중첩** — C1 feature 와 O1 이 같은 창을 쓰면 circular | feature = T0→+14, outcome = +28→+56 로 시간 분리 |
| C-11 | **Union aggregate** — `union_level` 에 분석 대상 캐릭터 자신 기여분 포함 가능 | 대상 캐릭터가 Parker(레벨 무변동)면 기여 ≈ 0 이라 "다른 곳" 신호에 가깝지만 완전 분리 아님, 명시 |

---

## 8. Decision Rules — after +28 / after +56

### after +28 (Wave 1 데이터)

1. 축별 post-interval Δ 분포 산출 → `min_meaningful_change_X` 를 **noise floor 또는 낮은 분위**에서
   결정하고 문서화 (예: |ΔCP| 은 리롤 노이즈 분포의 상위 밖; ΔHEXA/ΔSymbol 은 ≥1 레벨).
2. 예비 O4 candidate 분류. **클래스 크기 확인.** Low-intensity Character Persistent n < ~10 →
   underpowered 표시, 결론 +56 로 유예.
3. `union_pre` 밴드별 `dUnion_post_28` 분포 확인. 분포가 단봉/축퇴 → **H5 = "분리 신호 없음"**,
   Portfolio Rotation 분기 중단. 이봉·꼬리 존재 → 밴드별 참조 임계 잠정 설정.
4. H1 예비: `dLevel_OVERDRIVE` ↔ 예비 composite post progression, cohort 층별 ρ 방향 확인.
5. `first_260` arrivers 수 확인. arm 당 n < 20 → H3 는 descriptive 로 고정.

### after +56 (Wave 2 데이터)

6. `min_meaningful_change_X` 를 +56 창으로 재확인(더 긴 창 → 저강도 성장 가시성 ↑). 바뀌면 +28
   분류도 재산출, 변화 문서화.
7. 최종 O4 + O4b(Parker × Union) candidate 분류. **비율 아닌 카운트**로 보고(선택편향).
8. H1~H5 를 §3 의 사전 등록 기준으로 **Supported / Partially Supported / Not Supported /
   Cannot-evaluate** 판정. 각 판정에 수치 근거 첨부.
9. **전체 1,958 확장 결정**: (a) C1/C2/C4 중 하나라도 방향 일관 + cohort-robust association 이
   pilot 규모에서 보이고, (b) 타깃 state 클래스가 안정적 기술에 너무 작으면 → 확장 수집 제안
   (별도 승인). 아니면 pilot 결론으로 종료.
10. `docs/pilot_findings.md` 작성: state 분포(카운트), H1~H5 판정, 확장 여부, 다음 액션.

---

## 9. Limitations (문서 명시)

1. **OCID panel 은 character-level 분석이다.** 계정 단위 결론이 아니다.
2. **character inactivity ≠ account churn.** 캐릭터가 멈춰도 유저는 다른 캐릭터를 플레이할 수 있다.
3. **동일 계정의 다른 캐릭터 progression 은 공개 API 로 연결할 수 없다** (`endpoint_feasibility_probe.md`,
   `phase_b_hypothesis_spec.md §6` — 응답에 account id 없음, `/character/list` 는 키 소유자 본인 계정 한정).
4. **Union 은 account activity/retention 의 직접 측정치가 아니다** — aggregate proxy.
5. **Union flat ≠ inactivity**, 특히 high-Union account (브레이크포인트 포화).
6. **post-event progression 도 완전한 voluntary progression 이 아니다** — 평시 이벤트샵·Sunday
   Maple·기존 보유 재화 존재. "major burning 지원 종료 이후에도 관측되는 progression" 이 정확한 표현.
7. **HEXA/Symbol/CP 변화는 playtime 이나 payer status 를 직접 의미하지 않는다** — Sol Erda Fragment
   등은 거래 구매 가능. 안전한 해석 = "그 캐릭터의 progression 에 대한 지속적 resource investment".
8. pilot 285 = provisional-label stratified(무작위 아님) → 비율·base rate 모집단 대표 아님.
9. 전 분석 associational. **causal / intention claim 금지** (개입 효과·넥슨 내부 목적 단정 안 함).

---

## 10. Claim Boundary — 3 단계

### A. 현재 데이터로 말할 수 있는 것 (retrospective, pre-outcome)

- 랭킹 통합 3M위 근방 post-255 캐릭터는 관측 35일간 대부분 레벨 무변동 (Part 1).
- climb 260 도달자 54명 중 49명(91%)에서 **관측기간 내 해당 캐릭터의 261+ level progression 이
  관측되지 않았다** (character-scoped; 다른 캐릭터 플레이 / 계정 비활성 여부는 불명).
- **H1 방향 근거**: 이벤트 기간 큰 ΔLevel 은 "여러 시즌 progression" provisional label 과 양의
  관계가 없다 (Parker event_growth median 9 > Persistent 5; matched pair 에서 같은 event 성장에
  total 2~4배; burnend 내부 event_growth 동일).
- concentration/burstiness 는 provisional label 을 정의상 재표현한 것 (circular). 독립 신호 아님.
- Character ≠ Account 는 구조적으로 확인됨 (공개 API 로 계정 연결 불가).

### B. Phase B 이후 (2026-11 데이터 확보 후) 말할 수 있는 것 — pilot 285명, character-level, associational

- 어떤 **pre-event / arrival / trajectory feature** 가 주요 버닝 지원 종료 후 4축(Level/HEXA/Symbol/CP)
  progression 지속과 **연관**되는가 (방향·순위상관·cohort 내부 일관성; 인과 아님).
- **Low-intensity Character Persistent** 가 별개 관측 집단으로 나타나는가 — level 단독 분류 대비
  HEXA/Symbol/CP breadth 분류가 추가로 잡아내는 subgroup 유무 (H4).
- H1 반증 여부, H2 연관 여부, H4 분리력 여부 — §3 사전 등록 기준으로.
- Character Parker 중 Union proxy 가 움직이는 **사례가 존재하는가** (H5, 존재 가능성만).
- pilot 규모에서 신호가 보이면 전체 1,958 확장이 정당한가 (§8-9).

### C. 이 데이터로도 말할 수 없는 것 (범위 밖 — 추가 인증/데이터 필요)

- 실제 login / DAU / session retention, account churn.
- 동일 계정의 다른 캐릭터가 실제로 성장했는지 (Union 은 aggregate proxy, 어느 캐릭터인지 불명).
- Portfolio Rotation 의 **확정** (candidate 존재 가능성까지만).
- 결제 / ARPU / LTV / payer conversion.
- 넥슨의 이벤트 설계 의도 · 내부 KPI (intention claim 금지).
- 인과: "특정 행동을 하면 Persistent 가 된다" (associational only, 개입 실험 없음).
- 모집단 일반화 — pilot 은 provisional-label stratified, 무작위 표본 아님. 비율·base rate 는
  랭킹/서버 전체를 대표하지 않는다.
- pilot 285명을 넘는 전체 결론 (확장 수집 전).

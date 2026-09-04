/* ============================================================================
 * report/data.js  — 리포트에 들어가는 모든 수치를 이 한 파일에 모은다.
 *
 *   REPORT_DATA.real     : 이미 확보한 실제 분석 결과 (repo 의 CSV/분석에서 나온 값)
 *   REPORT_DATA.pending  : Phase B(이벤트 종료 후) 미수집 영역 — 미래 데이터 없음, 상태만
 *
 * Phase B 결과가 나오면 pending.* 를 실제 값으로 교체하고 status 를 "done" 으로 바꾸면
 * render.js 가 자동으로 placeholder 대신 실제 차트를 그린다. 미래 수치를 임의로 만들지 말 것.
 * ==========================================================================*/
window.REPORT_DATA = {

  meta: {
    title: "메이플스토리 성장 이벤트의 Seasonal → Core Progression 전환 분석",
    subtitle: "이벤트에서 많이 성장한 캐릭터가 이벤트 종료 후에도 계속 성장하는가?",
    scopeNote: "NEXON Open API 기반 character-level longitudinal analysis · 넥슨 내부 데이터·결제 데이터 아님",
    dataSources: "/character/basic · /character/stat · /character/hexamatrix · /character/symbol-equipment · /user/union · /ranking/overall",
    updated: "2026-09-04",
    repo: "github.com/Frost0313z/maplestory-260hurdle-analysis",
    purpose: "코디세이 부트캠프 AI 데이터 분석 미션 + 게임 사업 PM 포트폴리오"
  },

  /* ------------------------------------------------------------------ *
   * REAL — 확보된 실제 값
   * ------------------------------------------------------------------ */
  real: {

    /* Section 2 — Initial Discovery : climb cohort */
    climb: {
      cohortN: 300,
      screening: "앵커 직전 14일간 레벨이 오른(모멘텀) Lv.255~258 캐릭터",
      funnel: [
        { key: "cohort",   label: "climb cohort",        n: 300, pct: 100.0 },
        { key: "reach260", label: "35일 내 Lv.260 도달",  n: 54,  pct: 18.0 },
        { key: "final260", label: "260 도달 후 최종 Lv.260", n: 49,  pct: 90.7, sub: "260 도달자 54명 기준" },
        { key: "cross261", label: "261+ 도달",            n: 5,   pct: 9.3,  sub: "260 도달자 54명 기준" },
        { key: "reach270", label: "270+ 도달",            n: 0,   pct: 0.0,  sub: "260 도달자 54명 기준" }
      ],
      robustness: [
        { window: "관측창 ≥ 0일 (전체)", reach260: 54, final260: 49, pct: 90.7 },
        { window: "관측창 ≥ 7일",        reach260: 39, final260: 35, pct: 89.7 },
        { window: "관측창 ≥ 14일",       reach260: 23, final260: 20, pct: 87.0 }
      ],
      message: "260 도달 이후 해당 캐릭터의 즉각적인 level progression이 크게 감소했다. 관측창을 ≥14일로 좁혀도 패턴이 유지되므로 '관측 기간 부족' 때문이 아니다.",
      caveat: "이 수치는 character-level 관측이다. 해당 유저가 다른 캐릭터를 플레이했는지, 계정이 비활성화됐는지는 이 데이터로 알 수 없다. '이탈'로 표현하지 않는다."
    },

    /* Section 3 — Historical EDA : Parker vs Persistent candidate */
    signature: {
      chartTitle: "Historical growth signature (Parker 49 vs Persistent candidate 61)",
      groups: [
        { key: "parker",     label: "Seasonal Parker",        n: 49,
          metrics: { eventGrowth: 9, betweenGrowth: 0,  totalGrowth: 9,  top1Share: 1.00, hhi: 1.00 } },
        { key: "persistent", label: "Persistent candidate",   n: 61,
          metrics: { eventGrowth: 5, betweenGrowth: 22, totalGrowth: 30, top1Share: 0.50, hhi: 0.382 } }
      ],
      metricMeta: {
        eventGrowth:   { name: "이벤트 기간 성장 (median ΔLv)", fmt: "int" },
        betweenGrowth: { name: "시즌 사이 성장 (median ΔLv)",   fmt: "int" },
        totalGrowth:   { name: "15개월 total 성장 (median ΔLv)", fmt: "int" },
        top1Share:     { name: "top-1 구간 집중도 (maxΔ / totalΔ)", fmt: "ratio" },
        hhi:           { name: "성장 집중 HHI  Σ(Δi/total)²",   fmt: "ratio" }
      },
      keyMessage: "Peak event growth ≠ long-term progression. 이벤트 기간에 가장 크게 성장한 쪽은 오히려 Parker다.",
      circularityNote: "growth concentration(top1 share·HHI)은 provisional label 정의(‘Δ≥2 구간 ≥3’)와 circularity가 있어 predictive evidence가 아니다. historical descriptive signature로만 본다. (docs/burstiness_robustness.md)"
    },

    /* Section 3 & 6 — 가설 상태판 */
    hypotheses: [
      { id: "H1", text: "이벤트 기간 성장량이 클수록 장기 progression 가능성이 높다",
        status: "Not Supported",
        basis: "Parker median event ΔLv 9 > Persistent 5. 같은 event 성장에서 Persistent의 total 성장이 2~4배. burnend cohort 내부에서는 event 성장이 동일(4.5 vs 5)." },
      { id: "H2", text: "pre-event / historical between-season progression magnitude가 post-event progression과 연관된다",
        status: "Pending (Phase B)",
        basis: "retrospective에서 방향성은 보이나 label과 circularity. label-free pool + prospective outcome으로 검증 예정." },
      { id: "H3", text: "260 arrival momentum(도달 timing + 도달 시 exp_rate)이 이후 progression과 연관될 수 있다",
        status: "Pending (Phase B, descriptive)",
        basis: "climb 261+ 도달 n=5 기반 hypothesis. 통계적 결론 없이 방향·사례만." },
      { id: "H4", text: "post-event progression breadth(HEXA/Symbol/CP)가 low-intensity persistent를 level 단독보다 잘 구분한다",
        status: "Pending (Phase B)",
        basis: "레벨이 멈춰도 HEXA/Symbol/CP에 자원 투자가 이어지는 집단의 존재 여부를 +28/+56에서 확인." },
      { id: "H5", text: "일부 Character Parker는 Union을 통해 account-level progression 신호를 보일 수 있다",
        status: "Pending (Phase B, exploratory)",
        basis: "Portfolio Rotation의 증명이 아니라 존재 가능성 탐색. Union proxy만으로 확정하지 않음." }
    ],

    /* Section 4 — 분석 질문의 발전 */
    questionEvolution: [
      { step: 1, q: "260은 성장 허들인가?",
        note: "레벨 251/260/262/281 코호트 추적 → 대부분 정체" },
      { step: 2, q: "260 이후 왜 progression이 감소하는가?",
        note: "sampling bias 발견 → 모멘텀 코호트(climb) 추가 → 오르던 캐릭터도 260 도달 후 progression 급감" },
      { step: 3, q: "하지만 Character Parker ≠ Account Churn",
        note: "유니온 구조상 그 캐릭터가 멈춰도 계정은 활성일 수 있음. 공개 API로 다른 캐릭터 연결 불가" },
      { step: 4, q: "어떤 캐릭터가 이벤트 종료 후에도 progression을 유지하는가?",
        note: "= 현재 Primary Research Question. Phase B에서 prospective로 검증" }
    ],

    /* Section 5 — 2-layer framework */
    framework: {
      layer1: {
        name: "Layer 1 · Character-level Progression",
        desc: "이벤트에서 육성한 그 캐릭터가 종료 후에도 progression을 지속하는가",
        axes: [
          { key: "Level",  meaning: "grind / time-oriented progression" },
          { key: "HEXA",   meaning: "6차 progression 자원 투자 (Sol Erda / Fragment — 거래 가능, 접속과 동일시 안 함)" },
          { key: "Symbol", meaning: "장기 / 일일형 progression 시스템 참여 proxy" },
          { key: "CP",     meaning: "위 투자가 실제 스펙 성장으로 전환됐는가" }
        ]
      },
      layer2: {
        name: "Layer 2 · Account-level Context",
        desc: "그 캐릭터가 파킹돼도 계정 전체 progression이 유지되는가",
        axes: [
          { key: "Union", meaning: "account-level progression proxy · account retention 직접 지표 아님" }
        ],
        warnings: [
          "character inactivity ≠ account churn",
          "동일 계정의 다른 캐릭터 progression은 공개 API로 연결 불가",
          "Union flat ≠ inactivity (특히 high-Union 계정: 브레이크포인트 포화)"
        ]
      }
    },

    /* 참고 — 확보된 데이터 규모 (real) */
    assets: {
      referencePanel: { ocids: 1958, milestones: 6, rows: 11748,
        span: "2025-06 ~ 2026-09", seasons: ["ASSEMBLE 2025 여름", "CROWN 2025 겨울", "OVERDRIVE 2026 여름"] },
      part1: { cohorts: 5, dailyRows: 70000, observationDays: 35 },
      smoke: { chars: 16, calls: 192,
        checked: ["stat 파서", "hexamatrix raw core 배열", "symbol 파서", "union 파서", "empty/ok 구분", "resume/skip"] ,
        result: "전부 통과" }
    }
  },

  /* ------------------------------------------------------------------ *
   * PENDING — Phase B (이벤트 종료 후). 미래 데이터 없음. 상태만.
   * ------------------------------------------------------------------ */
  pending: {
    phaseB: {
      status: "Pending — Post-event data collection",
      pilotN: 285,
      pilotBreakdown: "260명 (provisional-label stratified) + 25명 event_period_new (별도 exploratory segment)",
      trackedAxes: ["Level", "HEXA", "Symbol", "CP", "Union"],
      eventEnd: "2026-09-16",
      timeline: [
        { label: "Event End", date: "2026-09-16", offset: "D0",  done: false },
        { label: "+7",        date: "2026-09-23", offset: "+7d",  done: false },
        { label: "+14",       date: "2026-09-30", offset: "+14d", done: false },
        { label: "+28",       date: "2026-10-14", offset: "+28d", done: false },
        { label: "+56",       date: "2026-11-11", offset: "+56d", done: false }
      ],
      waves: [
        { name: "Wave 1", when: "2026-10-15 이후", scope: "Phase A retro + +7/+14/+28", calls: "~9,120", done: false },
        { name: "Wave 2", when: "2026-11-12 이후", scope: "+56", calls: "~1,425", done: false }
      ],
      /* +28/+56 데이터 확보 후 채울 카드. 지금은 전부 pending. */
      outcomeCards: [
        { axis: "Level",  question: "post-event ΔLevel 지속?",              status: "pending" },
        { axis: "HEXA",   question: "post-event 6차 자원 투자 지속?",        status: "pending" },
        { axis: "Symbol", question: "post-event 장기 progression 참여 지속?", status: "pending" },
        { axis: "CP",     question: "post-event 스펙 성장 전환?",            status: "pending" },
        { axis: "Union",  question: "character 파킹 시 account proxy 움직임?", status: "pending" }
      ],
      /* state 분류 결과 카드 — Phase B outcome 전까지 provisional, 수치 없음 */
      stateCards: [
        { name: "High-intensity Character Persistent", status: "pending" },
        { name: "Low-intensity Character Persistent",  status: "pending" },
        { name: "Seasonal Character Parker",           status: "pending" },
        { name: "Dormant-like Character",              status: "pending" },
        { name: "Portfolio Rotation candidate (exploratory)", status: "pending" },
        { name: "Reactivated Character (retrospective dim.)", status: "pending" }
      ]
    }
  },

  /* ------------------------------------------------------------------ *
   * Section 7 — PM Decision (가설·제안, 검증 전)
   * ------------------------------------------------------------------ */
  pm: {
    businessQuestion: "이벤트에 강하게 반응하지만 평시에 progression이 끊기는 Seasonal character를 어떻게 지속 가능한 저강도 progression으로 전환할 것인가?",
    conversionFlow: [
      { key: "seasonal",   label: "High-intensity Seasonal Growth", note: "방학 = 시간 여유 + 성장 부스트" },
      { key: "lowintense", label: "Low-intensity Sustainable Progression", note: "평시 = 짧은 세션으로도 progression 유지" },
      { key: "reactivate", label: "Next Seasonal Re-activation", note: "다음 시즌 재유입" }
    ],
    proposedActions: [
      { name: "Short-session growth support",  idea: "제한된 플레이 시간에서도 의미 있는 progression이 가능하도록 하는 지원", status: "PM Hypothesis — 미검증" },
      { name: "Progression onboarding",        idea: "260 직후 6차/HEXA/심볼 등 상시 progression 시스템 경험 유도", status: "PM Hypothesis — 미검증" },
      { name: "Post-event transition rewards", idea: "이벤트 종료 직후 구간을 critical window로 보고 전환 보상 설계", status: "PM Hypothesis — 미검증" }
    ],
    disclaimer: "위 action은 실험 결과가 아니라 분석에서 도출한 PM 가설이다. 실제 효과는 A/B 등 별도 검증이 필요하며, 넥슨 내부 KPI·이벤트 의도를 단정하지 않는다."
  }
};

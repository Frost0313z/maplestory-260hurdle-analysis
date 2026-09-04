# 메이플스토리 여름 성장 이벤트 — "260 허들 돌파율" 분석

넥슨 오픈 API 랭킹 스냅샷으로 레벨 260 구간의 성장·정착·이탈 패턴과
2026 여름 성장 이벤트의 효과를 분석하는 시계열 프로젝트 (코디세이 부트캠프 AI 데이터 분석 미션).

## 현재 상태

**Part 1** (260 허들) 수집·분석·리포트 완료 → **[REPORT.md](REPORT.md)**.
**Part 2** (260 이후 상시 progression 전환) 설계 단계 — `collect_panel.py` 준비 완료, 대량 수집 전.

Part 1 핵심 결과:
- 랭킹 통합 3M위 근방(Lv.251~262) 캐릭터는 35일간 99% 이상이 레벨을 전혀 올리지 않음
- 실제로 오르던 인구(`climb`, 모멘텀 스크리닝)조차 260 도달 18%, 그중 **260→261 전환율이 매우 낮음**
  (post-260 관측창 ≥14일 확보해도 13% — 관측 기간 부족 아님, robustness check 통과), 270+ 도달 0명
- 260 정지의 상당수는 실패가 아닐 수 있음 (유니온 파킹 / 하이퍼버닝 목표점 / BEYOND 지정 분기) —
  단 능동적 파킹과 계정 이탈은 스냅샷으로 구분 불가
- 활동성은 레벨대(251→281)가 아니라 전투력(17만→3천만)을 따라 9%→64%; 실질 성장률로 좁히면 251·260·262 = 5~10%, 281만 32%

Part 2 Business Question: *"방학 이벤트에서 성장한 캐릭터 중 누가 260 이후 상시 progression으로
전환되는가? 그 차이를 조기 식별해 Seasonal User를 Core User로 전환할 개입은?"* (REPORT.md §14)

| 문서 | 내용 |
|---|---|
| [REPORT.md](REPORT.md) | 분석 리포트 (질문·데이터·결과 Q1~Q3·인사이트·결론·한계·AI 로그) |
| [메이플스토리_이벤트분석_계획문서.md](메이플스토리_이벤트분석_계획문서.md) | 분석 질문·가설, 코호트 정의, 지표 정의, 한계점 (왜/무엇) |
| [메이플스토리_이벤트분석_스펙문서.md](메이플스토리_이벤트분석_스펙문서.md) | API 스펙, CSV 스키마, 함수 시그니처, 노트북·시각화·리포트 구조 (어떻게) |

## 산출물

```
collect.py            # Part 1 수집 (일간 소급, (캐릭터,날짜) 단위 재개, climb 모멘텀 스크리닝)
analysis.ipynb        # Part 1 정제·시계열 분석·시각화
REPORT.md             # 분석 리포트 (§14 = Part 2 방향)
data/cohort_*.csv     # 5코호트 원본 (approach/at260/past260/burnend/climb, 계 70,000행)
data/cohort_climb_roster.txt              # climb 스크리닝 통과 명단 캐시
data/breakthrough_retention_summary.csv   # 코호트×날짜 집계
data/stagnation_pooled.csv                # 정체 시작 레벨 (4코호트 풀링)
images/01~06*.png     # 돌파 곡선 / 8일 리텐션 / 정체 지도 / 성장 궤적 / 전투력 성장 / climb 궤적
requirements.txt

# Part 2 (설계 단계, 대량 수집 전)
endpoint_feasibility_probe.md   # 캐릭터 endpoint 소급 범위 실측 (2023-12-22, ranking 4개월과 다름)
panel_config.py                 # 이벤트 일정·스냅샷 격자·endpoint (코드에서 분리, 검토용)
collect_panel.py                # 2025~2026 longitudinal 패널 수집 (--dry-run 지원, classification 로직 없음)
build_pilot_sample.py           # panel_basic 궤적 → provisional label → data/pilot_targets.csv
analysis/retrospective_eda.py   # Parker vs Persistent 후보 비교 (호출 0)
analysis/burstiness_robustness.py  # concentration 산식 robustness·circularity 검증 (호출 0)
docs/phase_b_analysis_plan.md    # Phase B 분석계획 FREEZE (RQ·outcome·H1~H5·features·states·claim boundary)
docs/data_collection_checklist.md # Wave 1/2 실행 전·후 체크리스트 + V1~V11 validation
report/                         # interactive 포트폴리오 리포트 (static HTML, index.html + data.js + render.js)
```

## 실행

```bash
pip install -r requirements.txt
cp .env.example .env          # .env 에 NXOPEN_API_KEY 값 채우기 (커밋 금지, .gitignore 처리됨)
python collect.py            # data/cohort_*.csv 생성/이어쓰기 (~6시간, live 키 1회)
jupyter nbconvert --to notebook --execute --inplace analysis.ipynb
```

> 키는 `.env` 파일 대신 셸 환경변수(`$env:NXOPEN_API_KEY = "..."`)로 줘도 됩니다.

### 포트폴리오 리포트 (interactive HTML)

빌드 불필요. `report/index.html` 을 브라우저로 열면 됩니다 (desktop 권장).

```bash
# 그냥 열기
start report/index.html          # Windows  (mac: open / linux: xdg-open)
# 또는 로컬 서버 (file:// 캐시 이슈 없이)
python -m http.server -d report 8000   # → http://localhost:8000
```

- 모든 수치는 `report/data.js` 한 곳에 모여 있습니다. `real` = 확보된 실제 분석 결과,
  `pending` = Phase B(이벤트 종료 후) 미수집 영역(상태만, 미래 수치 없음).
- Phase B 결과가 나오면 `data.js` 의 `pending.*` 를 실제 값으로 채우면 placeholder 가 자동으로 대체됩니다.

## 데이터 출처 · 라이선스

- 출처: [NEXON Open API](https://openapi.nexon.com/) — 메이플스토리 캐릭터/랭킹 정보
- NEXON Open API 이용약관 준수. 비상업적 포트폴리오 용도, 출처 표기. 재배포·상업 이용 전 약관 재확인.

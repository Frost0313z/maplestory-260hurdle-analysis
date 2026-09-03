# 메이플스토리 여름 성장 이벤트 — "260 허들 돌파율" 분석

넥슨 오픈 API 랭킹 스냅샷으로 레벨 260 구간의 성장·정착·이탈 패턴과
2026 여름 성장 이벤트의 효과를 분석하는 시계열 프로젝트 (코디세이 부트캠프 AI 데이터 분석 미션).

## 현재 상태

수집·분석·리포트 완료. **[REPORT.md](REPORT.md)** 참고.

핵심 결과 요약:
- 랭킹 통합 3M위 근방(Lv.251~262) 캐릭터는 35일간 99% 이상이 레벨을 전혀 올리지 않음
- 정지 캐릭터는 레벨 경계에서 진행도 ≈0으로 멈춤 → 난이도 장벽보다 **유니온 부캐 파킹**의 서명
- 성수기에도 260 돌파율 ~0.3% — 버닝은 계정당 1캐릭터 한정이라 기존 캐릭터엔 효과 없음
- 활동성은 레벨대(251→281)가 아니라 전투력(17만→3천만)을 따라 9%→64%로 상승

| 문서 | 내용 |
|---|---|
| [REPORT.md](REPORT.md) | 분석 리포트 (질문·데이터·결과 Q1~Q3·인사이트·결론·한계·AI 로그) |
| [메이플스토리_이벤트분석_계획문서.md](메이플스토리_이벤트분석_계획문서.md) | 분석 질문·가설, 코호트 정의, 지표 정의, 한계점 (왜/무엇) |
| [메이플스토리_이벤트분석_스펙문서.md](메이플스토리_이벤트분석_스펙문서.md) | API 스펙, CSV 스키마, 함수 시그니처, 노트북·시각화·리포트 구조 (어떻게) |

## 산출물

```
collect.py            # 넥슨 API 수집 스크립트 (일간 소급, (캐릭터,날짜) 단위 재개)
analysis.ipynb        # 정제·시계열 분석·시각화 (셀 1~9)
REPORT.md             # 분석 리포트
data/cohort_*.csv     # 4코호트 원본 (approach/at260/past260/burnend, 계 59,500행)
data/breakthrough_retention_summary.csv   # 코호트×날짜 집계
data/stagnation_pooled.csv                # 정체 시작 레벨 (4코호트 풀링)
images/01~04*.png     # 돌파 곡선 / 리텐션 / 정체 지도 / 성장 궤적
requirements.txt
```

## 실행

```bash
pip install -r requirements.txt
cp .env.example .env          # .env 에 NXOPEN_API_KEY 값 채우기 (커밋 금지, .gitignore 처리됨)
python collect.py            # data/cohort_*.csv 생성/이어쓰기 (~6시간, live 키 1회)
jupyter nbconvert --to notebook --execute --inplace analysis.ipynb
```

> 키는 `.env` 파일 대신 셸 환경변수(`$env:NXOPEN_API_KEY = "..."`)로 줘도 됩니다.

## 데이터 출처 · 라이선스

- 출처: [NEXON Open API](https://openapi.nexon.com/) — 메이플스토리 캐릭터/랭킹 정보
- NEXON Open API 이용약관 준수. 비상업적 포트폴리오 용도, 출처 표기. 재배포·상업 이용 전 약관 재확인.

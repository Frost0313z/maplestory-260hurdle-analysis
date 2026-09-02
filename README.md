# 메이플스토리 여름 성장 이벤트 — "260 허들 돌파율" 분석

넥슨 오픈 API 랭킹 스냅샷으로 레벨 260 구간의 성장·정착·이탈 패턴과
2026 여름 성장 이벤트의 효과를 분석하는 시계열 프로젝트 (코디세이 부트캠프 AI 데이터 분석 미션).

## 현재 상태

계획·스펙 확정 단계. 데이터 수집·분석은 미착수.

| 문서 | 내용 |
|---|---|
| [메이플스토리_이벤트분석_계획문서.md](메이플스토리_이벤트분석_계획문서.md) | 분석 질문·가설, 코호트 정의, 지표 정의, 한계점 (왜/무엇) |
| [메이플스토리_이벤트분석_스펙문서.md](메이플스토리_이벤트분석_스펙문서.md) | API 스펙, CSV 스키마, 함수 시그니처, 노트북·시각화·리포트 구조 (어떻게) |

## 예정 산출물

```
collect.py            # 넥슨 API 수집 스크립트
analysis.ipynb        # 정제·시계열 분석·시각화
REPORT.md             # 분석 리포트
data/                 # 코호트 CSV (공개 랭킹 데이터)
images/               # 시각화 4종
requirements.txt
```

## 실행 (구현 후)

```bash
pip install -r requirements.txt
cp .env.example .env          # .env 에 NXOPEN_API_KEY 값 채우기 (커밋 금지, .gitignore 처리됨)
python collect.py            # data/cohort_*.csv 생성
jupyter notebook analysis.ipynb
```

> 키는 `.env` 파일 대신 셸 환경변수(`$env:NXOPEN_API_KEY = "..."`)로 줘도 됩니다.

## 데이터 출처 · 라이선스

- 출처: [NEXON Open API](https://openapi.nexon.com/) — 메이플스토리 캐릭터/랭킹 정보
- NEXON Open API 이용약관 준수. 비상업적 포트폴리오 용도, 출처 표기. 재배포·상업 이용 전 약관 재확인.

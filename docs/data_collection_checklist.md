# Phase B — Data Collection Checklist

작성: 2026-09-04 · 대상: pilot 수집 (`docs/phase_b_analysis_plan.md` FREEZE 기준)
목적: **collection readiness 만.** 분석 feature/state 정의는 변경 없음.

수집 스크립트: `collect_panel.py` (`--tier pilot --endpoints pilot`) · 설정: `panel_config.py`
표본: `data/pilot_targets.csv` — 285명 (260 pilot + 25 `event_period_new`)
산출 파일: `data/panel_basic.csv` · `data/panel_status.csv` · `data/panel_raw_{stat,hexamatrix,symbol,union}.jsonl`

> 코드 수정 이력: `collect_panel.py` basic append 를 `outcome not in RETRYABLE` 로 가드
> (일시 실패 행이 resume 시 중복 append 되는 것 방지). feature/state 정의 불변.

---

## 1. Milestone 기록표 (실행 시마다 채움)

| 필드 | Phase A · 2025-06-12 | Phase A · 2025-12-12 | Phase A · 2026-06-12 | W1 · 2026-09-15 | W1 · 2026-09-23 | W1 · 2026-09-30 | W1 · 2026-10-14 | W2 · 2026-11-11 |
|---|---|---|---|---|---|---|---|---|
| collection date (실행일) | | | | | | | | |
| target snapshot date | 2025-06-12 | 2025-12-12 | 2026-06-12 | 2026-09-15 | 2026-09-23 | 2026-09-30 | 2026-10-14 | 2026-11-11 |
| target n | 285 | 285 | 285 | 285 | 285 | 285 | 285 | 285 |
| endpoints | stat·hexamatrix·symbol·union | 〃 | 〃 | basic·stat·hexamatrix·symbol·union | 〃 | 〃 | 〃 | 〃 |
| expected API calls | ~1,140 (basic 0, Stage1 완료) | ~1,140 | ~1,140 | ~1,425 | ~1,425 | ~1,425 | ~1,425 | ~1,425 |
| actual API calls (stdout "총 API 호출") | | | | | | | | |
| success count (`outcome=ok`) | | | | | | | | |
| empty/null count (`outcome=empty`) | | | | | | | | |
| HTTP 400 (`outcome=http_400`) | | | | | | | | |
| HTTP 429 (`outcome=http_429_giveup`) | | | | | | | | |
| retries (총 API 호출 − 신규 status 행) | | | | | | | | |
| duplicate rows (§3-V1) | | | | | | | | |
| missing characters (§3-V2) | | | | | | | | |
| resume/skip validation (§3-V3) | | | | | | | | |
| raw response preservation (§3-V4) | | | | | | | | |
| final CSV / JSONL row count | | | | | | | | |

- Phase B `+56`(2026-11-11)은 **Wave 2** — 2026-11-12 이후에만 실행 가능(T-1).
- `event_period_new` 25명은 Phase A 초기 시점에 `empty` 가 정상 (그 시점 미존재). "missing" 아님.
- 합계 예상: Wave 1 ≈ 8,900~9,120 콜 · Wave 2 ≈ 1,425 콜.

### 지표 산출 방법 (전부 `data/` 파일에서, API 호출 없음)

```bash
# outcome 카운트 (특정 snapshot date, endpoint)
python - <<'PY'
import csv, collections
D="2026-09-15"; c=collections.Counter()
for r in csv.DictReader(open("data/panel_status.csv",encoding="utf-8-sig")):
    if r["date"]==D: c[(r["endpoint"],r["outcome"])]+=1
print(dict(c))
PY
```
- **actual API calls / retries**: 실행 stdout 의 `총 API 호출: N` 와 `재시도 남음(일시 실패): M`.
  retries ≈ N − (이 실행에서 새로 추가된 `panel_status` 행 수).
- **final row count**: `wc -l data/panel_basic.csv` · `wc -l data/panel_raw_*.jsonl`.

---

## 2. Wave 1 — 실행 전 체크리스트 (2026-10-15 이후)

- [ ] 오늘 날짜 ≥ 2026-10-15 (그래야 `+28` = 2026-10-14 이 T-1 이내).
- [ ] `git status` clean, 최신 `main` (`panel_config.py` / `collect_panel.py` / `pilot_targets.csv` 반영).
- [ ] `NXOPEN_API_KEY` 설정 확인 (`.env` 또는 env). `live_` 키.
- [ ] `data/pilot_targets.csv` 285행, `provisional_label` 5종, 중복 ocid 0 (아래).
      ```bash
      python -c "import csv;r=list(csv.DictReader(open('data/pilot_targets.csv',encoding='utf-8-sig')));import collections;print(len(r),collections.Counter(x['provisional_label'] for x in r),'dup',len(r)-len({x['ocid'] for x in r}))"
      ```
- [ ] **dry-run** 으로 계획 확인 (호출 0):
      ```bash
      python collect_panel.py --dry-run --sampling list --list-file data/pilot_targets.csv --tier pilot --endpoints pilot
      ```
      - `표본 ... 총 285 캐릭터` 확인.
      - `날짜 격자` 에 A_* 3개 + B_event_end/post7/post14/post28 가 나오고 `B_post56` 는 안 나옴(T-1 초과) 확인.
      - `이번 실행 호출 예상` 이 대략 8,900~9,120 범위인지 확인.
- [ ] 기존 `data/panel_*` 백업 (`cp data/panel_status.csv data/panel_status.bak` 등) — resume 문제 시 롤백용.
- [ ] Excel 등에서 `data/panel_*.csv` **열지 않기** (수집 중 파일 락 → 재시도 소요).
- [ ] 실행:
      ```bash
      nohup python -u collect_panel.py --sampling list --list-file data/pilot_targets.csv \
        --tier pilot --endpoints pilot --yes >> panel_collect_run.log 2>&1 &
      ```
- [ ] 완료 시 stdout 마지막에 `재시도 남음(일시 실패): 0` 확인. 0 아니면 **같은 명령 재실행**(resume).

## 2b. Wave 1 — 실행 후 validation 체크리스트

각 항목 PASS/FAIL 기록. FAIL 시 원인·조치 메모.

- [ ] **V1 · 동일 character/date/endpoint 중복** — `panel_status` 에서 (ocid,date,endpoint) 가
      **둘 다 terminal outcome** 인 키가 0. (retryable 1 + terminal 1 조합은 정상.) `panel_basic`
      의 (ocid,date) 중복 0. `panel_raw_*` 의 (ocid,date) 중복 0.
      ```bash
      python - <<'PY'
      import csv,collections,json
      TERM={"ok","empty","http_400","http_404"}
      s=collections.defaultdict(list)
      for r in csv.DictReader(open("data/panel_status.csv",encoding="utf-8-sig")):
          s[(r["ocid"],r["date"],r["endpoint"])].append(r["outcome"])
      bad=[k for k,v in s.items() if sum(o in TERM for o in v)>1]
      print("V1 status dup(terminal x2):",len(bad))
      b=collections.Counter((r["ocid"],r["date"]) for r in csv.DictReader(open("data/panel_basic.csv",encoding="utf-8-sig")))
      print("V1 panel_basic dup:",sum(1 for v in b.values() if v>1))
      for ep in ("stat","hexamatrix","symbol","union"):
          c=collections.Counter((json.loads(l)["ocid"],json.loads(l)["date"]) for l in open(f"data/panel_raw_{ep}.jsonl",encoding="utf-8"))
          print(f"V1 raw_{ep} dup:",sum(1 for v in c.values() if v>1))
      PY
      ```
- [ ] **V2 · pilot 285명 coverage** — 각 (snapshot date × endpoint) 에 대해 285 ocid 전부
      `panel_status` 에 등장하고, terminal outcome 을 가짐. retryable-only 로 남은 ocid = 0.
      ```bash
      python - <<'PY'
      import csv,collections
      TERM={"ok","empty","http_400","http_404"}
      want={r["ocid"] for r in csv.DictReader(open("data/pilot_targets.csv",encoding="utf-8-sig"))}
      seen=collections.defaultdict(set)
      for r in csv.DictReader(open("data/panel_status.csv",encoding="utf-8-sig")):
          if r["outcome"] in TERM: seen[(r["date"],r["endpoint"])].add(r["ocid"])
      for k,v in sorted(seen.items()):
          miss=want-v
          if miss: print("V2 MISSING",k,len(miss))
      print("V2 done" )
      PY
      ```
- [ ] **V3 · resume/skip 동작** — Wave 1 완료 직후 **동일 명령 재실행 (dry-run)** → `이번 실행
      호출 예상 = 0`, `이미 완료(재개 스킵)` 가 전체 task 와 일치.
- [ ] **V4 · raw response 보존** — `panel_raw_{stat,hexamatrix,symbol,union}.jsonl` 존재. `ok` 행마다
      `json` 필드에 원본 body(빈 dict 아님). `empty` 행은 `json` 에 null/`[]` 있어도 됨. 행 수 =
      해당 endpoint 의 `panel_status` (ok+empty) 수와 일치.
- [ ] **V5 · Phase A ↔ Phase B key join** — join key = `(ocid, snapshot_date)`. `event_period_new`
      제외 260명이 A_overdrive_pre(2026-06-12) 와 B_event_end(2026-09-15) 양쪽에 존재하는가
      (endpoint 별). 결측이면 어느 쪽/누구인지 목록화.
      ```bash
      python - <<'PY'
      import csv,collections
      TERM={"ok","empty"}
      lab={r["ocid"]:r["provisional_label"] for r in csv.DictReader(open("data/pilot_targets.csv",encoding="utf-8-sig"))}
      core={o for o,L in lab.items() if L!="event_period_new"}
      has=collections.defaultdict(set)
      for r in csv.DictReader(open("data/panel_status.csv",encoding="utf-8-sig")):
          if r["outcome"] in TERM: has[(r["date"],r["endpoint"])].add(r["ocid"])
      for ep in ("stat","hexamatrix","symbol","union"):
          a=has[("2026-06-12",ep)]&core; b=has[("2026-09-15",ep)]&core
          print(f"V5 {ep}: A∩core={len(a)} B∩core={len(b)} joinable={len(a&b)}  A-only={len(a-b)} B-only={len(b-a)}")
      PY
      ```
- [ ] **V6 · HEXA raw core array 손실 여부** — `panel_raw_hexamatrix.jsonl` 의 `ok` 행마다
      `json.character_hexa_core_equipment` 가 list 이고, 원소에 `hexa_core_name` / `hexa_core_type`
      / `hexa_core_level` 3필드 존재. `hexa_core_type` 값이 {스킬 코어, 마스터리 코어, 강화 코어,
      공용 코어} 안에 있는지. 예상치 못한 값 있으면 목록화(파서에 반영).
      ```bash
      python - <<'PY'
      import json,collections
      t=collections.Counter(); bad=0; nrows=0
      for l in open("data/panel_raw_hexamatrix.jsonl",encoding="utf-8"):
          j=json.loads(l)
          if j["outcome"]!="ok": continue
          nrows+=1; cores=j["json"].get("character_hexa_core_equipment")
          if not isinstance(cores,list): bad+=1; continue
          for c in cores:
              if not all(k in c for k in ("hexa_core_name","hexa_core_type","hexa_core_level")): bad+=1
              t[c.get("hexa_core_type")]+=1
      print("V6 ok rows",nrows,"malformed",bad,"types",dict(t))
      PY
      ```
- [ ] **V7 · Symbol parsing consistency** — `panel_raw_symbol.jsonl` `ok` 행마다 `json.symbol` 이
      list, 원소에 `symbol_name` / `symbol_level` 존재. `symbol_level` 은 int, 0~수십 범위.
      아케인/어센틱 접두 분포 확인. 시점 간 같은 ocid 의 심볼 개수 급변(±5↑) 건수 = 플래그 목록.
- [ ] **V8 · CP / stat field parsing consistency** — `panel_raw_stat.jsonl` `ok` 행마다
      `json.final_stat` 이 44개 근처 list, `stat_name=="전투력"` 원소 1개 존재, `stat_value` 가
      int 파싱 가능. `rec.combat_power` 가 그 값과 일치. `combat_power` None/음수 건수 목록화.
      ```bash
      python - <<'PY'
      import json
      n=miss=neg=mismatch=0
      for l in open("data/panel_raw_stat.jsonl",encoding="utf-8"):
          j=json.loads(l)
          if j["outcome"]!="ok": continue
          n+=1; fs=j["json"].get("final_stat") or []
          cp=[x for x in fs if x.get("stat_name")=="전투력"]
          if not cp: miss+=1; continue
          try: v=int(cp[0]["stat_value"])
          except: miss+=1; continue
          if v<0: neg+=1
          if j.get("combat_power") not in (v,None) : mismatch+=1
      print(f"V8 ok {n} / 전투력 missing {miss} / negative {neg} / rec mismatch {mismatch}")
      PY
      ```
- [ ] **V9 · Union baseline/post join consistency** — 260 core 캐릭터가 `union` 에서
      2026-06-12 · 2026-09-15 · +28 전부 terminal outcome. `union_level` 정수, 시점 간 감소
      건수(= 이상치 후보) 목록화. `union_artifact_level` 필드 존재 확인.
- [ ] **V10 · missingness 편향** — `empty` + `http_400` + retryable-남음 을 "관측 실패" 로 보고,
      `provisional_label` 별 / `cohort` 별 실패율을 표로. 특정 label/cohort 에 실패가 몰리면
      (예: 한 그룹만 30%+) 분석 시 층별 결측 보정 필요 → 메모.
      ```bash
      python - <<'PY'
      import csv,collections
      TERM_OK={"ok"}; lab={};coh={}
      for r in csv.DictReader(open("data/pilot_targets.csv",encoding="utf-8-sig")):
          lab[r["ocid"]]=r["provisional_label"]; coh[r["ocid"]]=r["cohort"]
      tot=collections.Counter(); fail=collections.Counter()
      last={}
      for r in csv.DictReader(open("data/panel_status.csv",encoding="utf-8-sig")):
          last[(r["ocid"],r["date"],r["endpoint"])]=r["outcome"]
      for (oc,d,ep),o in last.items():
          if oc not in lab: continue
          tot[lab[oc]]+=1
          if o not in TERM_OK: fail[lab[oc]]+=1
      for L in sorted(tot): print(f"V10 label {L:18} fail {fail[L]}/{tot[L]} = {fail[L]/tot[L]:.1%}")
      PY
      ```
- [ ] 기록표(§1) Wave 1 열 전부 채움. `docs/` 에 이 파일 커밋.

---

## 3. 지정 validation 정의 (요약)

| ID | 이름 | PASS 조건 |
|---|---|---|
| V1 | 동일 character/date/endpoint 중복 | terminal outcome 2개인 status 키 0, panel_basic·raw JSONL (ocid,date) 중복 0 |
| V2 | pilot 285명 coverage | 각 (snapshot date × endpoint) 에 285 ocid 전부 terminal, retryable-only 잔여 0 |
| V3 | resume/skip validation | 완료 후 동일 명령 dry-run → 이번 실행 0콜 |
| V4 | raw response preservation | invest 4종 JSONL 존재, ok 행 `json` 채워짐, 행수 = status(ok+empty) |
| V5 | Phase A ↔ Phase B key join | `(ocid, date)` 로 core 260명이 2026-06-12 ↔ 2026-09-15 join 가능, 결측 목록화 |
| V6 | HEXA raw core array 손실 | ok 행마다 core list + name/type/level 3필드, type 값 4종 이내 |
| V7 | Symbol parsing consistency | ok 행마다 symbol list + name/level, level int, 개수 급변 플래그 |
| V8 | CP / stat field parsing consistency | 전투력 원소 1개, int 파싱, `combat_power` 일치, None/음수 목록화 |
| V9 | Union baseline/post join consistency | core 260명이 pre/T0/+28 전부 terminal, union_level 정수·감소 목록화 |
| V10 | missingness 편향 | label/cohort 별 관측 실패율 표, 특정 그룹 편중 시 메모 |

---

## 4. Wave 2 — 실행 전 체크리스트 (2026-11-12 이후)

- [ ] 오늘 날짜 ≥ 2026-11-12 (`+56` = 2026-11-11 이 T-1 이내).
- [ ] Wave 1 이 §2b V1~V10 전부 PASS 로 마감됨 (FAIL 미해결 시 Wave 2 보류).
- [ ] `git` 최신, 백업 (`cp data/panel_*`).
- [ ] **dry-run**:
      ```bash
      python collect_panel.py --dry-run --sampling list --list-file data/pilot_targets.csv --tier pilot --endpoints pilot
      ```
      - `날짜 격자` 에 `B_post56` (2026-11-11) 가 나타나고 T-1 이내인지.
      - `이번 실행 호출 예상` ≈ 1,425 (285 × 5 endpoint). Phase A·W1 은 전부 `이미 완료` 로 skip.
- [ ] Excel 락 주의. 실행 (`nohup ... --yes >> panel_collect_run.log 2>&1 &`).
- [ ] stdout `재시도 남음: 0` 확인, 아니면 재실행.

## 4b. Wave 2 — 실행 후 validation 체크리스트

- [ ] **V1** (중복) — 2026-11-11 행 포함 재검.
- [ ] **V2** (coverage) — (2026-11-11 × 5 endpoint) 에 285 전부 terminal.
- [ ] **V3** (resume) — 완료 후 dry-run 0콜.
- [ ] **V4** (raw 보존) — `+56` invest 행이 각 JSONL 에 추가, `json` 채워짐.
- [ ] **V5b · full trajectory join** — core 260명이 `union`/`stat`/`hexamatrix`/`symbol` 각각에서
      `[2026-06-12, 2026-09-15, +7, +14, +28, +56]` 6시점 중 몇 시점 terminal 인지 분포.
      6/6 인 캐릭터 수, ≤4/6 인 캐릭터 목록 (분석 시 제외/보간 판단).
- [ ] **V6~V9** — 2026-11-11 스냅샷에 대해 재실행 (HEXA core / Symbol / CP / Union 파싱).
- [ ] **V10** (missingness 편향) — 6시점 완결율을 `provisional_label` / `cohort` 별로. 편중 메모.
- [ ] **V11 · panel_basic ↔ Phase B basic 연속성** — Stage 1 `panel_basic` 의 2026-09-02 와
      Wave 1 의 2026-09-15 basic 이 같은 ocid 에서 레벨 단조(감소 없음)인지. 감소 건 목록화.
- [ ] 기록표(§1) Wave 2 열 채움. 커밋.

---

## 5. Go / No-Go

**Wave 1 → 분석(+28 checkpoint) 진행 조건**
- V1 (중복) PASS · V2 (coverage) ≥ 99% (미달 ocid 목록화 후 사유 확인) · V4/V6/V8 파서 PASS.
- V10 에서 특정 label/cohort 실패율이 다른 그룹의 2배+ 이면 → 층별 결측 처리 계획 메모 후 진행.

**Wave 2 → 최종 분석 진행 조건**
- V5b 에서 6/6 완결 core 캐릭터가 분석 최소선(state 후보별 카운트 안정) 이상.
- V11 레벨 단조성 위반 0 (있으면 해당 ocid 결측 처리).

**No-Go (수집 중단·조사)**
- V1 에서 panel_basic/raw 중복 > 0 (resume 로직 결함) → 원인 파악 전 재수집 금지.
- HTTP 429 가 특정 시점에 대량 (`outcome=http_429_giveup` > 5%) → 레이트리밋, 시간 두고 재개.
- 특정 endpoint 가 한 snapshot date 에서 전부 `http_400` → 그 날짜/endpoint 소급 불가 가능성,
  `endpoint_feasibility_probe.md` 대조 후 milestone 조정 검토 (feature/state 정의는 불변).

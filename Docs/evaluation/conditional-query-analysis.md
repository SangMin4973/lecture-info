# Conditional Query Analysis

## Summary

| Query | GT Docs | Retrieved | Hit@10 | Recall@10 | Problem |
| --- | ---: | ---: | ---: | ---: | --- |
| EV-011 | 3 | 10 | 1.0 | 1.0000 | retrieval success |
| EV-012 | 2 | 10 | 0.0 | 0.0000 | dense semantic mismatch / reverse-condition search |
| EV-013 | 5 | 10 | 1.0 | 0.4000 | partial recall; top-k finds some relevant docs but misses full set |
| EV-014 | 5 | 10 | 1.0 | 0.4000 | partial recall; top-k finds some relevant docs but misses full set |
| EV-015 | 6 | 10 | 1.0 | 0.1667 | partial recall; top-k finds some relevant docs but misses full set |

## Details

### EV-011

- Query: Python프로그래밍을 선수과목으로 하는 강의를 알려줘
- Analyzer K: 10
- Required fields: 선수과목과수강요건
- Problem: retrieval success
- Missed relevant docs:
  - (none)

### EV-012

- Query: 데이터베이스를 먼저 들어야 하는 강의가 뭐가 있어?
- Analyzer K: 10
- Required fields: 선수과목과수강요건
- Problem: dense semantic mismatch / reverse-condition search
- Missed relevant docs:
  - 백엔드프레임워크 / 이승진 / 선수과목과수강요건
  - 백엔드프로그래밍 / 김선형 / 선수과목과수강요건

### EV-013

- Query: 퀴즈가 자주 있거나 정기적으로 있는 강의를 찾아줘
- Analyzer K: 10
- Required fields: 수업진행방식
- Problem: partial recall; top-k finds some relevant docs but misses full set
- Missed relevant docs:
  - 백엔드프레임워크 / 이승진 / 수업진행방식
  - 서버구축및형상관리 / 이승진 / 수업진행방식
  - 데이터사이언스입문 / 이상윤 / 수업진행방식

### EV-014

- Query: 팀 프로젝트나 조별 활동이 있는 강의를 알려줘
- Analyzer K: 10
- Required fields: (none)
- Problem: partial recall; top-k finds some relevant docs but misses full set
- Missed relevant docs:
  - 빅데이터실무 / 신하진 / 수업진행방식
  - 오픈소스SW개발 / 이상윤 / 수업진행방식
  - 디지털회로실험 / 정인철 / 강의평가

### EV-015

- Query: 별점이 5.0인 강의를 알려줘
- Analyzer K: 10
- Required fields: 강의평가
- Problem: partial recall; top-k finds some relevant docs but misses full set
- Missed relevant docs:
  - 임베디드시스템 / 이종현 / 강의평가
  - 프론트엔드프레임워크 / 이승진 / 강의평가
  - 디지털회로실험 / 정인철 / 강의평가
  - 머신러닝입문 / 홍성준 / 강의평가
  - 데이터사이언스입문 / 이상윤 / 강의평가

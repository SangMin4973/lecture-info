# Commit Rule

## 기본 원칙

- 하나의 commit에는 하나의 목적만 담는다.
- 코드 변경, 문서 변경, 데이터셋 변경, 실험 결과 변경은 가능하면 분리한다.
- baseline 기록용 commit에서는 동작 변경을 섞지 않는다.
- 생성 결과물이나 실행 로그는 필요한 경우에만 commit한다.

## Commit Message Format

```text
<type>: <summary>
```

예시:

```text
docs: record baseline v0 system
eval: add retrieval evaluation dataset
eval: add retrieval debug script
fix: apply analyzer k to retrieval
refactor: simplify chatbot initialization
```

## Type

- `docs`: 문서 작성/수정
- `eval`: evaluation dataset, metric, debug script
- `feat`: 사용자 기능 추가
- `fix`: 버그 수정
- `refactor`: 동작 변경 없는 구조 개선
- `chore`: 설정, 의존성, 기타 관리 작업

## 현재 작업 Commit 권장 순서

1. `docs: record current baseline system`
2. `eval: define evaluation dataset schema`
3. `eval: add baseline retrieval questions`
4. `eval: add retrieval debug script`

## 주의

- `eval/results/`의 실행 결과는 기본적으로 commit하지 않는다.
- `models/`, `venv/`, `node_modules/`는 commit하지 않는다.
- API key, token, `.env`는 절대 commit하지 않는다.


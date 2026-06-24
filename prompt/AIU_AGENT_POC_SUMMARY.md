# AI-Studio GenAI Agent POC — 최종 정리

> MLflow pyfunc 모델로 등록되어 KServe로 서빙되는 LangChain 기반 GenAI 에이전트.
> 이 문서는 프로젝트의 아키텍처, 설계 결정, 구현 상태를 정리한 것이다.
> 저장소: `park-jongmin88/aui-agent-poc` · 주 작업 브랜치: `agent_aiu_custom`

---


## 1. 개요

에이전트는 **에셋(asset) 모듈을 조립**해 동작한다. `agent.py`는 "무엇을 켤지" 선언하고 "순서대로 실행"만 하며, 실제 기능은 각 에셋(`assets/*.py`)에 들어있다.

핵심 실행 흐름은 다음과 같다.

1. **대화 시작** — client가 MLflow에서 프롬프트 목록을 받아 하나 고른다. (프롬프트 텍스트의 주인은 서버, client는 id만 선택 = "A원칙")
2. **질문 진입** — 질문 한 건이 서빙 진입점(`aiu_custom.predict.ModelWrapper`)으로 들어온다.
3. **보따리(ctx) 파이프라인** — `prompt → rag → tool → llm` 순서로 각 에셋이 ctx의 자기 칸만 채우며 통과한다.
4. **반환** — `{"aiu_output": "답변"}` 형태로 반환. Trace/Session 자동 기록.
5. **judge 사후 평가** — 대화 종료 시 한 번, 답변들을 LLM으로 채점한다.


## 2. 폴더 구조

```
config.py            설정 (ENABLED_ASSETS, MLFLOW_CONN, LLM_*, ASSET_CONN, JUDGE_CONN)
agent.py             등록 전용 (register_agent)
client.py            서빙 엔드포인트 호출 테스트용 대화 프로그램
requirements.txt     서빙 의존성 (버전 고정)
aiu_custom/          서빙되는 모델 본체
  ├── __init__.py
  ├── model_wrapper.py   ModelWrapper (load_context / predict / 파이프라인)
  └── predict.py         re-export (서빙 진입점)
assets/              에셋 모듈 모음 (기능 추가는 여기)
  ├── __init__.py        에셋 공통 규약 + ctx 생성/로더
  ├── prompt.py          [구현] MLflow Prompts 로드 (캐싱)
  ├── llm.py             [구현] LangChain 체인으로 답변 생성
  ├── rag.py             [목업] mocks/ json 검색 (Milvus 연결 TODO)
  ├── tool.py            [목업] mocks/ 가상 API 호출 (실제 연동 TODO)
  └── judge.py           [구현] 세션 사후 평가
mocks/               목업 데이터 (실제 연결 전 POC용)
  ├── rag_documents.json   딥러닝/ML/GenAI 문서 20건
  └── tool_apis.json       가상 API 8종
```


## 3. 핵심 설계 결정

### 3-1. 진입점 고정, 내용물 교체

서빙 컨테이너(`custom_server.py`)는 항상 같은 경로 `aiu_custom.predict.ModelWrapper`에서 모델을 찾는다. `predict.py`는 단 한 줄의 re-export(`from .model_wrapper import ModelWrapper`)다.

- **진입점(`predict.py`)은 고정** — 실제 코드가 바뀌어도 서빙이 찾는 자리는 변하지 않는다.
- **내용물(config / assets / mocks)은 교체** — 빌더는 config만 동적 생성하면 되고, ModelWrapper 코드는 여러 에이전트가 하나로 공유한다.

```
custom_server.py
   └─ aiu_custom.predict.ModelWrapper   ← 고정된 진입점
        └─ model_wrapper.py             ← 실제 로직 (바뀌어도 됨)
             ├─ config.py               ← 설정 (빌더가 교체)
             ├─ assets/                 ← 기능 (켜고 끔)
             └─ mocks/                  ← 데이터
```

### 3-2. config 분리로 순환 import 방지

설정을 `config.py`로 빼서 등록(`agent.py`)과 서빙(`aiu_custom`)이 같은 값을 참조한다. 순환 import가 없고, 양쪽이 일관된 설정을 본다.

### 3-3. 보따리(ctx) 방식 파이프라인

`ENABLED_ASSETS = ["prompt", "rag", "tool", "llm"]` (리스트 순서 = 실행 순서). judge는 사후 평가라 파이프라인 밖이므로 제외한다.

ctx는 에셋들이 순서대로 주고받는 "보따리"다.

```
ctx = { query, prompt_id, system_message, context, tools_result, answer, score }
```

각 에셋은 자기 칸만 채우고 다음 에셋에게 넘긴다. 검색(rag)·도구(tool)는 우리가 직접 채우고, LLM은 채워진 보조자료(prompt + context + tools)를 받아 답변만 작성한다.

에셋 공통 규약: 각 에셋은 `NAME`, `build(conn)`, `run(ctx, resource)`를 가진다.


## 4. custom_server.py 계약 (고정, 수정 불가)

- **입력**: `model_input["input"][0]` = `{query, system_message, llm_api_key, session_id, prompt_id, user_id, mode, turns}`, 그리고 `trace_id` 등.
- **출력**: 반드시 `{"aiu_output": ...}` 키를 포함해야 한다. 없으면 custom_server 측에서 `UnboundLocalError: log_data` 연쇄 오류가 난다 (서버 측 코드라 수정 불가).
- 정상 응답 형태: `{...,"output":{"aiu_output":"답변"}}`.
- 에러는 서버를 죽이지 않고 `{"aiu_output":"[AGENT ERROR]..."}`로 반환한다.

### 등록 규칙

- signature 금지 → `input_example`만 사용.
- pip 버전 고정 필수 (포탈이 `mlflow==` 패턴을 파싱함).
- `code_paths = ["aiu_custom", "config.py", "assets", "mocks"]` — 서빙 환경에서 import 가능하도록 패키지/설정 동봉.
- requirements: `mlflow==3.10.0, cloudpickle==3.1.2, langchain-openai==1.2.1, langchain==1.2.15, pandas==2.3.3, kserve==0.15.0`.
- 권장 Python: **3.11.9** (kserve 0.15.0 호환; 3.13은 kserve 설치 안 됨).
- 로컬 등록/테스트만 한다면 kserve는 빼고 설치 가능 (서빙 이미지에서만 필요).


## 5. 각 에셋 상세

### prompt ✅
MLflow Prompt Registry에서 `prompt_id`로 텍스트를 로드한다.
- **A원칙**: 프롬프트 텍스트의 주인은 서버, client는 id만 선택. client가 보낸 system_message는 무시.
- **캐싱**: 같은 prompt_id는 첫 호출만 `load_prompt`, 이후 메모리 재사용 (응답 지연 해결의 핵심).
- 로드 실패 시 `default_system` 폴백.
- 프롬프트 타입은 **text** (chat 아님). 별칭 `alias="production"`, URI는 `prompts:/<이름>@production`.

### llm ✅
LangChain 체인으로 답변 생성: `prompt | model | StrOutputParser()` (LCEL).
- `ChatOpenAI` + `ChatPromptTemplate` + `StrOutputParser`.
- **system 메시지 단일화**: context/tools_result를 하나의 system 메시지로 합친다. (system을 여러 개 보내면 Qwen 등 일부 모델이 400 BadRequest 반환)
- surrogate 정화(`_safe_text`) 포함.

### rag 🟡목업
질문 키워드로 문서를 검색해 `ctx["context"]`를 채운다.
- 목업: `mocks/rag_documents.json` (딥러닝/ML/GenAI 20건) 키워드 매칭.
- `_build_mock`/`_search_mock` vs `_build_milvus`/`_search_milvus`(TODO) 함수 분리.
- mode에 따라 분기만 하고, 출력 형태(문자열)는 동일.

### tool 🟡목업
질문에 맞는 도구(API)를 호출해 `ctx["tools_result"]`를 채운다.
- 목업: `mocks/tool_apis.json` (가상 API 8종: weather/datetime/calculator/gpu_status/model_registry/mlflow_experiment/dataset/training_job).
- `trigger_keywords` 매칭 → **매칭된 도구 전부 호출**.
- `_run_mock` vs `_run_real`(TODO, LLM function calling) 분리.

### judge ✅
세션이 끝나면 생성된 답변(들)을 평가한다.
- **파이프라인 밖**: 다른 에셋과 달리 매 대화가 아니라 세션 끝에 한 번 도는 사후 평가. `mode="judge"`로 트리거. ENABLED_ASSETS에 넣지 않는다.
- 진입점은 `run`이 아니라 별도 `evaluate(items, resource)`.
- **평가 방식**: LLM-as-a-judge. 생성용 LLM(Qwen)을 평가에도 재사용 (POC).
- **평가 기준** 각 1~5점: accuracy(정확성), helpfulness(도움됨), clarity(명확성) + reason.
- 결과: `{"per_turn": [...], "avg": {...}, "count": n}`.
- `_evaluate_mock`(고정 점수) vs `_evaluate_llm`(실제 LLM 호출) 분리.
- judge 응답은 JSON으로만 받도록 강제하고, 파싱 실패 시 0점 처리.
- 설정은 `config.JUDGE_CONN`으로 분리 (base_url/model이 None이면 생성 LLM 재사용).


## 6. 트레이스 / 세션 기록

LangChain `mlflow.langchain.autolog()` + 각 에셋 run의 `@mlflow.trace`로 보따리 흐름을 가시화한다.

```
agent_pipeline                  ← _run() (@mlflow.trace)
  └ asset.prompt   [CHAIN]
  └ asset.rag      [RETRIEVER]
  └ asset.tool     [TOOL]
  └ asset.llm      [CHAIN]      (+autolog RunnableSequence 중첩)
judge_session     [CHAIN]       (mode=judge 시 별도)
```

- LangChain autolog는 **LangChain 컴포넌트만** 자동 기록한다. rag/tool 목업은 순수 파이썬이라 수동 `@mlflow.trace`가 필요하다.
- **judge는 트레이스 대상이 아니다** — 사후 평가라 대화 흐름(보따리)을 찍는 트레이스와 성격이 다르며, 점수(평가 결과)로 남는다.
- **Session**: Sessions 탭은 metadata 표준키(`mlflow.trace.session`/`mlflow.trace.user`)를 읽는다 (mlflow 3.10). `update_current_trace`로 기록.


## 7. 프롬프트 ↔ 실험 관계 (참고)

MLflow는 프롬프트를 실험에 태그로 묶을 수 있다.
- `load_prompt`/`register_prompt`가 활성 run 안에서 호출되면 `PROMPT_EXPERIMENT_IDS_TAG_KEY` 태그로 실험에 연결된다.
- 저장은 전역, UI 표시만 실험별로 갈린다.
- `mlflow.genai.search_prompts()` (필터 없음)은 전역 전체를 가져온다 (현재 사용 중).
- 실험별 필터: `search_prompts(filter_string="experiment_id = '...'")`.
- UI URL: `<mlflow>/#/prompts` (전역), `<mlflow>/#/experiments/<id>/prompts` (실험별).
- 50개 초과 시 페이지네이션 필요.


## 8. LangChain 활용 현황과 방향

**현재**: `assets/llm.py`만 LangChain(ChatOpenAI 체인) 사용 + autolog. 즉 Models + Prompts + Chains(LCEL) 기본 3요소만.

**방향 (실제 연동 단계에서 전환)**:
- rag → LangChain **Retriever** (Milvus 연동 시)
- tool → LangChain **Tool / bind_tools** (function calling — LLM이 도구 스스로 선택)
- judge → LangChain 평가 체인 또는 `mlflow.genai.evaluate`와 조합

**필요성**: autolog가 검색·도구 호출까지 자동 트레이싱, 표준 인터페이스로 교체·조합 용이, 실제 연동 구조와 일치.

**지금 바로 안 가는 이유**: LLM 2회 호출로 느려짐(도구 선택 + 답변), 함수 시그니처 변환 필요, Qwen function calling 호환 확인 필요, mock/real 분리가 복잡해짐.


## 9. 주요 트러블슈팅 (해결됨)

### 응답 지연 (504 / 14초)
- 원인: prompt 에셋이 매 질문마다 `load_prompt`로 MLflow 왕복.
- 해결: **프롬프트 캐싱** (2번째 질문부터 건너뜀).
- 재서빙 직후 첫 요청 504 + "activator request timeout"은 **KServe 콜드 스타트**(scale-to-zero에서 파드 깨우는 중). 첫 요청만 실패하고 다음부터 정상이면 정상 동작이다. min-replica=1 또는 게이트웨이 타임아웃으로 완화 가능하나 인프라 설정 영역.
- 평상시 응답 속도 편차는 LLM 서버 부하에 따른 것 (코드 문제 아님).

### UnicodeEncodeError (surrogate, position 22-23)
- 원인: 서버 응답에 surrogate(깨진 이모지/유니코드)가 섞여 옴 → 출력(print) 단계에서 인코딩 실패. 답변은 서버에서 정상 생성되어 트레이스엔 남지만 화면 출력에서 터짐.
- 해결: client에 **3겹 + 전역 방어**
  1. 응답 수신 직후 이중 정화 (`encode/decode("utf-8","replace")`)
  2. `_extract_output`에서 문자열만 정화 (dict인 프롬프트 목록은 보존 — 정화로 문자열화하면 목록이 깨져 "기본" 고정되는 버그가 있었음)
  3. `sys.stdout.reconfigure(errors="replace")` + `print`를 `_safe_print`로 전역 교체
- client.py만 수정이라 재서빙 불필요.

### judge "결과 없음"으로 끝남
- 원인: client의 판단 코드가 모든 비정상 응답(에러 문자열, 빈 turns 등)을 "결과 없음" 하나로 뭉개서 진짜 원인을 숨김.
- 해결: 케이스별로 실제 응답 내용을 노출하도록 진단 강화 (에러 문자열 / 빈 turns / avg 없음 구분).


## 10. TODO (개발 예정)

1. **LLM 모델 선택** — `/v1/models`에서 목록 받아 고르기 (mode=list_models, model_id 추가) — 다음 1순위
2. **judge 평가모델 분리** — 현재 생성 LLM 재사용(POC) → 평가 전용 모델로 외부화 (self-bias 해소)
3. **rag 실제 연결** — Milvus, LangChain Retriever
4. **tool 실제 연동** — 실제 API + function calling, LangChain Tool 전환
5. **프롬프트 태그 필터** — experiment_id 필터로 에이전트/유저별 분리
6. **빌더 연동** — config를 포탈 DB로 외부화, user_id 인증, 시크릿 암호화 (장기 보류)

### 미정 (방향만)
- **LLM 관리**: 향후 포탈 DB에서 관리 (현재 config.py 하드코딩).
- **Prompt 관리**: (A) 사용자별/시스템별 포탈 DB or (B) 현재처럼 MLflow Prompts. 미정.
- **빌더**: config.py 동적 생성 방향.

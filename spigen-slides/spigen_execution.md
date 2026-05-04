# spigen-slides Execution Guide (v6)

## Step 3. 생성

승인된 구성을 그대로 Python 빌드 스크립트로 변환하고 실행한다.

v6 기본 방향:
- 운영용 = 디테일용 = 보고서형
- 각 슬라이드는 한 페이지 자기완결 설명
- 설명량이 부족해지면 구조형 컴포넌트보다 `slide()`를 우선한다

---

## 빌드 스크립트 템플릿

```python
import sys, shutil

# 빌더 복사
shutil.copy2("/Users/harugury/.agents/skills/spigen-slides/spigen_build.py",
             "/tmp/spigen_build.py")
sys.path.insert(0, "/tmp")
from spigen_build import SpigenBuilder

from spigen_build import SpigenBuilder, load_pid, save_pid

BUILD_NAME = "my_deck"

# 1. in-place 모드로 프레젠테이션 생성/수정
pid = load_pid(BUILD_NAME, "light")
b = SpigenBuilder("(PPT 제목)", theme="light", presentation_id=pid)
if pid is None:
    save_pid(BUILD_NAME, "light", b.pid)

# 2. 슬라이드 추가 (승인된 구성대로)
# 표지 — 항상 첫 번째, 생략 불가
# light: KPI 라이트 템플릿 cover 복사 / dark: 다크 템플릿 cover 복사
b.cover(
    title="(제목)",
    subtitle="(부제)")  # date 생략 시 오늘 날짜(yyyy. mm. dd.) 자동 입력

# 콘텐츠 슬라이드 — oid/idx 없이 호출, 순서대로 자동 배치
b.slide(
    heading="(슬라이드 제목)",
    body="(본문 내용\n• bullet\n• bullet)")

b.two_col(
    heading="(슬라이드 제목)",
    left_title="(왼쪽 제목)",
    left_body="(왼쪽 내용)",
    right_title="(오른쪽 제목)",
    right_body="(오른쪽 내용)")

# 3. 실행
ok = b.flush()
if ok:
    ppt_link = f"https://docs.google.com/presentation/d/{b.pid}/edit"
    print(f"빌드 완료: {ppt_link}")

    # ★ PID 안정성 게이트 (수정 단계 기본 강제)
    # python3 ~/.agents/skills/spigen-slides/spigen_pid_guard.py expect-stable BUILD_NAME light
    # python3 /tmp/build_<name>.py
    # python3 ~/.agents/skills/spigen-slides/spigen_pid_guard.py assert-stable BUILD_NAME light
    # 기존 PID가 있는데 링크가 바뀌면 실패 처리

    # ★ 검증은 별도 스킬에서 실행
    # 이 제작 스킬에서는 review gate를 자동 실행하지 않는다.
    # 완료 링크와 요약을 전달한 뒤 "2. 검증을 실행할까요?"를 묻는다.
    # 사용자가 검증을 요청하면 spigen-slides-review 스킬로 진행한다.
else:
    print("생성 실패")
```

수정 단계 필수 규칙:
- `clear_pid()` 사용 금지
- 같은 `BUILD_NAME` 작업은 같은 URL에 누적 수정
- 사용자가 새 덱을 명시적으로 요구한 경우에만 새 PID 허용

---

## 슬라이드 함수 레퍼런스

### `cover(title, subtitle, dept, name, date)` ★ 첫 슬라이드 강제

템플릿 표지의 텍스트를 교체. oid/idx 없음.

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `title` | 메인 제목 | 필수 |
| `subtitle` | 부제 (생략 가능) | `""` |
| `dept` | 부서명 | `"디자인부문ㅣ패키지디자인팀"` |
| `name` | 담당자명 | `"한원진 담당"` |
| `date` | 날짜 | 생략 시 오늘 날짜 자동 입력 (`yyyy. mm. dd.`) |

### `slide(heading, body, body_size)`

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `heading` | 헤더 텍스트 | 필수 |
| `body` | 본문 텍스트 (`\n` 줄바꿈, `• ` bullet) | 필수 |
| `body_size` | 본문 폰트 크기 (pt) | `14` |

기본값:
- v6에서는 `slide()`가 가장 우선되는 기본 컴포넌트다.
- 운영용(=디테일용=보고서형)은 본문 5~6줄까지 허용한다.
- 실행 주체 / 상태 / 다음 액션을 한 페이지에 함께 설명할 수 있어야 한다.

### `two_col(heading, left_title, left_body, right_title, right_body)`

| 파라미터 | 설명 |
|---------|------|
| `heading` | 전체 헤더 |
| `left_title` | 왼쪽 패널 제목 (오렌지) |
| `left_body` | 왼쪽 본문 |
| `right_title` | 오른쪽 패널 제목 (오렌지) |
| `right_body` | 오른쪽 본문 |

### `flow(heading, steps)`

순서 있는 흐름 슬라이드. 번호 + 세로선 + 텍스트 구조.

| 파라미터 | 설명 |
|---------|------|
| `heading` | 헤더 텍스트 |
| `steps` | `[(label, desc), ...]` — label: 단계명, desc: 부연 설명 (빈 문자열 가능) |

### `decision(heading, question, yes_label, yes_body, no_label, no_body)`

분기/판단 슬라이드. 질문 박스 + YES/NO 패널.

| 파라미터 | 설명 |
|---------|------|
| `heading` | 헤더 텍스트 |
| `question` | 판단 질문 (예: "촬영이 필요한가?") |
| `yes_label` / `yes_body` | YES 경로 제목·본문 |
| `no_label` / `no_body` | NO 경로 제목·본문 |

### `checklist(heading, items)`

완료·미완료 체크리스트 슬라이드.

| 파라미터 | 설명 |
|---------|------|
| `heading` | 헤더 텍스트 |
| `items` | `[(label, done), ...]` — done: `True`(완료 ●) / `False`(미완료 ○) |

---

## KPI 덱 빌드 스크립트 (template="kpi")

KPI / 목표 / 실적 내용이 있을 때는 `SpigenBuilder(title, template="kpi")`로 생성한다.

```python
import sys, shutil

shutil.copy2("/Users/harugury/.agents/skills/spigen-slides/spigen_build.py",
             "/tmp/spigen_build.py")
sys.path.insert(0, "/tmp")
from spigen_build import SpigenBuilder

b = SpigenBuilder("(PPT 제목)", theme="light", template="kpi")

b.cover(title="(제목)", subtitle="(부제)")

b.kpi_status(
    title="1. KPI 진행 현황",
    eyebrow="2025년도",
    top_rows=[
        # [목표구분, KPI명, 가중치, 상반기목표, 상반기실적, 상반기달성, 연간목표, 연간실적, 비고]
        ["팀명", "KPI1", 30, 85, 90, 28, 95, 85, ""],
        [None, "KPI2", 40, 70, 75, 28, 80, 75, ""],  # ri=1 col0은 None — merged cell skip
        [None, "KPI3", 30, 60, 65, 18, 70, 65, ""],
    ],
    detail_rows=[
        # [KPI명, 정의, 측정산식, 증빙]
        ["KPI1", "설명", "산식", "증빙"],
        ["KPI2", "설명", "산식", "증빙"],
        ["KPI3", "설명", "산식", "증빙"],
    ]
)

b.kpi_tasks(
    title="2. 핵심과제",
    eyebrow="2025",
    rows=[
        # [연관KPI, 핵심과제, 실행계획, 나의역할]
        ["KPI1", "과제1", "실행계획", "역할"],
        [None, "과제2", "실행계획", "역할"],  # ri=1 col0은 None — merged cell skip
        ["KPI3", "과제3", "실행계획", "역할"],
    ]
)

ok = b.flush()
if ok:
    print(f"완료: https://docs.google.com/presentation/d/{b.pid}/edit")
else:
    print("생성 실패")
```

### `kpi_status(title, eyebrow, top_rows, detail_rows)`

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `title` | 슬라이드 제목 | `"1. KPI 진행 현황"` |
| `eyebrow` | 상단 작은 텍스트 (연도 등) | `"2025년도"` |
| `top_rows` | KPI 실적 표 (최대 3행) — 각 행 9개 값. `ri=1` col0은 `None` 전달 | `None` |
| `detail_rows` | KPI 세부정보 표 (최대 3행) — 각 행 4개 값 | `None` |

### `kpi_tasks(title, eyebrow, rows)`

| 파라미터 | 설명 | 기본값 |
|---------|------|--------|
| `title` | 슬라이드 제목 | `"2. 핵심과제"` |
| `eyebrow` | 상단 작은 텍스트 | `"2025"` |
| `rows` | 핵심과제 표 (최대 3행) — 각 행 4개 값. `ri=1` col0은 `None` 전달 | `None` |

---

## 실행 명령

```bash
python3 /tmp/build_<name>.py
```

FAIL 시: 오류 메시지 확인 → 해당 슬라이드 수정 → 재실행.

---

## 완료 보고

```
완성: https://docs.google.com/presentation/d/<ID>/edit
```

빌드가 성공하면 제작 결과를 요약하고 검증 실행 여부를 묻는다.

```text
완성: https://docs.google.com/presentation/d/<ID>/edit
요약: (생성한 주요 내용)

2. 검증을 실행할까요?
```

- 검증을 자동 실행하지 않는다.
- 사용자가 "검증", "검수", "2번", "검증 실행"을 명시하면 `spigen-slides-review` 스킬을 사용한다.
- 검증 결과가 불통과여도 이 제작 스킬에서 반복 수정 루프를 시작하지 않는다.

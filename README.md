# Spigen Slides

Google Slides 자동 생성을 위한 Claude Code 스킬 (Spigen 디자인 시스템 적용).

> 사내 전용 공유 저장소 — 외부 공개·재배포 금지.

## 구성

- **spigen-slides** — 메인 제작 스킬 (Google Slides 자동 빌드)
- **spigen-slides-review** — 검수 스킬 (페르소나 검수, 자동 검증 — 사용자가 명시적으로 요청할 때만 실행)
- **craft-design-rules.md** — 범용 디자인 craft 규칙 (Anti-AI-Slop / 자간 / 색상 규율 / 80/20 소울 원칙) — 다른 디자인 스킬에서도 참조 가능

## 설치

1. 두 스킬 디렉토리를 Claude Code skills 경로에 복사
   ```bash
   cp -r spigen-slides ~/.claude/skills/
   cp -r spigen-slides-review ~/.claude/skills/
   ```

2. 범용 craft 규칙도 같은 위치에 복사
   ```bash
   cp craft-design-rules.md ~/.claude/skills/
   ```

3. 의존성: `gws` CLI (Google Workspace OAuth 인증 후 사용)

4. Google Slides 템플릿 복사 권한 + 본인 템플릿 사용 시 `custom_template_id` 인자 전달

## 사용

Claude Code에서 PPT 생성 요청 시 자동 발동:

> "패키지 자동화 PPT 만들어줘"

테마는 사용자가 명시한다 (Q4):

> "다크모드로 만들어줘" / "라이트모드로 만들어줘"

생략 시 기본은 dark.

직접 빌더 호출:

```python
from spigen_build import SpigenBuilder

b = SpigenBuilder("발표 제목", theme="dark")
b.cover(title="제목\n부제")  # date 생략 → 오늘 날짜 yyyy.mm.dd 자동
b.start_slide(heading="개요", eyebrow="OVERVIEW")
b.card(x=48, y=110, w=300, h=200, label="01", title="첫 카드", body="본문")
b.section_divider(1, "방법론")
b.numbered_steps(heading="실행 방법", items=["단계 1", "단계 2"])
b.flush()
```

## 핵심 헬퍼

| 의도 | 헬퍼 | 시각 |
|---|---|---|
| 표지 | `cover()` | 템플릿 표지 텍스트 교체 (date 자동 yyyy.mm.dd) |
| 자유 헤더 | `start_slide()` | eyebrow + 22pt 헤더 |
| 카드 | `card()` | label(accent 오렌지) + title + body(9pt) |
| 단계 흐름 | `flow_step()` | 번호 박스 + 단계 설명 |
| 비교 행 | `compare_pair()` | y만 지정, 가로 자동 배치 |
| 챕터 구분 | `section_divider()` | 큰 오렌지 숫자 + Section 라벨 + 제목 |
| 점검 체크 | `checklist()` | ●/○ 마크 |
| 순서 안내 | `numbered_steps()` | 01-NN 숫자 라벨 |
| 강조 메시지 | `callout()` | 한 슬라이드 한 문장 |
| 결론 | `conclusion()` | 큰 메트릭 + 캡션 + 디테일 4개 |

자세한 가이드는 `spigen-slides/SKILL.md` 참조.

## 디자인 시스템

- **다크 / 라이트** 테마 자동 강제 (V6.3.2: Q4에서 명시 선택, 기본 dark)
- **다크 배경 #000000** (V6.3, 표지와 통일)
- **카드 본문 9pt + line spacing 1.5** (V6.3, 코드 토큰 자동 적용)
- **카드 라벨 accent 오렌지** (V6.3, default emphasis 컬러)
- **마진 48 / 12 컬럼 그리드** (V6.2)
- **폰트 위계**: 22 / 10.5 / 8 (FONT_HIERARCHY 강제)
- **컬러**: 오렌지 슬라이드당 2회 이내, dim/fg/accent 토큰만 사용
- **헤더 좌측 정렬**: x=48
- **80/20 소울 원칙**: 80% 토큰·컴포넌트 규칙 준수 + 20% 차별점 1가지

## 검수

검수가 필요한 경우 별도 명시:

> "검수해줘"

→ `spigen-slides-review` 스킬이 페르소나 검수 + 자동 검증 실행.

## 변경 이력

### v6.3.2 (2026-05-07)
- Q4 테마 선택 명시화 — `dark / light 중 선택 (기본 dark)`
- "다크 / 라이트 / 어두운 / 밝은" 한국어 표현 인식
- Step 1 Q4와 Step 1.5 강제 규칙 모순 해결

### v6.3.1 (2026-05-07)
- 표지 자동 날짜 포맷 `%Y.%m.%d` (공백 제거 → 좁은 텍스트박스 줄바꿈 방지)

### v6.3.0 (2026-05-06)
- SKILL.md 정합 — V6.3 코드 변경(다크 #000000 / 본문 9pt / 라벨 accent) 명시
- v6.2.0 craft 룰 4종 추가 — 80/20 소울, 수치 위조 금지, 플레이스홀더 금지, ALL CAPS 자간
- `craft-design-rules.md` 신규 — 범용 디자인 craft 규칙

### V6.3 (2026-05-04)
- 카드 라벨 default emphasis: dim → accent (오렌지)
- 본문 폰트 8pt → 9pt + line spacing 1.5
- 다크 배경 `#1A1A1A` → `#000000` (표지와 통일)

## 라이선스

**사내 전용** — 외부 공유·재배포·인용 금지.
Spigen Korea 디자인부문 패키지디자인팀 운영.

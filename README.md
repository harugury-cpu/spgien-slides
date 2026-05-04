# Spigen Slides

Google Slides 자동 생성을 위한 Claude Code 스킬 (Spigen 디자인 시스템 적용).

## 구성

- **spigen-slides** — 메인 제작 스킬 (Google Slides 자동 빌드)
- **spigen-slides-review** — 검수 스킬 (페르소나 검수, 자동 검증 — 사용자가 명시적으로 요청할 때만 실행)

## 설치

1. 두 디렉토리를 Claude Code skills 경로에 복사 또는 심볼릭 링크
   ```bash
   cp -r spigen-slides ~/.claude/skills/
   cp -r spigen-slides-review ~/.claude/skills/
   ```

2. 의존성: `gws` CLI (Google Workspace OAuth 인증 후 사용)

3. Google Slides 템플릿 복사 권한 + 본인 템플릿 사용 시 `custom_template_id` 인자 전달

## 사용

Claude Code에서 PPT 생성 요청 시 자동 발동:

> "패키지 자동화 PPT 만들어줘"

또는 직접 빌더 호출:

```python
from spigen_build import SpigenBuilder

b = SpigenBuilder("발표 제목", theme="dark")
b.cover(title="제목\n부제", date="2026. 05.")
b.start_slide(heading="개요", eyebrow="OVERVIEW")
b.card(x=48, y=110, w=300, h=200, label="01", title="첫 카드", body="본문")
b.section_divider(1, "방법론")
b.numbered_steps(heading="실행 방법", items=["단계 1", "단계 2"])
b.flush()
```

## 핵심 헬퍼

| 의도 | 헬퍼 | 시각 |
|---|---|---|
| 표지 | `cover()` | 템플릿 표지 텍스트 교체 |
| 자유 헤더 | `start_slide()` | eyebrow + 22pt 헤더 |
| 카드 | `card()` | label + title + body 박스 |
| 단계 흐름 | `flow_step()` | 번호 박스 + 단계 설명 |
| 챕터 구분 | `section_divider()` | 큰 오렌지 숫자 + Section 라벨 + 제목 |
| 점검 체크 | `checklist()` | ●/○ 마크 |
| 순서 안내 | `numbered_steps()` | 01-NN 숫자 라벨 |
| 강조 메시지 | `callout()` | 한 슬라이드 한 문장 |
| 결론 | `conclusion()` | 큰 메트릭 + 캡션 + 디테일 |

자세한 가이드는 `spigen-slides/SKILL.md` 참조.

## 디자인 시스템

- **다크 / 라이트** 테마 자동 강제 (Spigen Design System)
- **마진 48 / 12 컬럼 그리드** (V6.2)
- **폰트 위계**: 22 / 10.5 / 8 (FONT_HIERARCHY 강제)
- **컬러**: 오렌지 10% 이내, dim/fg/accent 토큰만 사용
- **헤더 좌측 정렬**: x=48 (자유 빌딩 블록 마진과 통일)

## 검수

검수가 필요한 경우 별도 명시:

> "검수해줘"

→ `spigen-slides-review` 스킬이 페르소나 검수 + 자동 검증 실행.

## 라이선스

내부용 — 외부 공유 시 Spigen 정책 확인 필요.

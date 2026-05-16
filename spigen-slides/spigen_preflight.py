#!/usr/bin/env python3
"""
spigen_preflight.py — Spigen Slides planning gate.

빌드 전에 슬라이드 구성 계획(JSON)을 검사한다.
목적은 디자인 검수가 아니라, "내용 타입 분류 → 섹션 구조 → 컴포넌트 선택" 순서를
실제로 지켰는지 막는 것이다.

Usage:
  python3 ~/.agents/skills/spigen-slides/spigen_preflight.py /tmp/spigen_plan.json

Plan schema:
{
  "purpose": "운영 구조 설명",
  "audience": "프로젝트 참여자",
  "mode": "operational_detail_report",
  "sections": [
    {
      "title": "현재 구조",
      "slides": [
        {"title": "전체 구조", "role": "structure", "component": "diagram"}
      ]
    }
  ]
}
"""

import json
import sys
from pathlib import Path


DIAGRAM_COMPONENTS = {
    "diagram",
    "free_diagram",
    "flow",
    "flow_step",
    "mk_flow",
    "mk_flow_focus",
    "mk_arch_layers",
    "mk_decision_tree",
    "mk_swimlane_mapping",
}
CARD_COMPONENTS = {"card", "cards", "3col_cards", "mk_3col_cards"}


def fail(msg):
    print(f"[FAIL] {msg}")
    return False


def warn(msg):
    print(f"[WARN] {msg}")


def main(path):
    data = json.loads(Path(path).read_text())
    ok = True

    purpose = str(data.get("purpose", "")).strip()
    audience = str(data.get("audience", "")).strip()
    mode = str(data.get("mode", "")).strip()
    sections = data.get("sections", [])

    if not purpose:
        ok &= fail("purpose가 비어 있음 — 자료 목적을 먼저 정의해야 함")
    if not audience:
        ok &= fail("audience가 비어 있음 — 청중을 먼저 정의해야 함")
    if mode and mode != "operational_detail_report":
        warn("기본 모드는 operational_detail_report임. 요약/발표형은 사용자가 명시 요청한 경우만 허용")
    if not sections:
        ok &= fail("sections가 없음 — 섹션 구조를 먼저 나눠야 함")

    slide_count = sum(len(s.get("slides", [])) for s in sections if isinstance(s, dict))
    if slide_count >= 7 and len(sections) < 2:
        ok &= fail("7장 이상 덱인데 섹션이 2개 미만 — section_divider로 세션을 나눌 것")

    for si, section in enumerate(sections, start=1):
        stitle = str(section.get("title", "")).strip()
        slides = section.get("slides", [])
        if not stitle:
            ok &= fail(f"section {si}: title이 비어 있음")
        if not slides:
            ok &= fail(f"section {si}({stitle}): slides가 비어 있음")

        for li, slide in enumerate(slides, start=1):
            title = str(slide.get("title", "")).strip()
            role = str(slide.get("role", "")).strip().lower()
            component = str(slide.get("component", "")).strip().lower()

            where = f"section {si} / slide {li}({title or 'untitled'})"
            if not title:
                ok &= fail(f"{where}: title이 비어 있음")
            if not role:
                ok &= fail(f"{where}: role이 비어 있음 — 설명/구조/흐름/논의/비교 등 먼저 지정")
            if not component:
                ok &= fail(f"{where}: component가 비어 있음 — role 이후 선택")

            if role in {"agenda", "discussion", "논의", "decision"} and component in CARD_COMPONENTS:
                ok &= fail(f"{where}: 논의 항목을 카드로 만들지 말 것 — numbered_text/text 사용")

            if role in {"structure", "architecture", "system", "구조"} and component not in DIAGRAM_COMPONENTS:
                ok &= fail(f"{where}: 구조 설명은 diagram/arch/flow 계열 우선")

            if role in {"flow", "process", "workflow", "흐름"} and component not in DIAGRAM_COMPONENTS:
                ok &= fail(f"{where}: 작동 방식은 flow/diagram 계열 우선")

            if role in {"detail", "explain", "text", "설명"} and component in CARD_COMPONENTS:
                warn(f"{where}: 설명형 내용을 카드로 압축하지 않았는지 확인")

    print("[PASS] spigen preflight 통과" if ok else "[FAIL] spigen preflight 실패")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: spigen_preflight.py <plan.json>")
        sys.exit(2)
    sys.exit(main(sys.argv[1]))

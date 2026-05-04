"""
spigen_layout.py — shared layout decisions from semantic input.

This is intentionally lightweight for now: it gives preview and Slides
renderers the same normalized component choice without forcing HTML to be
the source of truth.
"""

from spigen_models import SelectionInput, SelectionResult


def choose_component(selection: SelectionInput) -> SelectionResult:
    diagram_kind = selection.diagram_kind.lower()
    deck_mode = (selection.deck_mode or "").lower()
    detail_mode = (selection.detail_mode or "").lower()
    purpose = (selection.purpose or "").lower()
    detail_level = int(selection.detail_level or 8)
    layout_variance = int(selection.layout_variance or 3)
    preserve_max = (selection.content_preservation_priority or "").lower() == "max"
    clarity_max = (selection.execution_clarity_priority or "").lower() == "max"
    operational_like = deck_mode in ("operational_detail_report", "operational", "report", "hybrid") or detail_mode == "detail" or purpose in ("report", "guide", "operate", "ops", "documentation")

    if selection.is_kpi:
        return SelectionResult("kpi-status-detail", "mk_kpi_status_detail", f"KPI 고정 양식 | {selection.item_count}개 항목")
    if diagram_kind in ("layers", "architecture_layers"):
        return SelectionResult("arch-layers", "mk_arch_layers", "구조 설명 페이지 | 입력→선택→렌더링→출력 계층")
    if diagram_kind in ("orchestrator", "architecture", "module_relations"):
        return SelectionResult("arch-orchestrator", "mk_arch_orchestrator", "구조 설명 페이지 | 오케스트레이터 중심 관계")
    if diagram_kind in ("decision", "decision_tree", "branch", "fallback"):
        return SelectionResult("decision-tree", "mk_decision_tree", "분기/폴백 구조 | YES/NO 판단 흐름")
    if diagram_kind in ("mapping", "swimlane"):
        return SelectionResult("swimlane-mapping", "mk_swimlane_mapping", "모듈↔설정 매핑 구조")
    if selection.is_bilateral:
        return SelectionResult("compare-rows", "mk_compare_rows", f"양방향 비교 구조 | {selection.item_count}개 항목 | 내용 보존 우선")
    if selection.is_process:
        if operational_like:
            if detail_level >= 8 or preserve_max or clarity_max:
                return SelectionResult("flow", "mk_flow", f"운영용 프로세스 | {selection.item_count}단계 | 자기완결 설명 우선")
            return SelectionResult("flow", "mk_flow", f"운영용 프로세스 | {selection.item_count}단계 | 설명량 우선")
        if selection.item_count <= 4 and selection.purpose not in ("report", "appendix"):
            return SelectionResult("flow-focus", "mk_flow_focus", f"단방향 프로세스 | {selection.item_count}단계 | 메인 메시지")
        return SelectionResult("flow", "mk_flow", f"단방향 프로세스 | {selection.item_count}단계")
    if selection.has_comparison:
        return SelectionResult("compare-rows", "mk_compare_rows", f"속성 비교 구조 | {selection.item_count}개 항목 | 내용 보존 우선")
    if selection.has_status:
        if operational_like:
            if selection.item_count <= 4:
                return SelectionResult("split-cards", "mk_split_cards", f"운영 상태 구분 카드 | {selection.item_count}개 항목 | 자기완결형")
            return SelectionResult("text-block", "mk_text_block", f"운영 상태 서술형 | {selection.item_count}개 항목 | 자유도 우선")
        if selection.detail_mode == "detail":
            return SelectionResult("split-cards", "mk_split_cards", f"상태 구분 카드 | {selection.item_count}개 항목 | 자기완결형")
        return SelectionResult("text-block", "mk_text_block", f"상태 요약 서술형 | {selection.item_count}개 항목")
    if operational_like and selection.message_shape in ("narrative", "dense_explanation", "instruction", "report"):
        return SelectionResult("text-block", "mk_text_block", f"운영/보고서형 서술 | {selection.item_count}개 항목 | 자유도 우선")
    if operational_like and (detail_level >= 8 or preserve_max):
        return SelectionResult("text-block", "mk_text_block", f"운영/보고서형 기본값 | {selection.item_count}개 항목 | 형식보다 내용 우선")
    if selection.item_count == 3 and selection.message_shape not in ("narrative", "dense_explanation") and layout_variance >= 5:
        return SelectionResult("3col-cards", "mk_3col_cards", "독립 항목 3개 카드")
    if selection.item_count <= 2:
        if operational_like:
            return SelectionResult("text-block", "mk_text_block", f"운영/보고서형 2항목 설명 | {selection.item_count}개 항목 | 형식보다 설명 우선")
        return SelectionResult("split-layout", "mk_split", f"2분할 레이아웃 | {selection.item_count}개 항목")
    return SelectionResult("text-block", "mk_text_block", f"서술형 텍스트 | {selection.item_count}개 항목 | 자유도 우선")

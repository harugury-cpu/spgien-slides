"""
spigen_tokens.py — Spigen Slides 디자인 토큰 (공개 API)

빌더가 시트의 시각 토큰만 빌려쓰면서 자유 레이아웃을 구성할 수 있도록
색·간격·타이포·캔버스 토큰을 한 곳에서 명시 노출한다.

색 토큰 / 캔버스 토큰은 spigen_lib.THEME_TOKENS, W/H/M, CONTENT_TOP/BOTTOM
값을 참조한다. SPACING / TYPO는 시트 분석값을 정리한 것이다.

사용:
    import spigen_tokens as T
    T.SPACING["card_gap"]      # 카드 간 간격
    T.TYPO["heading"]["size"]  # 헤더 폰트 크기
    T.color("ORANGE")          # 현재 테마 오렌지
"""

import spigen_lib as _lib


# ─────────────────────────────────────────────────────────────────
# 색 (테마 동적)
# ─────────────────────────────────────────────────────────────────

def color(name):
    """현재 테마 기준 색 토큰 반환 (set_theme로 변경됨)."""
    tokens = _lib.THEME_TOKENS.get(_lib.CURRENT_THEME, _lib.THEME_TOKENS["dark"])
    return tokens.get(name)


def colors():
    """현재 테마의 모든 색 토큰 dict 반환."""
    return _lib.THEME_TOKENS.get(_lib.CURRENT_THEME, _lib.THEME_TOKENS["dark"])


# ─────────────────────────────────────────────────────────────────
# 캔버스 (16:9 720×405pt 고정)
# ─────────────────────────────────────────────────────────────────

CANVAS = {
    "width": _lib.W,            # 720
    "height": _lib.H,           # 405
    "margin": _lib.M,           # 36
    "content_top": _lib.CONTENT_TOP,        # 112 (mk_* legacy)
    "content_bottom": _lib.CONTENT_BOTTOM,  # 381 (mk_* legacy)
    "content_w": _lib.W - _lib.M * 2,       # 648
    "content_h": _lib.CONTENT_BOTTOM - _lib.CONTENT_TOP,  # 269
    # V5.7: 자유 빌딩 블록(start_slide+) 모드 콘텐츠 영역
    # 위 빈 여백 = eyebrow 시작 y=32, 아래도 동일 32pt 빈 여백 → end=373
    "v57_content_top": 100,    # start_slide 헤더 후 콘텐츠 시작
    "v57_content_bottom": 373, # 405 - 32 (위 여백과 대칭)
}


# ─────────────────────────────────────────────────────────────────
# 간격 (시트 실측 기반)
# ─────────────────────────────────────────────────────────────────

SPACING = {
    "card_gap": 8,           # 카드 간 가로 간격 (3col, flow_focus)
    "card_gap_y": 12,        # 카드 간 세로 간격 (rule_grid)
    "card_pad": 16,          # 카드 내부 패딩 (좌우상하)
    "card_pad_inner": 18,    # 카드 텍스트 좌우 인셋
    "header_to_body": 24,    # 헤더 가로선 → 본문 시작
    "section_gap": 12,       # 섹션 간 간격
    "tight": 4,              # 타이트 간격 (라인 간)
    "narrow": 8,             # 좁은 간격
    "normal": 12,            # 일반 간격
    "wide": 16,              # 넓은 간격
    "row_h": 28,             # 표/매핑 행 높이 기본
}


# ─────────────────────────────────────────────────────────────────
# 타이포 (시트 실측 기반)
# ─────────────────────────────────────────────────────────────────

TYPO = {
    "cover_title":   {"size": 34, "bold": True,  "font": "Noto Sans KR"},
    "cover_subtitle":{"size": 17, "bold": False, "font": "Noto Sans KR"},
    "cover_meta":    {"size": 11, "bold": False, "font": "Noto Sans KR"},
    "heading":       {"size": 22, "bold": True,  "font": "Noto Sans KR"},
    "eyebrow":       {"size": 7,  "bold": True,  "font": "Proxima Nova"},
    "body":          {"size": 14, "bold": False, "font": "Noto Sans KR"},
    "body_sm":       {"size": 13, "bold": False, "font": "Noto Sans"},
    "card_title":    {"size": 13, "bold": True,  "font": "Noto Sans"},
    "card_body":     {"size": 7,  "bold": False, "font": "Noto Sans"},
    "card_label":    {"size": 7,  "bold": True,  "font": "Proxima Nova"},
    "callout_lead":  {"size": 16, "bold": True,  "font": "Noto Sans KR"},
    "callout_sub":   {"size": 10, "bold": False, "font": "Noto Sans KR"},
    "footnote":      {"size": 7,  "bold": False, "font": "Noto Sans"},
}


# ─────────────────────────────────────────────────────────────────
# 강조 룰
# ─────────────────────────────────────────────────────────────────

EMPHASIS = {
    "primary_max": 1,  # 한 슬라이드에 풀-오렌지 강조 카드 최대 개수
    "accent_dim_when_more": True,  # primary 2개 이상 시 나머지는 ORANGE_DIM 강등
    "border_weight_normal": 0.5,
    "border_weight_accent": 0.8,
    "divider_weight": 0.5,
    "header_line_weight": 2,
}


# ─────────────────────────────────────────────────────────────────
# 보더
# ─────────────────────────────────────────────────────────────────

BORDERS = {
    "card": {"weight": 0.5, "color_token": "BORDER"},
    "card_accent": {"weight": 0.5, "color_token": "ORANGE"},
    "divider": {"weight": 0.75, "color_token": "BORDER_HI"},
}


# ─────────────────────────────────────────────────────────────────
# 시트 실측 좌표 (dark 템플릿 기준 — light도 동일 좌표 사용)
# ─────────────────────────────────────────────────────────────────

FONT_HIERARCHY = {
    # V5.9 빌드 시점 폰트 위계 강제 — 임의 사이즈 사용 금지.
    # 코드 호출 시 이 토큰만 사용해서 페이지 간 일관성 보장.
    "title":         22,    # 슬라이드 헤더
    "metric":        56,    # 결론 페이지 큰 메시지
    "card_title":    10.5,  # 카드 / flow_step / compare_pair item / checklist 텍스트
    "body":          8,     # 카드 body / flow desc / compare 본문 (line spacing 1.5 자동)
    "label":         8,     # 카드 label / eyebrow (bold)
    "footnote":      7,     # 작은 sub / annotation
    "minimum":       6,     # 가장 작은 부가 정보
    # 호환 — checklist mark 등 비텍스트 사이즈
    "mark":          12,    # 체크리스트 마크 ●/○
}


HEADER = {
    # 모든 텍스트박스 valign=MIDDLE 일관성. 박스 가운데 = 텍스트 시각 위치.
    # eyebrow + title 동시 사용 (start_slide에 eyebrow 인자 전달 시)
    "eyebrow": {
        # V6.2: 자유 빌딩 블록 마진 48과 정렬 (헤더-본문 좌측 X 통일)
        "x": 48, "y": 32, "w": 312, "h": 10,
        "valign": "MIDDLE",
        "font_size": 8, "bold": True,
        "color_token": "ORANGE",
    },
    "title_with_eyebrow": {
        # eyebrow와 시각 영역이 겹치지 않도록 박스 가운데 = y=59
        # (22pt 텍스트 시각 영역 y=48~70, eyebrow 시각 영역 y=33~41 → 7pt 간격)
        # V6.2: x 40→48, w 640→624 (자유 블록 마진과 정렬)
        "x": 48, "y": 46, "w": 624, "h": 26,
        "valign": "MIDDLE",
        "font_size": 22, "bold": True,
        "color_token": "TEXT",
    },
    # eyebrow 없이 title만 있을 때 (start_slide에 heading만 전달 시)
    "title_only": {
        "x": 48, "y": 20, "w": 624, "h": 38,
        "valign": "MIDDLE",
        "font_size": 22, "bold": True,
        "color_token": "TEXT",
    },
    # 권장 콘텐츠 시작 y (title_with_eyebrow 사용 시 헤더 끝점 ~48 + 여백 52)
    "content_start_y": 100,
}


SHEET_GEOM = {
    # mk_3col_cards 표준 ─────────────────────────────────────────
    "card_3col": {
        "card_w": 206,
        "card_h": 190,
        "gap_x": 12,
        "x0": 36,                # 캔버스 마진과 일치
        "y0": 116,
        "padding_x": 18,         # 카드 내 좌우 인셋
        "label_y_offset": 16,    # 카드 top → label
        "label_h": 12,
        "title_y_offset": 39,    # 카드 top → title
        "title_h": 28,
        "body_y_offset": 79,     # 카드 top → body 시작
        "label_size": 8,
        "title_size": 14,
        "body_size": 8,
    },

    # mk_flow_focus / mk_flow 카드 (가로 분할, height 작음) ────────
    "flow_step": {
        "card_h": 140,
        "gap_x": 8,
        "padding_x": 16,
        "num_y_offset": 14,
        "num_h": 16,
        "name_y_offset": 36,
        "name_h": 22,
        "desc_y_offset": 62,
        "num_size": 10,
        "name_size": 14,
        "desc_size": 10,
    },

    # mk_swimlane_mapping 표준 ───────────────────────────────────
    "swimlane": {
        "y0": 146,
        "left_w": 240,
        "mid_w": 110,
        "right_w": 222,
        "gap_x": 20,
        "total_h": 168,
        "padding_x": 16,
        "header_h": 12,
        "header_y_offset": 18,
        "row_h_3rows": 39,       # 3행일 때 행 높이
        "row_size": 12,
        "mid_size": 10,
        "header_size": 8,
    },

    # mk_arch_layers 표준 ─────────────────────────────────────────
    "arch_layers": {
        "side_w": 72,
        "main_w": 520,
        "gap_x": 20,             # side와 main 사이
        "layer_h": 42.5,
        "layer_gap_y": 10,
        "y0": 148,
        "padding_x": 18,
        "side_label_size": 8,
        "main_text_size": 12,
    },

    # mk_decision_tree 표준 ──────────────────────────────────────
    "decision_tree": {
        "input_w": 110,
        "input_h": 44,
        "decision_w": 126,
        "decision_h": 76,
        "result_w": 150,
        "result_h": 44,
        "exit_w": 74,
        "exit_h": 44,
        "label_size": 10,
        "branch_label_size": 7,
    },

    # mk_compare_rows 표준 ───────────────────────────────────────
    "compare_rows": {
        "item_w": 140,
        "before_w": 240,
        "after_w": 240,
        "x0": 40,
        "row_h_min": 28,
        "header_size": 8,
        "item_size": 12,
        "body_size": 11,
    },

    # mk_conclusion_detail 표준 ──────────────────────────────────
    "conclusion_detail": {
        "main_metric_size": 56,
        "card_w": 314,
        "card_h": 44,
        "card_gap_y": 8,
        "card_x_right": 370,     # 우측 4개 카드의 x 시작
    },
}


# 강조(primary) 표현 — 시트 실측 기반
EMPHASIS_STYLE = {
    "primary": {
        "fill_token": "ORANGE_DIM",   # 시트는 풀 ORANGE이 아니라 DIM 사용
        "border_token": "ORANGE",
        "border_weight": 0.5,
        "text_token": "TEXT",          # 텍스트는 기본 (흰색 강제 안 함)
    },
    "accent": {
        "fill_token": "SURFACE",
        "border_token": "ORANGE",
        "border_weight": 0.5,
        "text_token": "TEXT",
    },
    "normal": {
        "fill_token": "SURFACE",
        "border_token": "BORDER",
        "border_weight": 0.4,
        "text_token": "TEXT",
    },
}

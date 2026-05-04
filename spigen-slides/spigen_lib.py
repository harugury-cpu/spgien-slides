"""
spigen_lib.py — Spigen / CrossCheck Bot Google Slides component library

Design source:
    https://docs.google.com/presentation/d/1rh_2NNwM2CeZxFaZFfgoK3s1RAU2SyzZd794480hrVo/edit

Design direction:
    - 720 × 405pt Google Slides 16:9 canvas
    - theme-selectable token system (dark / light)
    - orange accent (#FF6B1A)
    - native Google Slides shapes/text only

Compatibility:
    Existing public helper/function names are preserved so older execution snippets
    still run, but all visual output now follows the user's current template.
"""
import math
from spigen_layout import choose_component
from spigen_models import ComponentSpec, SelectionInput, SlideSpec


# ─────────────────────────────────────────────────────────────────────
# Tokens / primitives
# ─────────────────────────────────────────────────────────────────────

def pt(v):
    return int(v * 12700)





def c255(r, g, b):
    return {"red": r / 255, "green": g / 255, "blue": b / 255}


# V6.0: Spigen Design System 컬러 토큰 직접 동기화
# 출처: Spigen Dark/Light Design System colors_and_type.css
THEME_TOKENS = {
    "dark": {
        "BG":         c255(26, 26, 26),       # #1A1A1A
        "SURFACE":    c255(38, 38, 38),       # #262626 (★ V6.0: 14→38, 24% 밝게)
        "SURFACE_HI": c255(48, 48, 48),       # #303030
        "SURFACE_2":  c255(42, 42, 42),       # #2A2A2A
        "BORDER":     c255(53, 53, 53),       # rgba(255,255,255,.12) 합성
        "BORDER_HI":  c255(72, 72, 72),       # rgba(255,255,255,.20) 합성
        "ORANGE":     c255(255, 107, 26),     # #FF6B1A
        "ORANGE_DIM": c255(58, 37, 26),       # 14% 합성 (★ V6.0)
        "ORANGE_LINE": c255(152, 71, 26),     # 55% 합성
        "ORANGE_SOFT": c255(35, 29, 26),      # 4% 합성
        "WHITE":      {"red": 1, "green": 1, "blue": 1},
        "TEXT":       c255(228, 228, 228),    # 88% 합성
        "TEXT_DIM":   c255(196, 196, 196),    # 74% 합성
        "TEXT_FAINT": c255(154, 154, 154),    # 56% 합성
        "GOOD":       c255(156, 227, 125),    # #9CE37D
        "BAD":        c255(255, 122, 122),    # #FF7A7A
        "BLACK":      c255(0, 0, 0),
    },
    "light": {
        "BG":             c255(255, 255, 255),   # #FFFFFF (순백, V6.0.1 사용자 요청)
        "SURFACE":        c255(251, 250, 246),   # #FBFAF6
        "SURFACE_HI":     c255(236, 234, 227),   # #ECEAE3
        "SURFACE_2":      c255(229, 226, 217),   # #E5E2D9
        "BORDER":         c255(228, 226, 221),   # rgba(20,20,20,.07) 합성
        "BORDER_HI":      c255(215, 213, 208),   # rgba(20,20,20,.13) 합성
        "ORANGE":         c255(239, 95, 14),     # ★ V6.0: #EF5F0E (다크보다 어두운 오렌지)
        "ORANGE_STRONG":  c255(208, 78, 7),      # #D04E07 (hover/press)
        "ORANGE_DIM":     c255(244, 229, 216),   # 9% 합성 (★ V6.0)
        "ORANGE_LINE":    c255(242, 180, 143),   # 42% 합성
        "ORANGE_SOFT":    c255(244, 237, 227),   # 4% 합성
        "WHITE":          {"red": 1, "green": 1, "blue": 1},
        "TEXT":           c255(47, 47, 46),      # 88% 합성
        "TEXT_DIM":       c255(105, 104, 102),   # 62% 합성
        "TEXT_FAINT":     c255(150, 149, 145),   # 42% 합성
        "GOOD":           c255(31, 166, 74),     # #1FA64A
        "BAD":            c255(197, 48, 48),     # #C53030
        "BLACK":          c255(0, 0, 0),
    },
}

CURRENT_THEME = "dark"


def select_component(content_type="", item_count=0, has_comparison=False,
                     is_process=False, has_status=False, is_bilateral=False,
                     is_kpi=False, audience="", purpose="", detail_mode="",
                     diagram_kind="", message_shape=""):
    """Returns (component_name, function_name, rationale) — 결정론적 컴포넌트 선택.
    spigen_render_rules.md 섹션 8 결정 테이블 코드 구현.
    기획 단계 1-4에서 호출 후 rationale을 아웃라인에 기록한다."""
    selection = SelectionInput(
        content_type=content_type,
        item_count=item_count,
        has_comparison=has_comparison,
        is_process=is_process,
        has_status=has_status,
        is_bilateral=is_bilateral,
        is_kpi=is_kpi,
        audience=audience,
        purpose=purpose,
        detail_mode=detail_mode,
        diagram_kind=diagram_kind,
        message_shape=message_shape,
    )
    result = choose_component(selection)
    return result.component_name, result.function_name, result.rationale


def render_component_spec(sid, component, reqs, eyebrow="", title=""):
    """Render a shared component spec into native Google Slides requests."""
    if isinstance(component, dict):
        component = ComponentSpec.from_dict(component)
    ctype = component.type
    props = component.props
    if ctype == "flow":
        return mk_flow(sid, props.get("steps", []), reqs=reqs)
    if ctype == "flow-focus":
        return mk_flow_focus(sid, props.get("steps", []), reqs)
    if ctype == "compare-rows":
        return mk_compare_rows(
            sid,
            props.get("rows", []),
            reqs,
            left_label=props.get("left_label", "현재"),
            right_label=props.get("right_label", "도입 후"),
            callout=props.get("callout", ""),
            is_bilateral=props.get("is_bilateral", False),
        )
    if ctype == "decision-tree":
        return mk_decision_tree(sid, props.get("nodes", {}), reqs, eyebrow=eyebrow, title=title)
    if ctype == "split-layout":
        return mk_split(sid, props.get("left", {}), props.get("right", {}), reqs, arrow=props.get("arrow", True))
    if ctype == "text-block":
        return mk_text_block(sid, props.get("body_text", ""), reqs)
    if ctype == "arch-layers":
        return mk_arch_layers(sid, props.get("layers", []), reqs, eyebrow=eyebrow, title=title)
    if ctype == "arch-orchestrator":
        return mk_arch_orchestrator(sid, props.get("nodes", {}), reqs, eyebrow=eyebrow, title=title)
    if ctype == "swimlane-mapping":
        return mk_swimlane_mapping(sid, props.get("rows", []), reqs, eyebrow=eyebrow, title=title)
    if ctype == "split-cards":
        return mk_split_cards(sid, props.get("text_lines", []), props.get("cards", []), reqs)
    if ctype == "3col-cards":
        return mk_3col_cards(sid, props.get("cards", []), reqs)
    if ctype == "3-col":
        return mk_3col(sid, props.get("cols", []), reqs)
    raise ValueError(f"Unsupported component type: {ctype}")


def render_slide_spec(slide_spec, insert_index, reqs, total=None):
    """Render a shared slide spec into Google Slides requests."""
    if isinstance(slide_spec, dict):
        slide_spec = SlideSpec.from_dict(slide_spec)
    if not slide_spec.components:
        raise ValueError("SlideSpec.components is empty")

    first = slide_spec.components[0]
    if first.type == "cover":
        props = first.props
        return mk_cover(
            slide_spec.slide_id,
            props.get("title", ""),
            insert_index,
            reqs,
            subtitle=props.get("subtitle", ""),
            department=props.get("department", "디자인부문ㅣ패키지디자인팀"),
            owner=props.get("owner", "한원진 담당"),
            date_text=props.get("date_text", ""),
            version=props.get("version", "V1.0"),
        )

    if first.type == "section-divider":
        props = first.props
        return mk_section_divider(
            slide_spec.slide_id,
            props.get("num", "01"),
            props.get("title", ""),
            insert_index,
            reqs,
        )

    slide_base(slide_spec.slide_id, slide_spec.title, insert_index, reqs, page_no=slide_spec.page_no, total=total)
    for component in slide_spec.components:
        render_component_spec(slide_spec.slide_id, component, reqs)


def mk_compare_rows(sid, rows, reqs, left_label="현재", right_label="도입 후", callout="", is_bilateral=False):
    """Compare layout modeled after the system guide page 17 reference.

    is_bilateral=True: 두 경로가 대등한 분기일 때. 좌측에 BAD 색상을 쓰지 않고
    오렌지를 우측 헤더 1개로만 절제한다.
    """
    left_header_color = TEXT_DIM if is_bilateral else BAD
    _text(reqs, sid, f"{sid}_cmp_left_label", 36, 109, 120, 10, left_label, left_header_color, 5, False, "Noto Sans")
    _text(reqs, sid, f"{sid}_cmp_right_label", 370.5, 109, 120, 10, right_label, ORANGE, 5, True, "Noto Sans")

    row_y0, row_h, row_gap = 125.2, 40, 5
    visible = rows[:5]
    for i, row in enumerate(visible):
        ry = row_y0 + i * (row_h + row_gap)
        _rect(reqs, sid, f"{sid}_cmp_lb{i}", 36, ry, 313.5, row_h, SURFACE, BORDER, 0.5)
        _rect(reqs, sid, f"{sid}_cmp_mid{i}", 349.5, ry, 21, row_h, SURFACE, BORDER, 0.5)
        _rect(reqs, sid, f"{sid}_cmp_rb{i}", 370.5, ry, 313.5, row_h, ORANGE_DIM, ORANGE, 0.5)
        # 화살표 기호는 Proxima Nova (기호 전용 폰트 규칙)
        _text(reqs, sid, f"{sid}_cmp_ar{i}", 356, ry + 17, 10, 10, "›", TEXT_DIM, 5, False, "Proxima Nova", center=True)
        _text(reqs, sid, f"{sid}_cmp_item{i}", 47, ry + 6, 280, 11, row.get("item", ""), TEXT_DIM, 8, False, "Noto Sans")
        left_text_color = TEXT_DIM if is_bilateral else BAD
        _text(reqs, sid, f"{sid}_cmp_before{i}", 47, ry + 18, 280, 16, row.get("before", ""), left_text_color, 9, False, "Noto Sans")
        # is_bilateral: after_label에 ORANGE 남발 방지 — 레이블 없이 TEXT_DIM으로 절제
        after_label_color = TEXT_DIM if is_bilateral else ORANGE
        _text(reqs, sid, f"{sid}_cmp_after_label{i}", 382, ry + 6, 280, 11, row.get("after_label", "개선"), after_label_color, 8, True, "Noto Sans")
        _text(reqs, sid, f"{sid}_cmp_after{i}", 382, ry + 18, 280, 16, row.get("after", ""), TEXT, 9, False, "Noto Sans")

    if callout:
        cy = row_y0 + len(visible) * (row_h + row_gap) - row_gap + 14
        _rect(reqs, sid, f"{sid}_cmp_callout_bar", 36, cy, 1, 26, ORANGE, ORANGE, 0)
        _text(reqs, sid, f"{sid}_cmp_callout", 48, cy + 7, 636, 13, callout, TEXT, 7, False, "Noto Sans")


def set_theme(theme="dark"):
    """
    Public theme switch for future deck generation.

    Usage:
        import spigen_lib as lib
        lib.set_theme('light')
        ...
        lib.mk_rule_grid(...)
    """
    global CURRENT_THEME
    global BG, SURFACE, SURFACE_HI, BORDER, BORDER_HI
    global ORANGE, ORANGE_DIM, WHITE, TEXT, TEXT_DIM, TEXT_FAINT
    global GOOD, BAD, BLACK, THEMES

    key = str(theme or "dark").lower()
    if key not in THEME_TOKENS:
        key = "dark"
    CURRENT_THEME = key
    tokens = THEME_TOKENS[key]
    BG = tokens["BG"]
    SURFACE = tokens["SURFACE"]
    SURFACE_HI = tokens["SURFACE_HI"]
    BORDER = tokens["BORDER"]
    BORDER_HI = tokens["BORDER_HI"]
    ORANGE = tokens["ORANGE"]
    ORANGE_DIM = tokens["ORANGE_DIM"]
    WHITE = tokens["WHITE"]
    TEXT = tokens["TEXT"]
    TEXT_DIM = tokens["TEXT_DIM"]
    TEXT_FAINT = tokens["TEXT_FAINT"]
    GOOD = tokens["GOOD"]
    BAD = tokens["BAD"]
    BLACK = tokens["BLACK"]
    THEMES = {
        "dark": {
            "SLIDE_BG": THEME_TOKENS["dark"]["BG"],
            "TITLE_COLOR": THEME_TOKENS["dark"]["TEXT"],
            "BODY_COLOR": THEME_TOKENS["dark"]["TEXT_DIM"],
            "CARD_BG": THEME_TOKENS["dark"]["SURFACE"],
            "CARD_BORDER": THEME_TOKENS["dark"]["BORDER"],
        },
        "light": {
            "SLIDE_BG": THEME_TOKENS["light"]["BG"],
            "TITLE_COLOR": THEME_TOKENS["light"]["TEXT"],
            "BODY_COLOR": THEME_TOKENS["light"]["TEXT_DIM"],
            "CARD_BG": THEME_TOKENS["light"]["SURFACE"],
            "CARD_BORDER": THEME_TOKENS["light"]["BORDER"],
        },
    }
    return CURRENT_THEME


# initialize default theme
set_theme("dark")

W, H, M = 720, 405, 36
CONTENT_TOP = 112
CONTENT_BOTTOM = 381

# theme= 인자는 기존 API 호환용으로 남아 있으며,
# 실제 색상 토큰은 set_theme('dark'|'light') 로 전환한다.


def _same_rgb(a, b, eps=1e-6):
    if not a or not b:
        return False
    return (
        abs(a.get("red", 0) - b.get("red", 0)) < eps
        and abs(a.get("green", 0) - b.get("green", 0)) < eps
        and abs(a.get("blue", 0) - b.get("blue", 0)) < eps
    )


def _normalize_visible_fill(fg, bg):
    """
    Prevent boxes/lines from disappearing into the slide background.
    If both fill and outline match BG, promote them to visible neutral tokens.
    """
    if _same_rgb(fg, BG) and _same_rgb(bg, BG):
        return SURFACE, BORDER
    if _same_rgb(fg, BG) and not _same_rgb(bg, BG):
        return SURFACE, bg
    return fg, bg


def _clamp_rect_to_canvas(x, y, w, h, left=0, top=0, right=W, bottom=H):
    """
    Hard safety rail:
      no shape/text box may extend beyond the slide canvas.

    Returns a clamped rect that always remains visible inside the canvas.
    """
    x = max(left, min(x, right - 1))
    y = max(top, min(y, bottom - 1))
    w = max(1, min(w, right - x))
    h = max(1, min(h, bottom - y))
    return x, y, w, h


def _fit_height_to_content(y, desired_h, min_h=12, bottom=CONTENT_BOTTOM):
    """
    Fit a vertical block into the content area.
    Use before laying out stacks/tables/diagrams that can grow downward.
    """
    return max(min_h, min(desired_h, bottom - y))


def _grid_columns(x, total_w, ratios, precision=0.5):
    """
    Build a stable column grid from ratios.
    Snap intermediate widths to a small step and let the final column absorb
    the remainder so adjacent table sections always share the same edge.
    """
    unit = float(precision)
    widths = []
    used = 0.0
    for ratio in ratios[:-1]:
        raw = total_w * ratio
        snapped = round(raw / unit) * unit
        widths.append(snapped)
        used += snapped
    widths.append(total_w - used)
    xs = [x]
    for width in widths[:-1]:
        xs.append(xs[-1] + width)
    return xs, widths


def _stack_group_height(item_heights, gap=0):
    if not item_heights:
        return 0
    return sum(item_heights) + gap * max(0, len(item_heights) - 1)


def shape(oid, page, stype, x, y, w, h):
    x, y, w, h = _clamp_rect_to_canvas(x, y, w, h)
    return {
        "createShape": {
            "objectId": oid,
            "shapeType": stype,
            "elementProperties": {
                "pageObjectId": page,
                "size": {
                    "width": {"magnitude": pt(w), "unit": "EMU"},
                    "height": {"magnitude": pt(h), "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1,
                    "scaleY": 1,
                    "translateX": pt(x),
                    "translateY": pt(y),
                    "unit": "EMU",
                },
            },
        }
    }


def table(oid, page, rows, cols, x, y, w, h):
    x, y, w, h = _clamp_rect_to_canvas(x, y, w, h)
    return {
        "createTable": {
            "objectId": oid,
            "rows": rows,
            "columns": cols,
            "elementProperties": {
                "pageObjectId": page,
                "size": {
                    "width": {"magnitude": pt(w), "unit": "EMU"},
                    "height": {"magnitude": pt(h), "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1,
                    "scaleY": 1,
                    "translateX": pt(x),
                    "translateY": pt(y),
                    "unit": "EMU",
                },
            },
        }
    }


def merge_cells(table_id, row, col, row_span, col_span):
    return {
        "mergeTableCells": {
            "objectId": table_id,
            "tableRange": {
                "location": {"rowIndex": row, "columnIndex": col},
                "rowSpan": row_span,
                "columnSpan": col_span,
            },
        }
    }


def table_col_width(table_id, col_index, width):
    return {
        "updateTableColumnProperties": {
            "objectId": table_id,
            "columnIndices": [col_index],
            "tableColumnProperties": {
                "columnWidth": {"magnitude": width, "unit": "PT"}
            },
            "fields": "columnWidth",
        }
    }


def table_row_height(table_id, row_index, height):
    return {
        "updateTableRowProperties": {
            "objectId": table_id,
            "rowIndices": [row_index],
            "tableRowProperties": {
                "minRowHeight": {"magnitude": height, "unit": "PT"}
            },
            "fields": "minRowHeight",
        }
    }


def table_border(table_id, rows, cols, color, weight_pt=0.75, position="ALL"):
    return {
        "updateTableBorderProperties": {
            "objectId": table_id,
            "tableRange": {
                "location": {"rowIndex": 0, "columnIndex": 0},
                "rowSpan": rows,
                "columnSpan": cols,
            },
            "borderPosition": position,
            "tableBorderProperties": {
                "tableBorderFill": {
                    "solidFill": {"color": {"rgbColor": color}}
                },
                "weight": {"magnitude": weight_pt, "unit": "PT"},
                "dashStyle": "SOLID",
            },
            "fields": "tableBorderFill.solidFill.color,weight,dashStyle",
        }
    }


def table_cell_fill(table_id, row, col, row_span, col_span, color):
    return {
        "updateTableCellProperties": {
            "objectId": table_id,
            "tableRange": {
                "location": {"rowIndex": row, "columnIndex": col},
                "rowSpan": row_span,
                "columnSpan": col_span,
            },
            "tableCellProperties": {
                "tableCellBackgroundFill": {
                    "solidFill": {"color": {"rgbColor": color}}
                }
            },
            "fields": "tableCellBackgroundFill.solidFill.color",
        }
    }


def table_cell_valign(table_id, row, col, row_span, col_span, valign="MIDDLE"):
    return {
        "updateTableCellProperties": {
            "objectId": table_id,
            "tableRange": {
                "location": {"rowIndex": row, "columnIndex": col},
                "rowSpan": row_span,
                "columnSpan": col_span,
            },
            "tableCellProperties": {
                "contentAlignment": valign
            },
            "fields": "contentAlignment",
        }
    }


def table_cell_text(reqs, table_id, row, col, text, color=TEXT, size=7,
                    bold=False, ff="Noto Sans", center=False):
    reqs += [
        {
            "insertText": {
                "objectId": table_id,
                "cellLocation": {"rowIndex": row, "columnIndex": col},
                "text": str(text or " "),
                "insertionIndex": 0,
            }
        },
        {
            "updateTextStyle": {
                "objectId": table_id,
                "cellLocation": {"rowIndex": row, "columnIndex": col},
                "textRange": {"type": "ALL"},
                "style": {
                    "foregroundColor": {"opaqueColor": {"rgbColor": color}},
                    "fontSize": {"magnitude": _type_scale(size), "unit": "PT"},
                    "fontFamily": ff,
                    "bold": bold,
                },
                "fields": "foregroundColor,fontSize,fontFamily,bold",
            }
        },
    ]
    if center:
        reqs.append({
            "updateParagraphStyle": {
                "objectId": table_id,
                "cellLocation": {"rowIndex": row, "columnIndex": col},
                "textRange": {"type": "ALL"},
                "style": {"alignment": "CENTER"},
                "fields": "alignment",
            }
        })


def line(oid, page, x1, y1, x2, y2, category="STRAIGHT"):
    """
    Native Google Slides line / connector primitive.

    Use for:
        - process arrows
        - branch / fallback connectors
        - module relation lines

    Do not use for:
        - table separators
        - card dividers
        - decorative underlines

    Notes:
        Google Slides may normalize the created element's internal size/transform
        while preserving the visual endpoints. This is expected API behavior.
    """
    w = max(abs(x2 - x1), 0.1)
    h = max(abs(y2 - y1), 0.1)
    return {
        "createLine": {
            "objectId": oid,
            "category": category,
            "elementProperties": {
                "pageObjectId": page,
                "size": {
                    "width": {"magnitude": pt(w), "unit": "EMU"},
                    "height": {"magnitude": pt(h), "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1 if x2 >= x1 else -1,
                    "scaleY": 1 if y2 >= y1 else -1,
                    "translateX": pt(min(x1, x2)),
                    "translateY": pt(min(y1, y2)),
                    "unit": "EMU",
                },
            },
        }
    }


def linestyle(oid, color=ORANGE, weight=1.0, start_arrow="NONE", end_arrow="NONE", dash_style="SOLID"):
    return {
        "updateLineProperties": {
            "objectId": oid,
            "lineProperties": {
                "lineFill": {"solidFill": {"color": {"rgbColor": color}}},
                "weight": {"magnitude": weight, "unit": "PT"},
                "dashStyle": dash_style,
                "startArrow": start_arrow,
                "endArrow": end_arrow,
            },
            "fields": "lineFill.solidFill.color,weight,dashStyle,startArrow,endArrow",
        }
    }


def connector(reqs, sid, oid, x1, y1, x2, y2, color=ORANGE, weight=1.0,
              start_arrow="NONE", end_arrow="FILL_ARROW", category="STRAIGHT"):
    """
    Semantic relationship / flow line.

    Preferred for:
        - flow direction
        - branch yes/no routes
        - module-to-module relationships

    Avoid for:
        - table grid lines
        - card separators
        - static layout dividers
    """
    reqs += [
        line(oid, sid, x1, y1, x2, y2, category=category),
        linestyle(oid, color=color, weight=weight, start_arrow=start_arrow, end_arrow=end_arrow),
    ]


def fill(oid, fg, bg=None, wt=0.4):
    bg = bg or fg
    fg, bg = _normalize_visible_fill(fg, bg)
    props = {
        "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": fg}}},
    }
    if wt and wt > 0:
        props["outline"] = {
            "outlineFill": {"solidFill": {"color": {"rgbColor": bg}}},
            "weight": {"magnitude": pt(wt), "unit": "EMU"},
        }
    else:
        props["outline"] = {"propertyState": "NOT_RENDERED"}
    return {
        "updateShapeProperties": {
            "objectId": oid,
            "fields": "shapeBackgroundFill,outline",
            "shapeProperties": props,
        }
    }


def clr(oid):
    # NOT_RENDERED가 테마 기본값(흰 배경)을 상속할 수 있으므로 alpha=0 투명 fill 명시
    return {
        "updateShapeProperties": {
            "objectId": oid,
            "fields": "outline,shapeBackgroundFill",
            "shapeProperties": {
                "shapeBackgroundFill": {
                    "solidFill": {
                        "color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}},
                        "alpha": 0.0,
                    }
                },
                "outline": {"propertyState": "NOT_RENDERED"},
            },
        }
    }


def txt(oid, text):
    return {"insertText": {"objectId": oid, "insertionIndex": 0, "text": str(text)}}


def paragraph_bullets(oid, preset="BULLET_DISC_CIRCLE_SQUARE"):
    return {
        "createParagraphBullets": {
            "objectId": oid,
            "textRange": {"type": "ALL"},
            "bulletPreset": preset,
        }
    }


def _type_scale(size):
    """
    Remap small / mid typography tiers so the minimum readable size becomes 7pt
    while preserving relative hierarchy.

    Display titles are kept mostly stable; body / caption / label tiers are
    proportionally lifted.
    """
    if size <= 5.5:
        return 7
    if size <= 6:
        return 7.5
    if size <= 6.5:
        return 8
    if size <= 7:
        return 7.5
    if size <= 8:
        return 9.5
    if size <= 8.5:
        return 10
    if size <= 9:
        return 10.5
    if size <= 11:
        return 12.5
    if size <= 13:
        return 14.5
    return size


def txtstyle(oid, color, size, bold=False, ff="Noto Sans"):
    size = _type_scale(size)
    return {
        "updateTextStyle": {
            "objectId": oid,
            "textRange": {"type": "ALL"},
            "style": {
                "foregroundColor": {"opaqueColor": {"rgbColor": color}},
                "fontSize": {"magnitude": size, "unit": "PT"},
                "fontFamily": ff,
                "bold": bold,
            },
            "fields": "foregroundColor,fontSize,fontFamily,bold",
        }
    }


def align(oid, alignment="CENTER"):
    return {
        "updateParagraphStyle": {
            "objectId": oid,
            "textRange": {"type": "ALL"},
            "style": {"alignment": alignment},
            "fields": "alignment",
        }
    }


def bring_to_front(oids):
    if isinstance(oids, str):
        oids = [oids]
    return {
        "updatePageElementsZOrder": {
            "pageElementObjectIds": oids,
            "operation": "BRING_TO_FRONT",
        }
    }


def middle(oid):
    return {
        "updateShapeProperties": {
            "objectId": oid,
            "fields": "contentAlignment",
            "shapeProperties": {"contentAlignment": "MIDDLE"},
        }
    }


def _page_bg(sid, reqs):
    reqs.append({
        "updatePageProperties": {
            "objectId": sid,
            "fields": "pageBackgroundFill",
            "pageProperties": {
                "pageBackgroundFill": {
                    "solidFill": {"color": {"rgbColor": BG}}
                }
            },
        }
    })


def _new_slide(sid, insert_index, reqs, layout_id=None):
    layout_ref = {"layoutId": layout_id} if layout_id else {"predefinedLayout": "BLANK"}
    reqs.append({
        "createSlide": {
            "objectId": sid,
            "insertionIndex": insert_index,
            "slideLayoutReference": layout_ref,
        }
    })
    _page_bg(sid, reqs)


def mk_cover(slide_oid, title, insert_index, reqs, subtitle="",
             department="디자인부문ㅣ패키지디자인팀", owner="한원진 담당",
             date_text="", version="V1.0"):
    """
    Theme-aware standard cover helper.

    Use this for previews / generated decks instead of ad-hoc first-slide text boxes.
    The hierarchy follows the current cover contract:
      - large title block
      - bottom-left department / owner
      - bottom-right date / version
    """
    _new_slide(slide_oid, insert_index, reqs)
    title_text = title if not subtitle else f"{title}\n{subtitle}"
    meta_text = version if not date_text else f"{date_text}\n{version}"
    team_text = department if not owner else f"{department}\n{owner}"

    _text(reqs, slide_oid, f"{slide_oid}_cover_title",
          27.6, 34.3, 594.8, 99.5, title_text, TEXT, 36, False, "Noto Sans")
    _text(reqs, slide_oid, f"{slide_oid}_cover_team",
          27.6, 319.4, 561.4, 50.2, team_text, TEXT, 12, False, "Noto Sans")
    _text(reqs, slide_oid, f"{slide_oid}_cover_meta",
          507.5, 319.4, 176.6, 50.2, meta_text, TEXT, 12, False, "Noto Sans")


def _text(reqs, sid, oid, x, y, w, h, text, color=TEXT, size=8, bold=False,
          ff="Noto Sans", center=False, valign=True):
    reqs.append(shape(oid, sid, "TEXT_BOX", x, y, w, h))
    if text:
        reqs.append(txt(oid, text))
        reqs.append(txtstyle(oid, color, size, bold=bold, ff=ff))
        if center:
            reqs.append(align(oid, "CENTER"))
    reqs.append(clr(oid))
    if valign:
        reqs.append(middle(oid))


def _rect(reqs, sid, oid, x, y, w, h, bg=SURFACE, border=BORDER, wt=0.5):
    reqs += [shape(oid, sid, "RECTANGLE", x, y, w, h), fill(oid, bg, border, wt)]


def _divider(reqs, sid, oid, x, y, w, h=0.5, color=BORDER_HI):
    """Static divider line rendered as a thin rectangle, not a connector."""
    reqs += [shape(oid, sid, "RECTANGLE", x, y, w, h), fill(oid, color, color, 0)]


def _bullet_line(reqs, sid, oid_prefix, x, y, w, text,
                 bullet_color=TEXT_FAINT, text_color=TEXT_DIM,
                 text_size=7, line_h=13, bullet_size=2.5,
                 bullet_gap=8, ff="Noto Sans", bold=False):
    """
    Bullet + text are treated as one logical row.
    The bullet is vertically centered against the first text line area,
    so it never floats too high/low relative to the copy.
    """
    bullet_y = y + max(0, (line_h - bullet_size) / 2)
    reqs += [
        shape(f"{oid_prefix}_dot", sid, "RECTANGLE", x, bullet_y, bullet_size, bullet_size),
        fill(f"{oid_prefix}_dot", bullet_color, bullet_color, 0),
    ]
    _text(
        reqs,
        sid,
        f"{oid_prefix}_text",
        x + bullet_size + bullet_gap,
        y,
        w - bullet_size - bullet_gap,
        line_h,
        text,
        text_color,
        text_size,
        bold,
        ff,
    )


def _bulleted_text_box(reqs, sid, oid, x, y, w, h, items,
                       color=TEXT_DIM, size=7, ff="Noto Sans",
                       bold=False, preset="BULLET_DISC_CIRCLE_SQUARE"):
    """
    Native paragraph bullets inside a single text box.
    Use when bullets are semantically needed and alignment stability matters more
    than custom square-glyph styling.
    """
    text = "\n".join(str(i) for i in items if str(i).strip())
    reqs += [
        shape(oid, sid, "TEXT_BOX", x, y, w, h),
        txt(oid, text),
        paragraph_bullets(oid, preset=preset),
        txtstyle(oid, color, size, bold=bold, ff=ff),
        clr(oid),
    ]


def _contains_korean(text):
    s = str(text or "")
    return any(
        ("\uac00" <= ch <= "\ud7a3")
        or ("\u1100" <= ch <= "\u11ff")
        or ("\u3130" <= ch <= "\u318f")
        for ch in s
    )


def _header(sid, reqs, eyebrow="", title="", page_no=None, total=None, footer="", eyebrow_dim=False):
    if eyebrow:
        # 한국어 포함 → Noto Sans, 그 외(영문/숫자/기호 혼합) → Proxima Nova
        eyebrow_ff = "Noto Sans" if _contains_korean(eyebrow) else "Proxima Nova"
        _text(reqs, sid, f"{sid}_eyebrow", M, M, 240, 16, eyebrow.upper(),
              ORANGE, 7, True, eyebrow_ff, valign=False)
        if eyebrow_dim:
            reqs.append(fill(f"{sid}_eyebrow", ACCENT_DIM, wt=0))
    if title:
        _text(reqs, sid, f"{sid}_title", M, 54, W - M * 2, 40, title,
              TEXT, 22, True, "Noto Sans", valign=False)
    # Current template direction: no title underline bar, no top page indicator,
    # no bottom footer/year. Keep only eyebrow + title.


def _footer(sid, reqs, text):
    # Footer intentionally disabled for the current clean template.
    return


def _primary_index(items, predicate):
    """Return the single item explicitly allowed to use 100% orange."""
    for i, item in enumerate(items):
        if isinstance(item, dict) and item.get("primary"):
            return i
    for i, item in enumerate(items):
        if predicate(item):
            return i
    return None


def _primary_set(items, predicate):
    """Return set of indices allowed to use 100% orange. Supports multiple primaries.
    Explicit primary=True keys take priority; if none exist, collect all predicate matches.
    """
    result = set()
    for i, item in enumerate(items):
        if isinstance(item, dict) and item.get("primary"):
            result.add(i)
    if result:
        return result
    for i, item in enumerate(items):
        if predicate(item):
            result.add(i)
    return result


def _estimate_lines(text, card_w, chars_per_line_at_100=11):
    """
    Rough line estimator for Korean/English mixed short labels.
    We prefer expanding card height over shrinking font size.
    """
    if not text:
        return 1
    # Normalize by a ~100pt card width baseline.
    capacity = max(6, int(chars_per_line_at_100 * (card_w / 100.0)))
    return max(1, (len(str(text)) + capacity - 1) // capacity)


def _estimate_block_lines(text, card_w, chars_per_line_at_100=11):
    """
    Estimate wrapped line count while respecting explicit line breaks.
    """
    chunks = str(text or "").splitlines() or [""]
    return max(1, sum(_estimate_lines(chunk, card_w, chars_per_line_at_100) for chunk in chunks))


def _cap_text_block(text, card_w, max_lines=4, chars_per_line_at_100=10):
    """
    Keep table copy editable but bounded.
    If text would make the table too tall, compress it to a readable number of lines.
    """
    raw_lines = []
    for part in str(text or "").replace("\n\n", "\n").splitlines():
        part = part.strip()
        if part:
            raw_lines.append(part)
    if not raw_lines:
        return " "
    capacity = max(6, int(chars_per_line_at_100 * (card_w / 100.0)))
    out = []
    truncated = False
    for line_idx, line in enumerate(raw_lines):
        while line:
            out.append(line[:capacity])
            line = line[capacity:]
            if len(out) >= max_lines:
                truncated = bool(line) or line_idx < len(raw_lines) - 1
                break
        if len(out) >= max_lines:
            break
    if truncated and out:
        out[-1] = out[-1].rstrip(" .,") + "…"
    return "\n".join(out[:max_lines])


def _center_group_start(card_y, card_h, group_h, min_pad=8):
    """
    Center a text group vertically when the available padding is tight.
    This encodes the rule:
      "If text area is x, and top/bottom padding is smaller than x,
       keep top/bottom padding visually balanced."
    """
    pad = max(0, (card_h - group_h) / 2)
    if pad < group_h:
        return card_y + max(min_pad, pad)
    return card_y + min_pad


def _top_weighted_group_start(card_y, card_h, group_h, top_pad=14, bottom_bias=10):
    """
    For larger / hero-style cards:
      keep top padding smaller than bottom padding.
    Use when the card should read from the upper area downward.
    """
    max_start = card_y + max(0, card_h - group_h - bottom_bias)
    return min(card_y + top_pad, max_start)


def _face_center(x, y, w, h, side):
    """
    Return the center point of a card face.
    side: left | right | top | bottom
    """
    if side == "left":
        return x, y + h / 2
    if side == "right":
        return x + w, y + h / 2
    if side == "top":
        return x + w / 2, y
    if side == "bottom":
        return x + w / 2, y + h
    return x + w / 2, y + h / 2


def _face_pair_between(src, dst):
    """
    Pick source/destination faces so both endpoints land on face centers.

    src, dst: (x, y, w, h)
    Rule:
      - if horizontal delta dominates, connect left/right face centers
      - if vertical delta dominates, connect top/bottom face centers
    """
    sx, sy, sw, sh = src
    dx, dy, dw, dh = dst
    scx, scy = sx + sw / 2, sy + sh / 2
    dcx, dcy = dx + dw / 2, dy + dh / 2
    vx, vy = dcx - scx, dcy - scy

    if abs(vx) >= abs(vy):
        s_face = "right" if vx >= 0 else "left"
        d_face = "left" if vx >= 0 else "right"
    else:
        s_face = "bottom" if vy >= 0 else "top"
        d_face = "top" if vy >= 0 else "bottom"
    return _face_center(sx, sy, sw, sh, s_face), _face_center(dx, dy, dw, dh, d_face)


def connect_boxes(reqs, sid, oid, src, dst, color=ORANGE, weight=1.0,
                  start_arrow="NONE", end_arrow="FILL_ARROW", category="STRAIGHT"):
    (x1, y1), (x2, y2) = _face_pair_between(src, dst)
    connector(
        reqs, sid, oid,
        x1, y1, x2, y2,
        color=color, weight=weight,
        start_arrow=start_arrow, end_arrow=end_arrow, category=category,
    )


def orth_connector(reqs, sid, oid, x1, y1, x2, y2, color=ORANGE, weight=1.0,
                   lead=28, start_arrow="NONE", end_arrow="FILL_ARROW"):
    """
    Manual orthogonal connector composed from straight line segments.

    Use when Google Slides native BENT connectors visually detach from the
    exact face-center start/end points.
    """
    if abs(y2 - y1) < 0.5:
        connector(reqs, sid, oid, x1, y1, x2, y2,
                  color=color, weight=weight,
                  start_arrow=start_arrow, end_arrow=end_arrow,
                  category="STRAIGHT")
        return

    if x2 >= x1:
        elbow_x = min(x2 - 12, x1 + lead)
    else:
        elbow_x = max(x2 + 12, x1 - lead)

    connector(reqs, sid, f"{oid}_h1", x1, y1, elbow_x, y1,
              color=color, weight=weight,
              start_arrow=start_arrow, end_arrow="NONE",
              category="STRAIGHT")
    connector(reqs, sid, f"{oid}_v", elbow_x, y1, elbow_x, y2,
              color=color, weight=weight,
              start_arrow="NONE", end_arrow="NONE",
              category="STRAIGHT")
    connector(reqs, sid, f"{oid}_h2", elbow_x, y2, x2, y2,
              color=color, weight=weight,
              start_arrow="NONE", end_arrow=end_arrow,
              category="STRAIGHT")


# ─────────────────────────────────────────────────────────────────────
# Public components — current template direction
# ─────────────────────────────────────────────────────────────────────

def slide_base(slide_oid, title_text, insert_index, reqs, theme="dark",
               page_label="", page_no=None, total=None, footer="", eyebrow_dim=False):
    _new_slide(slide_oid, insert_index, reqs)
    _header(
        slide_oid,
        reqs,
        eyebrow=page_label or "",
        title=title_text,
        page_no=page_no,
        total=total,
        footer=footer or title_text,
        eyebrow_dim=eyebrow_dim,
    )


def mk_section_divider(slide_oid, num, title, insert_index, reqs):
    _new_slide(slide_oid, insert_index, reqs)
    _text(reqs, slide_oid, f"{slide_oid}_num", 51, 103, 120, 100, num,
          ORANGE, 80, True, "Proxima Nova")
    # 숫자와 텍스트 영역 사이 세로 구분선
    reqs += [shape(f"{slide_oid}_vline", slide_oid, "RECTANGLE", 174, 155, 1.5, 86),
             fill(f"{slide_oid}_vline", BORDER_HI, BORDER_HI, 0)]
    _text(reqs, slide_oid, f"{slide_oid}_label", 178, 158, 100, 16, "Section",
          TEXT_FAINT, 14.5, False, "Proxima Nova")
    _text(reqs, slide_oid, f"{slide_oid}_title", 178, 174, 380, 64, title,
          TEXT, 28, True, "Noto Sans")
    _footer(slide_oid, reqs, "Section Divider")


def mk_quote(slide_oid, quote_text, insert_index, reqs, attribution=""):
    _new_slide(slide_oid, insert_index, reqs)
    _text(reqs, slide_oid, f"{slide_oid}_quote_mark", 80, 112, 80, 60, "“",
          ORANGE, 80, True, "Proxima Nova")
    _text(reqs, slide_oid, f"{slide_oid}_quote", 80, 155, 560, 76, quote_text,
          TEXT, 24, True, "Noto Sans", center=True)
    if attribution:
        reqs += [shape(f"{slide_oid}_qbar", slide_oid, "RECTANGLE", 250, 259, 2, 20),
                 fill(f"{slide_oid}_qbar", ORANGE, ORANGE, 0)]
        _text(reqs, slide_oid, f"{slide_oid}_attr", 264, 250, 300, 24, attribution,
              TEXT_DIM, 10, False, "Noto Sans")
    _footer(slide_oid, reqs, "Quote · Callout")


def mk_contents(slide_oid, sections, insert_index, reqs):
    _new_slide(slide_oid, insert_index, reqs)
    _header(slide_oid, reqs, eyebrow="Contents", title="목차", footer="Contents")
    y0 = 132
    for i, sec in enumerate(sections[:5]):
        if isinstance(sec, dict):
            num = sec.get("num", f"{i+1:02d}")
            title = sec.get("title", "")
            desc = sec.get("desc", "")
        else:
            num, title = sec[0], sec[1]
            desc = sec[2] if len(sec) > 2 else ""
        y = y0 + i * 46
        reqs += [shape(f"{slide_oid}_line{i}", slide_oid, "RECTANGLE", M, y - 8, W - M * 2, 0.5),
                 fill(f"{slide_oid}_line{i}", BORDER, BORDER, 0)]
        _text(reqs, slide_oid, f"{slide_oid}_num{i}", M, y, 32, 18, num,
              ORANGE, 13, True, "Proxima Nova")
        _text(reqs, slide_oid, f"{slide_oid}_ttl{i}", M + 50, y, 220, 18, title,
              TEXT, 12, True, "Noto Sans")
        if desc:
            _text(reqs, slide_oid, f"{slide_oid}_desc{i}", M + 280, y + 1, 360, 16, desc,
                  TEXT_DIM, 8, False, "Noto Sans")


def mk_3col(sid, cols, reqs, theme="dark", align_mode="top_weighted"):
    """Template-style 3-column card grid."""
    card_w, gap, x0, y0 = 206, 12, M, 128
    visible_cols = cols[:3]
    primary = _primary_index(
        visible_cols,
        lambda c: isinstance(c, dict) and (
            c.get("role") in ("conclusion", "summary")
            or c.get("style") in ("primary", "conclusion", "summary")
        ),
    )
    for i, col in enumerate(visible_cols):
        x = x0 + i * (card_w + gap)
        marked = col.get("primary") or col.get("hot") or col.get("accent")
        hot = i == primary
        dim_hot = marked and not hot
        _rect(reqs, sid, f"{sid}_col{i}", x, y0, card_w, 190,
              ORANGE if hot else (ORANGE_DIM if dim_hot else SURFACE),
              ORANGE if marked else BORDER, 0.5)
        label = col.get("label", f"0{i+1}")
        title = col.get("title", label)
        items = col.get("items", [])
        reason = col.get("reason", "")
        label_h = 12
        title_h = 28
        item_h = 12
        reason_h = 10
        label_gap = 11
        title_gap = 12
        reason_gap = 5
        body_gap = 4
        outer_pad = 16
        group_h = label_h + label_gap + title_h
        if reason:
            group_h += reason_gap + reason_h
        if items:
            group_h += title_gap + item_h * min(5, len(items)) + body_gap * max(0, min(5, len(items)) - 1)
        if align_mode == "balanced":
            start_y = _center_group_start(y0, 190, group_h, min_pad=outer_pad)
        else:
            start_y = _top_weighted_group_start(y0, 190, group_h, top_pad=20, bottom_bias=16)
        cursor_y = start_y
        _text(reqs, sid, f"{sid}_cl{i}", x + 18, cursor_y, card_w - 36, label_h,
              str(label).upper(), WHITE if hot else (ORANGE if dim_hot else TEXT_FAINT), 7, True, "Noto Sans", valign=True)
        cursor_y += label_h + label_gap
        _text(reqs, sid, f"{sid}_ct{i}", x + 18, cursor_y, card_w - 36, title_h,
              title, WHITE if hot else TEXT, 13, True, "Noto Sans", valign=True)
        cursor_y += title_h + (reason_gap if reason else title_gap)
        if reason:
            _text(reqs, sid, f"{sid}_reason{i}", x + 18, cursor_y, card_w - 36, reason_h,
                  reason, WHITE if hot else ORANGE, 7, True, "Noto Sans", valign=True)
            cursor_y += reason_h + title_gap
        if items:
            line_y = cursor_y
            for j, item in enumerate(items[:5]):
                _text(
                    reqs, sid, f"{sid}_items{i}_{j}",
                    x + 18, line_y, card_w - 36, item_h, item,
                    WHITE if hot else TEXT_DIM,
                    7, False, "Noto Sans", valign=True
                )
                line_y += item_h + body_gap


def mk_3col_cards(sid, cards, reqs, theme="dark"):
    normalized = []
    for i, c in enumerate(cards[:3]):
        normalized.append({
            "label": c.get("num", c.get("label", f"0{i+1}")),
            "title": c.get("title", c.get("label", "")),
            "items": (c["body"] if isinstance(c.get("body"), list) else ([c["body"]] if c.get("body") else c.get("items", []))),
            "hot": c.get("hot") or c.get("accent") or c.get("style") == "accent",
            "reason": c.get("reason", ""),
        })
    mk_3col(sid, normalized, reqs, theme=theme)


def mk_rule_grid(sid, cards, reqs, x=M, y=CONTENT_TOP, w=None, cols=2, gap_x=12, gap_y=12, card_h=96):
    """
    Equal-ratio rule/guide cards.

    Use when the page should remain simple:
      - repeated grid cards are okay
      - mixed 3-up + 1-wide patterns are not

    This helper applies:
      - equal card ratios
      - centered text-group padding in tight cards
      - bullet/text row alignment
    """
    visible = cards[: max(1, cols * 2)]
    if not visible:
        return
    w = w or (W - M * 2)
    rows = (len(visible) + cols - 1) // cols
    label_gap = 8
    title_gap = 10
    body_gap = 4
    outer_pad = 16
    max_group_h = 0
    for card in visible:
        label = card.get("label", "")
        title = card.get("title", "")
        lines = card.get("lines", [])
        label_h = 10 if label else 0
        title_h = 18 if title else 0
        line_h = 10
        group_h = 0
        if label:
            group_h += label_h
        if title:
            if group_h:
                group_h += label_gap
            group_h += title_h
        if lines:
            if group_h:
                group_h += title_gap
            group_h += line_h * len(lines) + body_gap * max(0, len(lines) - 1)
        max_group_h = max(max_group_h, group_h)
    # Keep top/bottom padding larger than inner gaps.
    card_h = max(card_h, max_group_h + outer_pad * 2)
    card_w = (w - gap_x * (cols - 1)) / cols
    total_h = rows * card_h + gap_y * (rows - 1)
    if y + total_h > CONTENT_BOTTOM:
        fitted = max(72, (CONTENT_BOTTOM - y - gap_y * max(0, rows - 1)) / rows)
        card_h = max(fitted, max_group_h + outer_pad * 2)
    for i, card in enumerate(visible):
        row = i // cols
        col = i % cols
        xx = x + col * (card_w + gap_x)
        yy = y + row * (card_h + gap_y)
        marked = bool(card.get("primary") or card.get("accent") or card.get("hot"))
        fill_color = ORANGE if card.get("primary") else (ORANGE_DIM if card.get("accent_bg") else SURFACE)
        border_color = ORANGE if marked or card.get("accent_bg") else BORDER
        _rect(reqs, sid, f"{sid}_rulegrid_box_{i}", xx, yy, card_w, card_h, fill_color, border_color, 0.5)

        label = card.get("label", "").upper()
        title = card.get("title", "")
        lines = card.get("lines", [])

        label_h = 10 if label else 0
        title_h = 18 if title else 0
        bullet_h = 10
        parts = ([label_h] if label else []) + ([title_h] if title else []) + ([bullet_h] * len(lines))
        group_h = _stack_group_height(parts, gap=8)
        start_y = _center_group_start(yy, card_h, group_h, min_pad=outer_pad)

        cursor_y = start_y
        if label:
            _text(
                reqs, sid, f"{sid}_rulegrid_label_{i}",
                xx + 16, cursor_y, card_w - 32, label_h, label,
                ORANGE if marked or card.get("accent_bg") else TEXT_FAINT,
                7, True, "Noto Sans", valign=True
            )
            cursor_y += label_h + label_gap

        if title:
            _text(
                reqs, sid, f"{sid}_rulegrid_title_{i}",
                xx + 16, cursor_y, card_w - 32, title_h, title,
                BLACK if card.get("primary") else TEXT,
                11, True, "Noto Sans", valign=True
            )
            cursor_y += title_h + title_gap

        for j, line in enumerate(lines):
            _text(
                reqs, sid, f"{sid}_rulegrid_line_{i}_{j}",
                xx + 16, cursor_y, card_w - 32, bullet_h, line,
                BLACK if card.get("primary") else TEXT_DIM,
                7, False, "Noto Sans", valign=True
            )
            cursor_y += bullet_h + body_gap


def mk_flow(sid, steps, cost_map=None, reqs=None, theme="dark"):
    """Dynamic-height horizontal process flow. Returns computed card height (ch)."""
    if reqs is None:
        raise ValueError("reqs is required")
    cost_map = cost_map or {}
    visible_steps = steps[:6]
    n = len(visible_steps)
    gap = 12 if n <= 4 else 8
    x0, y0 = 54, 132
    total_w = 612
    cw = (total_w - gap * max(0, n - 1)) / max(1, n)
    bw = cw - 16  # inner text width

    # chars-per-100pt for rendered font sizes
    ST_CPL100 = 13  # name: rendered ~9.5pt
    SV_CPL100 = 18  # service: rendered ~7pt
    SD_CPL100 = 18  # desc: rendered ~7pt

    PAD = 8      # top and bottom padding
    SN_H = 10    # sn fixed height
    ST_LH = 14   # name line-height
    SV_LH = 10   # service line-height
    SD_LH = 10   # desc line-height
    GAP_SEP = 5  # gap before/after separator line
    COST_H = 32  # fixed block for cost section

    # ── Pass 1a: unified top-section height (sn+st+sv max across all cards) ──
    max_top_h = PAD + SN_H
    for idx, step in enumerate(visible_steps):
        if isinstance(step, dict):
            name = step.get("name", step.get("title", ""))
            svc  = step.get("service", step.get("infra", ""))
        else:
            _, name, svc, _ = step[:4]
        st_lines = _estimate_block_lines(name, bw, ST_CPL100) if name else 1
        sv_lines = _estimate_block_lines(svc, bw, SV_CPL100) if svc else 1
        top_h = PAD + SN_H + st_lines * ST_LH + sv_lines * SV_LH
        max_top_h = max(max_top_h, top_h)

    # ── Pass 1b: max card height using unified max_top_h as base ────────────
    max_ch = 72
    for idx, step in enumerate(visible_steps):
        if isinstance(step, dict):
            desc = step.get("desc", step.get("detail", ""))
            cost = step.get("cost", cost_map.get(idx, ""))
        else:
            desc = ""
            cost = cost_map.get(idx, "")
        h = max_top_h
        if desc and not cost:
            sd_lines = _estimate_block_lines(desc, bw, SD_CPL100)
            h += GAP_SEP + 1 + GAP_SEP + sd_lines * SD_LH
        elif desc and cost:
            sd_lines = _estimate_block_lines(desc, bw, SD_CPL100)
            h += sd_lines * SD_LH
        if cost:
            h += COST_H
        h += PAD
        max_ch = max(max_ch, h)
    ch = min(round(max_ch), 405 - y0 - 8)

    # ── Pass 2: render with computed ch ──────────────────────────────
    def _is_marked(step):
        if isinstance(step, dict):
            return (
                step.get("role") in ("conclusion", "summary")
                or step.get("style") in ("primary", "conclusion", "summary")
                or bool(step.get("hot"))
            )
        return False

    primary = _primary_index(visible_steps, _is_marked)

    for i, step in enumerate(visible_steps):
        if isinstance(step, dict):
            num = step.get("num", f"{i+1:02d}")
            name = step.get("name", step.get("title", ""))
            svc  = step.get("service", step.get("infra", ""))
            desc = step.get("desc", step.get("detail", ""))
            cost = step.get("cost", cost_map.get(i, ""))
            cost_label = step.get("cost_label", "월 예상 비용")
            paid = step.get("paid", step.get("hot", bool(cost and cost != "무료")))
            marked = step.get("primary") or step.get("hot") or step.get("accent") or paid
        else:
            raw_step, name, svc, paid = step[:4]
            num = str(raw_step).replace("STEP", "").strip() or f"{i+1:02d}"
            desc = ""
            cost = cost_map.get(i, "")
            cost_label = "월 예상 비용"
            marked = paid

        is_primary = i == primary
        dim_hot = marked and not is_primary
        x = x0 + i * (cw + gap)

        _rect(reqs, sid, f"{sid}_step{i}", x, y0, cw, ch,
              ORANGE if is_primary else (ORANGE_DIM if dim_hot else SURFACE),
              ORANGE if marked else BORDER, 0.5)

        # sn — fixed at top
        _text(reqs, sid, f"{sid}_sn{i}", x + 8, y0 + PAD, bw, SN_H,
              f"STEP {num}", WHITE if is_primary else (ORANGE if dim_hot else TEXT_FAINT), 5, False, "Proxima Nova")

        # st — fixed anchor below sn
        st_y = y0 + PAD + SN_H
        st_lines = _estimate_block_lines(name, bw, ST_CPL100) if name else 1
        st_h = st_lines * ST_LH
        _text(reqs, sid, f"{sid}_st{i}", x + 8, st_y, bw, st_h,
              name, WHITE if is_primary else TEXT, 8, True, "Noto Sans")

        # sv — directly below st (dynamic y)
        sv_y = st_y + st_h
        sv_lines = _estimate_block_lines(svc, bw, SV_CPL100) if svc else 1
        sv_h = sv_lines * SV_LH
        _text(reqs, sid, f"{sid}_sv{i}", x + 8, sv_y, bw, sv_h,
              svc, WHITE if is_primary else TEXT_DIM, 5, False, "Noto Sans")

        # desc area — sep and sd anchored to unified max_top_h (same y across all cards)
        if desc:
            if not cost:
                sep_y = y0 + max_top_h + GAP_SEP
                sep_c = WHITE if is_primary else (ORANGE if dim_hot else BORDER_HI)
                reqs += [shape(f"{sid}_sep_hd{i}", sid, "RECTANGLE", x + 8, sep_y, bw, 0.5),
                         fill(f"{sid}_sep_hd{i}", sep_c, sep_c, 0)]
                sd_y = sep_y + 1 + GAP_SEP
                sd_lines = _estimate_block_lines(desc, bw, SD_CPL100)
                sd_h = sd_lines * SD_LH
                _text(reqs, sid, f"{sid}_sd{i}", x + 8, sd_y, bw, sd_h,
                      desc, WHITE if is_primary else TEXT_DIM, 5, False, "Noto Sans")
            else:
                sd_lines = _estimate_block_lines(desc, bw, SD_CPL100)
                sd_h = sd_lines * SD_LH
                _text(reqs, sid, f"{sid}_sd{i}", x + 8, y0 + max_top_h, bw, sd_h,
                      desc, WHITE if is_primary else TEXT_DIM, 5, False, "Noto Sans")

        # cost section — anchored at bottom of card
        if cost:
            cost_y = y0 + ch - COST_H
            reqs += [shape(f"{sid}_sep{i}", sid, "RECTANGLE", x + 8, cost_y, bw, 0.5),
                     fill(f"{sid}_sep{i}",
                          WHITE if is_primary else (ORANGE if dim_hot else BORDER_HI),
                          WHITE if is_primary else (ORANGE if dim_hot else BORDER_HI), 0)]
            _text(reqs, sid, f"{sid}_costl{i}", x + 8, cost_y + 4, bw, 8,
                  cost_label, WHITE if is_primary else (ORANGE if dim_hot else TEXT_FAINT), 4, False, "Noto Sans")
            _text(reqs, sid, f"{sid}_cost{i}", x + 8, cost_y + 12, bw, 10,
                  cost, WHITE if is_primary else TEXT, 7, True, "Noto Sans")

        # arrow — vertically centered
        if i < min(len(steps), 6) - 1:
            _text(reqs, sid, f"{sid}_arr{i}", x + cw - 5, y0 + ch // 2 - 4, 10, 8,
                  "›", TEXT_FAINT, 5, False, "Proxima Nova", center=True)

    return ch


def mk_flow_focus(sid, steps, reqs, x=54, y=136, w=612, cols=3):
    """
    Larger, template-like flow layout for pages where process itself is the main message.

    Compared with mk_flow():
        - bigger cards
        - single-row horizontal flow
        - larger titles/body for proposal / overview decks
        - no lower cost/table area
    """
    visible_steps = steps[:6]
    if not visible_steps:
        return
    cols = len(visible_steps)
    gap_x = 8
    card_w = (w - gap_x * (cols - 1)) / cols
    max_group_h = 0
    for step in visible_steps:
        if isinstance(step, dict):
            name = step.get("name", step.get("title", ""))
            svc = step.get("service", step.get("infra", ""))
        else:
            name = step[1] if len(step) > 1 else ""
            svc = step[2] if len(step) > 2 else ""
        title_lines = _estimate_lines(name, card_w - 24, chars_per_line_at_100=8)
        svc_lines = _estimate_lines(svc, card_w - 24, chars_per_line_at_100=10) if svc else 0
        num_h = 18
        title_h = 16 * title_lines
        svc_h = 14 * svc_lines if svc else 0
        group_h = num_h + 8 + title_h + (8 + svc_h if svc else 0)
        max_group_h = max(max_group_h, group_h)
    card_h = max(96, max_group_h + 28)
    card_h = _fit_height_to_content(y, card_h, min_h=72)
    primary_set = _primary_set(
        visible_steps,
        lambda s: isinstance(s, dict) and (
            s.get("role") in ("conclusion", "summary")
            or s.get("style") in ("primary", "conclusion", "summary")
        ),
    )
    for i, step in enumerate(visible_steps):
        xx = x + i * (card_w + gap_x)
        yy = y
        if isinstance(step, dict):
            num = step.get("num", f"{i+1:02d}")
            name = step.get("name", step.get("title", ""))
            svc = step.get("service", step.get("infra", ""))
            # style="auto"/"system": 자동 처리 step — 배경 동일하되 name 텍스트 dim 처리
            auto = step.get("style") in ("auto", "system")
            marked = step.get("primary") or step.get("accent") or step.get("hot") or (i in primary_set)
        else:
            raw_step, name, svc = step[:3]
            num = str(raw_step).replace("STEP", "").strip() or f"{i+1:02d}"
            auto = False
            marked = False
        # primary가 여러 개여도 첫 번째만 풀 오렌지 — 동시 2개 이상 ACCENT 금지
        primary_main = min(primary_set) if primary_set else -1
        hot = i == primary_main
        dim_hot = marked and not hot
        title_size = 10
        title_lines = _estimate_lines(name, card_w - 24, chars_per_line_at_100=8)
        title_h = 16 * title_lines
        svc_lines = _estimate_lines(svc, card_w - 24, chars_per_line_at_100=10) if svc else 0
        svc_h = 14 * svc_lines if svc else 0
        num_h = 18
        heights = [num_h, title_h] + ([svc_h] if svc else [])
        group_h = _stack_group_height(heights, gap=8)
        start_y = _top_weighted_group_start(yy, card_h, group_h, top_pad=14, bottom_bias=14)
        num_y = start_y
        title_y = num_y + num_h + 8
        svc_y = title_y + title_h + 8
        _rect(reqs, sid, f"{sid}_focus_bg{i}", xx, yy, card_w, card_h,
              ORANGE if hot else (ORANGE_DIM if dim_hot else SURFACE),
              ORANGE if marked else BORDER, 0.5)
        _text(reqs, sid, f"{sid}_focus_num{i}", xx + 12, num_y, 56, num_h,
              f"STEP {num}", WHITE if hot else (ORANGE if dim_hot else TEXT_FAINT),
              7, True, "Proxima Nova", valign=True)
        _text(reqs, sid, f"{sid}_focus_title{i}", xx + 12, title_y, card_w - 24, title_h,
              name, WHITE if hot else (TEXT_DIM if auto else TEXT), title_size, True, "Noto Sans", valign=True)
        if svc:
            _text(reqs, sid, f"{sid}_focus_svc{i}", xx + 12, svc_y, card_w - 24, svc_h,
                  svc, WHITE if hot else TEXT_DIM, 7, False, "Noto Sans", valign=True)
        if i < len(visible_steps) - 1:
            nx = x + (i + 1) * (card_w + gap_x)
            x1, y1 = _face_center(xx, yy, card_w, card_h, "right")
            x2, y2 = _face_center(nx, yy, card_w, card_h, "left")
            connector(
                reqs, sid, f"{sid}_focus_arrow{i}",
                x1, y1, x2, y2,
                color=BORDER_HI,
                weight=1.0,
                start_arrow="NONE",
                end_arrow="FILL_ARROW",
            )


def mk_text_block(sid, body_text, reqs, y_start=128, font_size=10, theme="dark"):
    box_h = _fit_height_to_content(y_start, 170, min_h=72)
    _rect(reqs, sid, f"{sid}_bodybox", M, y_start, W - M * 2, box_h, SURFACE, BORDER, 0.5)
    _text(reqs, sid, f"{sid}_body", M + 20, y_start + 22, W - M * 2 - 40, max(18, box_h - 44),
          body_text, TEXT_DIM, font_size, False, "Noto Sans")


def mk_split(sid, left, right, reqs, theme="dark", arrow=True):
    # body는 문자열이어야 함 — 리스트로 넘어온 경우 자동 변환
    if isinstance(left.get("body"), list):
        left = {**left, "body": "\n".join(left["body"])}
    if isinstance(right.get("body"), list):
        right = {**right, "body": "\n".join(right["body"])}
    left_x = 54
    top_y = 120
    card_w = 278
    card_h = 236
    right_x = 388
    body_w = 242
    _rect(reqs, sid, f"{sid}_leftbox", left_x, top_y, card_w, card_h, SURFACE, BORDER, 0.5)
    _rect(reqs, sid, f"{sid}_rightbox", right_x, top_y, card_w, card_h, ORANGE_DIM, ORANGE, 0.5)
    _text(reqs, sid, f"{sid}_lt", left_x + 18, top_y + 24, body_w, 24, left.get("title", ""),
          TEXT, 14, True)
    _text(reqs, sid, f"{sid}_lb", left_x + 18, top_y + 66, body_w, 136, left.get("body", ""),
          TEXT_DIM, 8, False)
    _text(reqs, sid, f"{sid}_rt", right_x + 18, top_y + 24, body_w, 24, right.get("title", ""),
          TEXT, 14, True)
    _text(reqs, sid, f"{sid}_rb", right_x + 18, top_y + 66, body_w, 136, right.get("body", ""),
          TEXT_DIM, 8, False)
    if arrow:
        _text(reqs, sid, f"{sid}_arrow", 348, 228, 16, 16, "›", ORANGE, 11, True, center=True)


def mk_title_accent(sid, accent_part, rest_part, reqs, theme="dark",
                    subtitle="", y=54, font_size=22):
    full = accent_part + rest_part
    oid = f"{sid}_title_accent"
    reqs += [shape(oid, sid, "TEXT_BOX", M, y, W - M * 2, 42), txt(oid, full)]
    reqs.append(txtstyle(oid, TEXT, font_size, bold=True, ff="Noto Sans"))
    reqs.append({
        "updateTextStyle": {
            "objectId": oid,
            "textRange": {"type": "FIXED_RANGE", "startIndex": 0, "endIndex": len(accent_part)},
            "style": {"foregroundColor": {"opaqueColor": {"rgbColor": ORANGE}}},
            "fields": "foregroundColor",
        }
    })
    reqs.append(clr(oid))
    if subtitle:
        _text(reqs, sid, f"{sid}_title_sub", M, y + 45, W - M * 2, 18,
              subtitle, TEXT_DIM, 8, False)


def mk_toc(slide_oid, items, insert_index, reqs, category="", year="",
           title_accent="Table Of", title_rest=" Content", description=""):
    _new_slide(slide_oid, insert_index, reqs)
    if category:
        _text(reqs, slide_oid, f"{slide_oid}_cat", M, 30, 240, 10,
              category.upper(), ORANGE, 7, True, "Proxima Nova")
    if year:
        _text(reqs, slide_oid, f"{slide_oid}_year", W - M - 60, 30, 60, 10,
              str(year), TEXT_FAINT, 7, False, "Proxima Nova")
    mk_title_accent(slide_oid, title_accent, title_rest, reqs, y=54, font_size=24)
    if description:
        _text(reqs, slide_oid, f"{slide_oid}_desc", M, 92, W - M * 2, 16,
              description, TEXT_DIM, 7, False)
    y0 = 140
    for i, item in enumerate(items[:6]):
        col = 0 if i < 3 else 1
        row = i if i < 3 else i - 3
        x = M + col * 335
        y = y0 + row * 56
        title = item.get("title", "") if isinstance(item, dict) else item[0]
        desc = item.get("desc", "") if isinstance(item, dict) else (item[1] if len(item) > 1 else "")
        reqs += [shape(f"{slide_oid}_ln{i}", slide_oid, "RECTANGLE", x, y - 8, 300, 0.5),
                 fill(f"{slide_oid}_ln{i}", BORDER, BORDER, 0)]
        _text(reqs, slide_oid, f"{slide_oid}_arr{i}", x, y, 16, 14, "→",
              ORANGE, 9, True, "Proxima Nova")
        _text(reqs, slide_oid, f"{slide_oid}_it{i}", x + 24, y, 130, 14, title,
              TEXT, 9, True)
        _text(reqs, slide_oid, f"{slide_oid}_id{i}", x + 24, y + 16, 260, 20, desc,
              TEXT_DIM, 7, False)
    _footer(slide_oid, reqs, "Table Of Content")


def mk_split_cards(sid, text_lines, cards, reqs, theme="dark"):
    x0, y0 = M, 140
    for i, line in enumerate(text_lines[:5]):
        _text(reqs, sid, f"{sid}_tl{i}", x0, y0 + i * 24, 260, 18,
              line, TEXT_DIM, 9, False)
    card_x, card_w, card_h, gap = 370, 314, 44, 8
    visible_cards = cards[:4]
    primary = _primary_index(
        visible_cards,
        lambda c: isinstance(c, dict) and (
            c.get("role") in ("conclusion", "summary")
            or c.get("style") in ("primary", "conclusion", "summary")
        ),
    )
    for i, card in enumerate(visible_cards):
        y = y0 + i * (card_h + gap)
        style = card.get("style", "")
        marked = card.get("primary") or style == "accent" or card.get("hot") or card.get("accent")
        hot = i == primary
        dim_hot = marked and not hot
        _rect(reqs, sid, f"{sid}_sc{i}", card_x, y, card_w, card_h,
              ORANGE if hot else (ORANGE_DIM if dim_hot else SURFACE),
              ORANGE if marked else BORDER, 0.5)
        _text(reqs, sid, f"{sid}_sct{i}", card_x + 18, y + 13, card_w - 36, 18,
              card.get("label", card.get("title", "")), BLACK if hot else TEXT, 10, True, center=True)


# Convenience aliases for template-like cases.
def mk_summary(slide_oid, message, insert_index, reqs, attribution=""):
    mk_quote(slide_oid, message, insert_index, reqs, attribution)


def mk_feature_grid(sid, cards, reqs, theme="dark"):
    mk_3col_cards(sid, cards, reqs, theme)


def mk_kpi_dashboard(sid, kpis, reqs, y=128):
    """
    kpis = [
        {"label": "처리 건수", "value": "1,248", "sub": "월 누적", "hot": True},
        ...
    ]
    """
    count = min(len(kpis), 4)
    if count <= 0:
        return
    gap = 12
    card_w = (W - M * 2 - gap * (count - 1)) / count
    card_h = _fit_height_to_content(y, 128, min_h=84)
    visible_kpis = kpis[:count]
    primary = _primary_index(
        visible_kpis,
        lambda k: isinstance(k, dict) and (
            k.get("role") in ("conclusion", "summary")
            or k.get("style") in ("primary", "conclusion", "summary")
        ),
    )
    for i, k in enumerate(visible_kpis):
        x = M + i * (card_w + gap)
        marked = k.get("primary") or k.get("hot") or k.get("accent")
        hot = i == primary
        dim_hot = marked and not hot
        _rect(reqs, sid, f"{sid}_kpi_bg{i}", x, y, card_w, card_h,
              ORANGE if hot else (ORANGE_DIM if dim_hot else SURFACE),
              ORANGE if marked else BORDER, 0.5)
        _text(reqs, sid, f"{sid}_kpi_label{i}", x + 14, y + 18, card_w - 28, 12,
              k.get("label", ""), BLACK if hot else (ORANGE if dim_hot else TEXT_FAINT), 7, True, "Noto Sans")
        _text(reqs, sid, f"{sid}_kpi_value{i}", x + 14, y + 46, card_w - 28, 40,
              k.get("value", ""), BLACK if hot else TEXT, 26, True, "Proxima Nova")
        _text(reqs, sid, f"{sid}_kpi_sub{i}", x + 14, y + 91, card_w - 28, 20,
              k.get("sub", ""), BLACK if hot else TEXT_DIM, 7, False, "Noto Sans")


def mk_bar_chart(sid, bars, reqs, x=M, y=144, w=420, h=150,
                 title="성과 추이", value_suffix="", max_value=None, key="chart"):
    """
    bars = [
        {"label": "1월", "value": 72, "accent": False},
        {"label": "2월", "value": 88, "accent": True},
    ]
    """
    if not bars:
        return
    prefix = f"{sid}_{key}"
    max_v = max_value or max(float(b.get("value", 0)) for b in bars) or 1
    _text(reqs, sid, f"{prefix}_title", x, y - 28, w, 16,
          title, TEXT, 9, True, "Noto Sans")
    reqs += [shape(f"{prefix}_axis", sid, "RECTANGLE", x, y + h, w, 0.5),
             fill(f"{prefix}_axis", BORDER_HI, BORDER_HI, 0)]
    gap = 10
    bw = (w - gap * (len(bars) - 1)) / len(bars)
    for i, b in enumerate(bars):
        val = float(b.get("value", 0))
        bh = max(2, h * val / max_v)
        bx = x + i * (bw + gap)
        by = y + h - bh
        hot = b.get("accent", i == len(bars) - 1)
        _rect(reqs, sid, f"{prefix}_bar{i}", bx, by, bw, bh,
              ORANGE if hot else SURFACE_HI, ORANGE if hot else BORDER, 0.3)
        _text(reqs, sid, f"{prefix}_val{i}", bx - 6, by - 17, bw + 12, 12,
              f"{int(val) if val.is_integer() else val:g}{value_suffix}",
              ORANGE if hot else TEXT_DIM, 7, True, "Proxima Nova", center=True)
        _text(reqs, sid, f"{prefix}_lab{i}", bx - 6, y + h + 8, bw + 12, 12,
              b.get("label", ""), TEXT_FAINT, 7, False, "Noto Sans", center=True)


def mk_report_table(sid, rows, reqs, x=M, y=138, w=648):
    """
    rows = [
        {"metric": "처리 시간", "before": "수분~수십분", "after": "약 100초", "impact": "–90%", "hot": True},
        ...
    ]
    """
    col = [0.23, 0.27, 0.28, 0.22]
    xs = [x]
    for ratio in col[:-1]:
        xs.append(xs[-1] + w * ratio)
    ws = [w * r for r in col]
    header_h, row_h = 24, 36
    headers = ["지표", "도입 전", "도입 후", "성과"]
    max_rows = max(1, int((_fit_height_to_content(y, CONTENT_BOTTOM - y, min_h=60) - header_h) // row_h))
    rows = rows[:max_rows]
    _rect(reqs, sid, f"{sid}_tbl_head_bg", x, y, w, header_h, SURFACE_HI, BORDER_HI, 0.5)
    for i, head in enumerate(headers):
        _text(reqs, sid, f"{sid}_tbl_head{i}", xs[i] + 10, y + 7, ws[i] - 20, 10,
              head, TEXT_FAINT, 7, True, "Noto Sans", valign=True)
    visible_rows = rows[:5]
    primary = _primary_index(
        visible_rows,
        lambda row: isinstance(row, dict) and (
            row.get("role") in ("conclusion", "summary")
            or row.get("style") in ("primary", "conclusion", "summary")
        ),
    )
    for r, row in enumerate(visible_rows):
        ry = y + header_h + r * row_h
        marked = row.get("primary") or row.get("hot") or row.get("accent")
        hot = r == primary
        dim_hot = marked and not hot
        _rect(reqs, sid, f"{sid}_tbl_rowbg{r}", x, ry, w, row_h,
              ORANGE if hot else (ORANGE_DIM if dim_hot else SURFACE),
              ORANGE if marked else BORDER, 0.4)
        vals = [row.get("metric", ""), row.get("before", ""), row.get("after", ""), row.get("impact", "")]
        for c, val in enumerate(vals):
            color = BLACK if hot else (TEXT if c in (0, 2, 3) else TEXT_DIM)
            bold = c in (0, 3)
            _text(reqs, sid, f"{sid}_tbl_{r}_{c}", xs[c] + 10, ry + 11, ws[c] - 20, 13,
                  val, color, 7, bold, "Noto Sans", valign=True)


def mk_kpi_status_detail(sid, reqs, eyebrow="APPENDIX", title="KPI 진행 현황",
                         x=54, y=96, w=612, summary_title=None, summary_groups=None,
                         summary_headers=None, summary_rows=None,
                         detail_title=None, detail_headers=None, detail_rows=None):
    """
    Dense appendix/report table page.

    Use for:
      - KPI summary tables
      - definition / formula appendix pages
      - report-style dense reference sheets

    summary_groups format:
      [("KPI 정보", 0, 4), ("상반기 목표/실적", 4, 3), ...]

    detail_rows format:
      [
        ["협업 업무 만족도", "정의 ...", "측정식 ..."],
        ...
      ]
    """
    _header(sid, reqs, eyebrow=eyebrow, title=title)

    summary_title = summary_title or None
    summary_groups = summary_groups or [
        ("KPI 정보", 0, 3),
        ("상반기 목표/실적", 3, 3),
        ("연간 목표/실적", 6, 3),
    ]
    summary_headers = summary_headers or [
        "목표", "KPI", "가중치", "목표", "실적", "달성률", "목표", "실적", "달성률"
    ]
    summary_rows = summary_rows or [
        {
            "goal": "브랜드 가치 향상을 위한 전략 디자인 제공",
            "goal_span": 2,
            "kpi": "협업 만족도 조사",
            "weight": "30%",
            "half_target": "유관부서 만족도 2.7/3",
            "half_actual": "",
            "half_rate": "",
            "year_target": "유관부서 만족도 2.8/3",
            "year_actual": "",
            "year_rate": "",
        },
        {
            "goal_cont": True,
            "kpi": "전략콘텐츠 기여도 조사",
            "weight": "20%",
            "half_target": "영업·마케팅 부서 설문조사 2.7/3",
            "half_actual": "",
            "half_rate": "",
            "year_target": "영업·마케팅 부서 설문조사 2.8/3",
            "year_actual": "",
            "year_rate": "",
        },
        {
            "goal": "안정적인 공급",
            "kpi": "오류건수 & 품질 이슈",
            "weight": "50%",
            "half_target": "3건 이하",
            "half_actual": "",
            "half_rate": "",
            "year_target": "6건 이하",
            "year_actual": "",
            "year_rate": "",
        },
    ]
    detail_title = detail_title or "■ KPI 세부정보"
    detail_headers = detail_headers or ["KPI", "정의", "측정산식", "증빙"]
    detail_rows = detail_rows or [
        {
            "kpi": "협업 만족도 조사",
            "definition": "패키지 품질과 협업 만족도를 조사해\n업무 기여도를 평가한다.",
            "formula": "유관부서 설문 평균 점수\n목표 2.7/3",
            "evidence": "설문조사 결과 자료",
        },
        {
            "kpi": "전략콘텐츠 기여도 설문조사",
            "definition": "디자인이 전략제품의 매출/브랜드 가치 향상에\n기여했는지 의견으로 확인한다.",
            "formula": "영업·마케팅 설문 점수\n전략콘텐츠 기여 의견",
            "evidence": "설문조사 결과 자료",
        },
        {
            "kpi": "오류건수 & 신규패키지 품질이슈",
            "definition": "오타·정보오류·품질 이슈 등\n개선이 필요한 케이스를 관리한다.",
            "formula": "발생 건수(먼데이)\n+ 부서 확인 건수",
            "evidence": "먼데이 이력 + 부서 확인 기록",
        },
    ]

    table_fill = SURFACE if CURRENT_THEME == "dark" else WHITE
    table_head_fill = SURFACE_HI if CURRENT_THEME == "dark" else WHITE
    table_border = BORDER_HI if CURRENT_THEME == "dark" else BORDER

    # Native editable table path.
    top_y = y
    if summary_title:
        _text(reqs, sid, f"{sid}_sec1", x, y, w, 12, summary_title, TEXT, 8, True, "Noto Sans")
        top_y += 18

    col_ratios = [0.165, 0.155, 0.06, 0.185, 0.06, 0.06, 0.185, 0.06, 0.07]
    col_xs, col_ws = _grid_columns(x, w, col_ratios)
    row_heights = []
    for row in summary_rows[:3]:
        cell_values = [
            row.get("kpi", ""),
            row.get("weight", ""),
            row.get("half_target", ""),
            row.get("half_actual", ""),
            row.get("half_rate", ""),
            row.get("year_target", ""),
            row.get("year_actual", ""),
            row.get("year_rate", ""),
        ]
        max_lines = max(
            _estimate_block_lines(val or " ", width - 8, 10)
            for val, width in zip(cell_values, col_ws[1:])
        )
        row_heights.append(max(28, 8 + max_lines * 8))
    for idx, row in enumerate(summary_rows[:3]):
        span = int(row.get("goal_span", 1))
        goal = row.get("goal", "")
        if goal and span > 1:
            needed = max(36, 8 + _estimate_block_lines(goal, col_ws[0] - 12, 10) * 8)
            current = sum(row_heights[idx:idx + span])
            if needed > current:
                extra = needed - current
                for off in range(span):
                    row_heights[idx + off] += extra / span

    top_row_heights = [20, 20] + row_heights
    top_h = sum(top_row_heights)
    top_tbl = f"{sid}_kpi_top_tbl"
    reqs.append(table(top_tbl, sid, 5, 9, x, top_y, w, top_h))
    for ci, width in enumerate(col_ws):
        reqs.append(table_col_width(top_tbl, ci, width))
    for ri, height in enumerate(top_row_heights):
        reqs.append(table_row_height(top_tbl, ri, height))
    reqs += [
        merge_cells(top_tbl, 0, 0, 1, 3),
        merge_cells(top_tbl, 0, 3, 1, 3),
        merge_cells(top_tbl, 0, 6, 1, 3),
        merge_cells(top_tbl, 2, 0, 2, 1),
    ]
    reqs += [
        table_cell_fill(top_tbl, 0, 0, 1, 3, table_head_fill),
        table_cell_fill(top_tbl, 0, 3, 1, 3, table_head_fill),
        table_cell_fill(top_tbl, 0, 6, 1, 3, table_head_fill),
    ]
    for ci in range(9):
        reqs.append(table_cell_fill(top_tbl, 1, ci, 1, 1, table_fill))
    for ri in range(2, 5):
        for ci in range(9):
            reqs.append(table_cell_fill(top_tbl, ri, ci, 1, 1, table_fill))

    top_group_labels = [("KPI 정보", 0), ("상반기 목표/실적", 3), ("연간 목표/실적", 6)]
    for label, ci in top_group_labels:
        table_cell_text(reqs, top_tbl, 0, ci, label, TEXT, 7, True, "Noto Sans", center=True)
    for ci, head in enumerate(summary_headers):
        table_cell_text(reqs, top_tbl, 1, ci, head, TEXT, 7, True, "Noto Sans", center=True)

    # merged goal cells
    table_cell_text(reqs, top_tbl, 2, 0, summary_rows[0].get("goal", ""), TEXT, 7.5, True, "Noto Sans", center=True)
    table_cell_text(reqs, top_tbl, 4, 0, summary_rows[2].get("goal", ""), TEXT, 7.5, True, "Noto Sans", center=True)
    top_value_keys = ["kpi", "weight", "half_target", "half_actual", "half_rate", "year_target", "year_actual", "year_rate"]
    for r, row in enumerate(summary_rows[:3], start=2):
        for ci, key in enumerate(top_value_keys, start=1):
            table_cell_text(
                reqs, top_tbl, r, ci, row.get(key, ""),
                TEXT, 7.5 if ci == 1 else 7, ci == 1, "Noto Sans", center=True
            )

    sec2_y = top_y + top_h + 14
    _text(reqs, sid, f"{sid}_sec2", x, sec2_y, w, 12, detail_title, TEXT, 8, True, "Noto Sans")
    detail_y = sec2_y + 14
    detail_ratios = [0.19, 0.32, 0.30, 0.19]
    _, detail_ws = _grid_columns(x, w, detail_ratios)
    detail_heights = []
    for row in detail_rows[:3]:
        vals = [row.get("kpi", ""), row.get("definition", ""), row.get("formula", ""), row.get("evidence", "")]
        max_lines = max(
            _estimate_block_lines(val or " ", width - (12 if idx == 0 else 8), 10 if idx else 9)
            for idx, (val, width) in enumerate(zip(vals, detail_ws))
        )
        detail_heights.append(max(32, 8 + max_lines * 8))
    detail_tbl = f"{sid}_kpi_detail_tbl"
    detail_h = 20 + sum(detail_heights)
    reqs.append(table(detail_tbl, sid, 4, 4, x, detail_y, w, detail_h))
    for ci, width in enumerate(detail_ws):
        reqs.append(table_col_width(detail_tbl, ci, width))
    reqs.append(table_row_height(detail_tbl, 0, 20))
    for ri, height in enumerate(detail_heights, start=1):
        reqs.append(table_row_height(detail_tbl, ri, height))
    for ci in range(4):
        reqs.append(table_cell_fill(detail_tbl, 0, ci, 1, 1, table_head_fill))
    for ri in range(1, 4):
        for ci in range(4):
            reqs.append(table_cell_fill(detail_tbl, ri, ci, 1, 1, table_fill))
    for ci, head in enumerate(detail_headers):
        table_cell_text(reqs, detail_tbl, 0, ci, head, TEXT, 7, True, "Noto Sans", center=True)
    detail_keys = ["kpi", "definition", "formula", "evidence"]
    for ri, row in enumerate(detail_rows[:3], start=1):
        for ci, key in enumerate(detail_keys):
            table_cell_text(
                reqs, detail_tbl, ri, ci, row.get(key, ""),
                TEXT, 7 if ci else 7.5, ci == 0, "Noto Sans", center=(ci == 0)
            )
    return

    # Section 1
    top_y = y
    if summary_title:
        _text(reqs, sid, f"{sid}_sec1", x, y, w, 12,
              summary_title,
              TEXT, 8, True, "Noto Sans")
        top_y += 18

    group_h = 20
    head_h = 20
    col_ratios = [0.18, 0.165, 0.055, 0.20, 0.055, 0.06, 0.20, 0.055, 0.06]
    xs, ws = _grid_columns(x, w, col_ratios)

    row_heights = []
    for row in summary_rows[:3]:
        cell_values = [
            row.get("kpi", ""),
            row.get("weight", ""),
            row.get("half_target", ""),
            row.get("half_actual", ""),
            row.get("half_rate", ""),
            row.get("year_target", ""),
            row.get("year_actual", ""),
            row.get("year_rate", ""),
        ]
        cell_widths = [ws[1], ws[2], ws[3], ws[4], ws[5], ws[6], ws[7], ws[8]]
        max_lines = max(
            _estimate_block_lines(val or " ", width - 8, 10)
            for val, width in zip(cell_values, cell_widths)
        )
        row_heights.append(max(28, 8 + max_lines * 8))

    for idx, row in enumerate(summary_rows[:3]):
        span = int(row.get("goal_span", 1))
        goal = row.get("goal", "")
        if goal and span > 1:
            needed = max(36, 8 + _estimate_block_lines(goal, ws[0] - 12, 10) * 8)
            current = sum(row_heights[idx:idx + span])
            if needed > current:
                extra = needed - current
                for off in range(span):
                    row_heights[idx + off] += extra / span

    table1_h = group_h + head_h + sum(row_heights)
    _rect(reqs, sid, f"{sid}_t1_outer", x, top_y, w, table1_h, table_fill, table_border, 0.5)

    for i, (label, start, span) in enumerate(summary_groups):
        gx = xs[start]
        gw = sum(ws[start:start + span])
        _rect(reqs, sid, f"{sid}_t1_group{i}", gx, top_y, gw, group_h, table_head_fill, table_border, 0.5)
        _text(reqs, sid, f"{sid}_t1_group_txt{i}", gx + 6, top_y + 4, gw - 12, 12,
              label, TEXT, 7, True, "Noto Sans", center=True, valign=True)

    head_y = top_y + group_h
    for i, head in enumerate(summary_headers):
        _rect(reqs, sid, f"{sid}_t1_head{i}", xs[i], head_y, ws[i], head_h, table_fill, table_border, 0.4)
        _text(reqs, sid, f"{sid}_t1_head_txt{i}", xs[i] + 4, head_y + 4, ws[i] - 8, 12,
              head, TEXT, 7, True, "Noto Sans", center=True, valign=True)

    current_y = head_y + head_h
    for r, row in enumerate(summary_rows[:3]):
        body_h = row_heights[r]
        ry = current_y
        if not row.get("goal_cont"):
            span = int(row.get("goal_span", 1))
            gh = sum(row_heights[r:r + span])
            _rect(reqs, sid, f"{sid}_t1_goal_{r}", xs[0], ry, ws[0], gh, table_fill, BORDER, 0.4)
            _text(reqs, sid, f"{sid}_t1_goal_txt_{r}", xs[0] + 6, ry + 4, ws[0] - 12, gh - 8,
                  row.get("goal", ""), TEXT, 7.5, True, "Noto Sans", center=True, valign=True)
        values = [
            row.get("kpi", ""),
            row.get("weight", ""),
            row.get("half_target", ""),
            row.get("half_actual", ""),
            row.get("half_rate", ""),
            row.get("year_target", ""),
            row.get("year_actual", ""),
            row.get("year_rate", ""),
        ]
        for offset, val in enumerate(values, start=1):
            _rect(reqs, sid, f"{sid}_t1_cell_{r}_{offset}", xs[offset], ry, ws[offset], body_h, table_fill, BORDER, 0.4)
            size = 7.5 if offset == 1 else 7
            _text(reqs, sid, f"{sid}_t1_txt_{r}_{offset}", xs[offset] + 4, ry + 4, ws[offset] - 8, body_h - 8,
                  val or " ", TEXT, size, offset == 1, "Noto Sans", center=True, valign=True)
        current_y += body_h

    # Section 2
    sec2_y = top_y + table1_h + 14
    _text(reqs, sid, f"{sid}_sec2", x, sec2_y, w, 12, detail_title, TEXT, 8, True, "Noto Sans")

    table2_y = sec2_y + 14
    col2 = [0.19, 0.32, 0.30, 0.19]
    xs2, ws2 = _grid_columns(x, w, col2)
    for i, head in enumerate(detail_headers):
        _rect(reqs, sid, f"{sid}_t2_head{i}", xs2[i], table2_y, ws2[i], 20, table_head_fill, table_border, 0.5)
        _text(reqs, sid, f"{sid}_t2_head_txt{i}", xs2[i] + 4, table2_y + 4, ws2[i] - 8, 12,
              head, TEXT, 7, True, "Noto Sans", center=True, valign=True)

    detail_heights = []
    for row in detail_rows[:3]:
        values = [
            row.get("kpi", ""),
            row.get("definition", ""),
            row.get("formula", ""),
            row.get("evidence", ""),
        ]
        widths = [ws2[0], ws2[1], ws2[2], ws2[3]]
        max_lines = max(
            _estimate_block_lines(val or " ", width - (12 if idx == 0 else 8), 10 if idx else 9)
            for idx, (val, width) in enumerate(zip(values, widths))
        )
        detail_heights.append(max(32, 8 + max_lines * 8))

    table2_h = 20 + sum(detail_heights)
    _rect(reqs, sid, f"{sid}_t2_outer", x, table2_y, w, table2_h, table_fill, table_border, 0.5)

    current_y = table2_y + 20
    for r, row in enumerate(detail_rows[:3]):
        row2_h = detail_heights[r]
        ry = current_y
        values = [
            row.get("kpi", ""),
            row.get("definition", ""),
            row.get("formula", ""),
            row.get("evidence", ""),
        ]
        for c, val in enumerate(values):
            _rect(reqs, sid, f"{sid}_t2_cell_{r}_{c}", xs2[c], ry, ws2[c], row2_h, table_fill, BORDER, 0.4)
            align_center = c == 0
            size = 7 if c else 7.5
            _text(reqs, sid, f"{sid}_t2_txt_{r}_{c}", xs2[c] + (4 if not align_center else 6), ry + 4,
                  ws2[c] - (8 if not align_center else 12), row2_h - 8, val or " ",
                  TEXT, size, c == 0, "Noto Sans", center=align_center, valign=True)
        current_y += row2_h


def mk_kpi_key_task_table(sid, reqs, eyebrow="APPENDIX", title="KPI 핵심 과제",
                          x=54, y=96, w=612, headers=None, rows=None):
    """
    Editable native-table layout for KPI key-task pages.

    columns:
      KPI 항목 / 달성률(%) / 세부 내용 / 하반기·내년 계획
    """
    _header(sid, reqs, eyebrow=eyebrow, title=title)

    headers = headers or [
        "KPI 항목",
        "달성률\n(%)",
        "핵심과제를 바탕으로 세부 내용 기입\n(달성: 주요 성과 / 미달성: 미달성 원인)",
        "(6월 PT) 하반기 계획\n(12월 PT) 내년 계획",
    ]
    rows = rows or [
        {
            "kpi": "협업 업무만족도",
            "kpi_span": 1,
            "col1": "100%",
            "col2": "주요 성과\n- 패키지 리뉴얼 체계 정리\n- 협업 프로세스 개선",
            "col3": "하반기\n- 운영 범위 확대",
        },
        {
            "kpi": "오류 및 신규 패키지 이슈 미발생",
            "kpi_span": 1,
            "col1": "120%",
            "col2": "주요 성과\n- 오류 이력 추적 체계 운영\n- 유관부서 확인 프로세스 정착\n- 신규 패키지 검수 기준 명확화",
            "col3": "하반기\n- 이슈 로그 표준화\n내년\n- 사전 경보 체계 도입",
        },
    ]

    table_fill = SURFACE if CURRENT_THEME == "dark" else WHITE
    table_head_fill = SURFACE_HI if CURRENT_THEME == "dark" else WHITE
    col_ratios = [0.16, 0.09, 0.42, 0.33]
    _, col_ws = _grid_columns(x, w, col_ratios)

    # Keep source data intact. The table must adapt to the content,
    # not the other way around.
    fitted_rows = [dict(row) for row in rows]

    def _task_row_needed_height(row):
        values = [
            row.get("col1", row.get("rate", "")),
            row.get("col2", row.get("detail", "")),
            row.get("col3", row.get("plan", "")),
        ]
        line_counts = [
            _estimate_block_lines(val or " ", width - 12, 8)
            for val, width in zip(values, col_ws[1:4])
        ]
        max_lines = max(line_counts or [1])
        return max(44, 14 + max_lines * 8.5)

    desired_row_heights = [_task_row_needed_height(row) for row in fitted_rows]
    row_weights = []
    for row in fitted_rows:
        values = [
            row.get("col1", row.get("rate", "")),
            row.get("col2", row.get("detail", "")),
            row.get("col3", row.get("plan", "")),
        ]
        row_weights.append(max(
            _estimate_block_lines(val or " ", width - 12, 8)
            for val, width in zip(values, col_ws[1:4])
        ))

    # Merged KPI label cells also need enough total span height.
    for idx, row in enumerate(fitted_rows):
        span = int(row.get("kpi_span", 1))
        label = row.get("kpi", "")
        if label and span > 1:
            needed = max(44, 14 + _estimate_block_lines(label, col_ws[0] - 12, 8) * 8.5)
            current = sum(desired_row_heights[idx:idx + span])
            if needed > current:
                extra = needed - current
                for off in range(span):
                    desired_row_heights[idx + off] += extra / span

    header_h = 26
    available_h = max(120, CONTENT_BOTTOM - y)
    available_rows_h = max(80, available_h - header_h)
    desired_total = sum(desired_row_heights)

    # Do not force the table to fill the whole page.
    # Keep a report-style natural density, then add only a modest amount of
    # breathing space if there is room.
    target_rows_h = min(available_rows_h, desired_total * 1.04 + 6)

    if desired_total > target_rows_h and desired_total > 0:
        scale = target_rows_h / desired_total
        row_heights = [h * scale for h in desired_row_heights]
    else:
        row_heights = list(desired_row_heights)
        extra = max(0, target_rows_h - sum(row_heights))
        weight_total = sum(row_weights) or len(row_weights) or 1
        row_heights = [
            h + extra * ((wgt or 1) / weight_total)
            for h, wgt in zip(row_heights, row_weights)
        ]

    min_row_h = 38
    row_heights = [max(min_row_h, round(h, 1)) for h in row_heights]

    table_id = f"{sid}_kpi_task_tbl"
    total_h = header_h + sum(row_heights)
    reqs.append(table(table_id, sid, 1 + len(fitted_rows), 4, x, y, w, total_h))
    for ci, width in enumerate(col_ws):
        reqs.append(table_col_width(table_id, ci, width))
    reqs.append(table_row_height(table_id, 0, header_h))
    for ri, height in enumerate(row_heights, start=1):
        reqs.append(table_row_height(table_id, ri, height))

    for ci in range(4):
        reqs.append(table_cell_fill(table_id, 0, ci, 1, 1, table_head_fill))
        reqs.append(table_cell_valign(table_id, 0, ci, 1, 1, "MIDDLE"))
        table_cell_text(reqs, table_id, 0, ci, headers[ci], TEXT, 7, True, "Noto Sans", center=True)

    for ri, row in enumerate(fitted_rows, start=1):
        span = int(row.get("kpi_span", 1))
        if not row.get("kpi_cont"):
            if span > 1:
                reqs.append(merge_cells(table_id, ri, 0, span, 1))
                reqs.append(table_cell_valign(table_id, ri, 0, span, 1, "MIDDLE"))
            else:
                reqs.append(table_cell_valign(table_id, ri, 0, 1, 1, "MIDDLE"))
            table_cell_text(reqs, table_id, ri, 0, row.get("kpi", ""), TEXT, 7.5, True, "Noto Sans", center=True)

    for ri, row in enumerate(fitted_rows, start=1):
        for ci in range(4):
            reqs.append(table_cell_fill(table_id, ri, ci, 1, 1, table_fill))
        values = [
            row.get("col1", row.get("rate", "")),
            row.get("col2", row.get("detail", "")),
            row.get("col3", row.get("plan", "")),
        ]
        for ci, val in enumerate(values, start=1):
            reqs.append(table_cell_valign(table_id, ri, ci, 1, 1, "MIDDLE" if ci == 1 else "TOP"))
            table_cell_text(
                reqs,
                table_id,
                ri,
                ci,
                val,
                TEXT,
                7.5 if ci == 1 else 7,
                ci == 1,
                "Noto Sans",
                center=(ci == 1),
            )


def mk_callout_message(sid, message, reqs, sub="", x=84, y=148, w=552, h=126):
    """Large emphasized message block for conclusion / executive summary."""
    _rect(reqs, sid, f"{sid}_callout_bg", x, y, w, h, ORANGE_DIM, ORANGE, 0.6)
    bar_y = y + min(28, max(10, h * 0.22))
    bar_h = max(2, h - (bar_y - y) * 2)
    reqs += [shape(f"{sid}_callout_bar", sid, "RECTANGLE", x + 28, bar_y, 3, bar_h),
             fill(f"{sid}_callout_bar", ORANGE, ORANGE, 0)]
    has_sub = bool(sub)
    msg_y = y + min(30, max(10, h * 0.24))
    if has_sub:
        msg_h = 50 if h >= 88 else max(18, h * 0.45)
        msg_size = 20 if h >= 88 else (12 if h >= 60 else 9.5)
    else:
        msg_h = max(22, h - (msg_y - y) - 10)
        msg_size = 20 if h >= 110 else (15 if h >= 70 else 12)
    _text(reqs, sid, f"{sid}_callout_msg", x + 48, msg_y, w - 80, msg_h,
          message, TEXT, msg_size, True, "Noto Sans")
    if has_sub:
        sub_y = y + h - 28 if h >= 70 else y + h - 18
        sub_size = 8 if h >= 70 else 6
        _text(reqs, sid, f"{sid}_callout_sub", x + 48, sub_y, w - 80, 20,
              sub, TEXT_DIM, sub_size, False, "Noto Sans")


def mk_conclusion_detail(sid, conclusion, details, reqs, eyebrow="SUMMARY", title="요약",
                         accent_line=True):
    """
    Closing summary layout:
        left  = one large conclusion
        right = small supporting details

    Use when the final slide should read as "결론 → 세부 근거".
    100% orange card is intentionally not used here; orange is limited to
    keywords, small numbers, and a short accent line.
    """
    if eyebrow:
        _text(reqs, sid, f"{sid}_summary_eyebrow", M, 28, 120, 10,
              eyebrow.upper(), ORANGE, 7, True, "Proxima Nova")
    _text(reqs, sid, f"{sid}_summary_title", M, 50, 180, 28,
          title, TEXT, 22, True, "Noto Sans")
    if accent_line:
        reqs += [shape(f"{sid}_summary_line", sid, "RECTANGLE", M, 95, 22, 1.2),
                 fill(f"{sid}_summary_line", ORANGE, ORANGE, 0.1)]

    # Left conclusion block.
    lines = conclusion if isinstance(conclusion, (list, tuple)) else [conclusion]
    base_y = 130
    for i, line in enumerate(lines[:3]):
        color = ORANGE if i == len(lines[:3]) - 1 else TEXT
        _text(reqs, sid, f"{sid}_summary_conclusion_{i}", M, base_y + i * 28, 280, 28,
              line, color, 18, True, "Noto Sans")

    # Right supporting details.
    box_x, box_y, box_w, box_h, gap = 390, 128, 276, 46, 10
    max_detail_h = _fit_height_to_content(box_y, 3 * box_h + 2 * gap, min_h=70)
    detail_count = min(3, len(details))
    if detail_count:
        box_h = max(34, (max_detail_h - gap * (detail_count - 1)) / detail_count)
    for i, detail in enumerate(details[:3]):
        y = box_y + i * (box_h + gap)
        if isinstance(detail, dict):
            label = detail.get("label", f"{i+1:02d}")
            text = detail.get("text", detail.get("title", ""))
        else:
            label = f"{i+1:02d}"
            text = str(detail)
        _rect(reqs, sid, f"{sid}_summary_detail_bg{i}", box_x, y, box_w, box_h,
              SURFACE, BORDER, 0.4)
        _text(reqs, sid, f"{sid}_summary_detail_no{i}", box_x + 16, y + max(10, (box_h - 11) / 2), 24, 11,
              label, ORANGE, 7, True, "Proxima Nova")
        _text(reqs, sid, f"{sid}_summary_detail_text{i}", box_x + 50, y + max(8, (box_h - 20) / 2), box_w - 68, 20,
              text, TEXT, 9, True, "Noto Sans")


def mk_metric_bar_summary(sid, metric, bars, reqs,
                          x=54, y=130, w=612, h=140,
                          metric_w=210, gap=24):
    """
    One-row performance expression:
        left  = large metric card
        right = monthly bar chart

    metric = {
        "label": "6-MONTH AVG",
        "value": "72.7%",
        "caption": "지난 6개월 평균"
    }
    bars = [
        {"label": "1월", "value": 45},
        {"label": "6월", "value": 95, "accent": True},
    ]
    """
    chart_x = x + metric_w + gap
    chart_w = w - metric_w - gap

    # Left metric card
    _rect(reqs, sid, f"{sid}_metric_bg", x, y, metric_w, h, SURFACE, BORDER, 0.5)
    _text(reqs, sid, f"{sid}_metric_label", x + 18, y + 24, metric_w - 36, 12,
          metric.get("label", "").upper(), TEXT_FAINT, 7, True, "Proxima Nova", valign=True)
    _text(reqs, sid, f"{sid}_metric_value", x + 18, y + 50, metric_w - 36, 48,
          metric.get("value", ""), ORANGE, 30, True, "Proxima Nova", valign=True)
    if metric.get("caption"):
        _text(reqs, sid, f"{sid}_metric_caption", x + 18, y + 106, metric_w - 36, 14,
              metric.get("caption", ""), TEXT_DIM, 7, False, "Noto Sans", valign=True)

    # Right chart panel
    _rect(reqs, sid, f"{sid}_chart_bg", chart_x, y, chart_w, h, SURFACE, BORDER, 0.5)
    if not bars:
        return

    max_v = max(float(b.get("value", 0)) for b in bars) or 1
    inner_x = chart_x + 18
    inner_y = y + 26
    inner_w = chart_w - 36
    bar_area_h = h - 70
    bar_gap = 8
    bar_w = (inner_w - bar_gap * (len(bars) - 1)) / len(bars)

    for i, b in enumerate(bars):
        val = float(b.get("value", 0))
        bh = max(4, bar_area_h * val / max_v)
        bx = inner_x + i * (bar_w + bar_gap)
        by = inner_y + bar_area_h - bh
        hot = b.get("accent", i == len(bars) - 1)
        bar_color = ORANGE if hot else c255(53, 31, 23)
        border_color = ORANGE if hot else c255(86, 50, 36)
        _rect(reqs, sid, f"{sid}_metric_bar{i}", bx, by, bar_w, bh,
              bar_color, border_color, 0.4)
        _text(reqs, sid, f"{sid}_metric_bar_val{i}", bx - 4, by - 15, bar_w + 8, 10,
              f"{int(val) if val.is_integer() else val:g}",
              TEXT if not hot else WHITE, 7, True, "Proxima Nova", center=True, valign=True)
        _text(reqs, sid, f"{sid}_metric_bar_lab{i}", bx - 4, y + h - 24, bar_w + 8, 10,
              b.get("label", ""), TEXT_FAINT, 7, False, "Noto Sans", center=True, valign=True)


def mk_arch_layers(sid, layers, reqs, x=54, y=148, w=612, spine_w=72, gap=20,
                   eyebrow="", title=""):
    """
    Layered architecture diagram.

    layers = [
        {"label": "입력", "title": "CSV / 제품번호 / 사용자 입력"},
        {"label": "선택", "title": "monday_resolver.py + monday_config.json", "accent": True, "desc": "..."},
        {"label": "렌더링", "title": "engine.jsx + project.json + {ID}_BSspec.json"},
        {"label": "출력", "title": "PDF 생성 / 파일명 규칙 / 저장"},
    ]
    """
    if eyebrow or title:
        _header(sid, reqs, eyebrow=eyebrow, title=title)
    visible = layers[:4]
    if not visible:
        return
    has_desc = any((row.get("desc", "") if isinstance(row, dict) else "") for row in visible)
    total_h = _fit_height_to_content(y, 230 if has_desc else 200, min_h=120)
    row_gap = 10
    row_h = (total_h - row_gap * (len(visible) - 1)) / len(visible)
    box_x = x + spine_w + gap
    box_w = w - spine_w - gap
    _rect(reqs, sid, f"{sid}_layers_spine", x, y, spine_w, total_h, SURFACE_HI, BORDER, 0.4)
    primary = _primary_index(
        visible,
        lambda row: isinstance(row, dict) and (
            row.get("role") in ("conclusion", "summary")
            or row.get("style") in ("primary", "conclusion", "summary")
        ),
    )
    for i, row in enumerate(visible):
        yy = y + i * (row_h + row_gap)
        label = row.get("label", f"{i+1:02d}")
        title_text = row.get("title", row.get("name", ""))
        desc = row.get("desc", "")
        marked = row.get("primary") or row.get("accent") or row.get("hot")
        hot = i == primary
        dim_hot = marked and not hot
        _text(reqs, sid, f"{sid}_layers_label{i}", x + 8, yy + row_h / 2 - 5, spine_w - 16, 10,
              label, ORANGE if (hot or dim_hot) else TEXT_FAINT, 7, True, "Proxima Nova", center=True)
        _rect(reqs, sid, f"{sid}_layers_box{i}", box_x, yy, box_w, row_h,
              ORANGE if hot else (ORANGE_DIM if dim_hot else SURFACE),
              ORANGE if marked else BORDER, 0.4)
        group_h = _stack_group_height([16] + ([12] if desc else []), gap=2)
        title_y = _center_group_start(yy, row_h, group_h, min_pad=10)
        _text(reqs, sid, f"{sid}_layers_title{i}", box_x + 18, title_y, box_w - 36, 16,
              title_text, BLACK if hot else TEXT, 10, True, "Noto Sans")
        if desc:
            desc_y = title_y + 18
            _text(reqs, sid, f"{sid}_layers_desc{i}", box_x + 18, desc_y, box_w - 36, 12,
                  desc, BLACK if hot else TEXT_DIM, 7, False, "Noto Sans")


def mk_arch_orchestrator(sid, nodes, reqs, eyebrow="", title="", x=54, y=146):
    """
    Structure diagram for module relationships.

    Preferred over card stacks when the page explains ownership / calling
    relationships between modules.
    """
    if eyebrow or title:
        _header(sid, reqs, eyebrow=eyebrow, title=title)

    input_text = nodes.get("input", "입력")
    main_text = nodes.get("main", "run.jsx")
    engine_text = nodes.get("engine", "engine.jsx")
    output_text = nodes.get("output", "출력")
    right_nodes = nodes.get("right_nodes", [])

    total_h = _fit_height_to_content(y, 208, min_h=160)
    main_y = y + 30
    input_y = y + 40
    right0_y = y
    engine_y = y + 128
    output_y = y + 172
    if y + 208 > CONTENT_BOTTOM:
        delta = y + 208 - CONTENT_BOTTOM
        main_y -= delta
        input_y -= delta
        right0_y -= delta
        engine_y -= delta
        output_y -= delta

    _rect(reqs, sid, f"{sid}_orc_in", x, input_y, 120, 44, SURFACE, BORDER, 0.4)
    in_group_h = 10 + 2 + 12
    in_top = _center_group_start(input_y, 44, in_group_h, min_pad=8) - input_y
    _text(reqs, sid, f"{sid}_orc_in_cap", x, input_y + in_top, 120, 10, "입력",
          TEXT_FAINT, 7, True, "Proxima Nova", center=True, valign=True)
    _text(reqs, sid, f"{sid}_orc_in_txt", x, input_y + in_top + 12, 120, 12, input_text,
          TEXT, 8, True, "Noto Sans", center=True, valign=True)

    _rect(reqs, sid, f"{sid}_orc_main", x + 200, main_y, 160, 64, ORANGE_DIM, ORANGE, 0.5)
    _text(reqs, sid, f"{sid}_orc_main_cap", x + 200, main_y + 15, 160, 10, "ORCHESTRATOR",
          ORANGE, 7, True, "Proxima Nova", center=True, valign=True)
    _text(reqs, sid, f"{sid}_orc_main_txt", x + 200, main_y + 31, 160, 16, main_text,
          TEXT, 13, True, "Noto Sans", center=True, valign=True)

    for i, item in enumerate(right_nodes[:3]):
        yy = right0_y + i * 54
        accent = item.get("accent") or item.get("primary")
        _rect(reqs, sid, f"{sid}_orc_rbox{i}", x + 428, yy, 184, 36,
              SURFACE, ORANGE if accent else BORDER, 0.4)
        _text(reqs, sid, f"{sid}_orc_rtxt{i}", x + 444, yy + 12, 152, 12,
              item.get("label", ""), TEXT, 7.5, True, "Noto Sans", valign=True)

    _rect(reqs, sid, f"{sid}_orc_engine", x + 200, engine_y, 160, 40, SURFACE, BORDER, 0.4)
    _text(reqs, sid, f"{sid}_orc_engine_txt", x + 200, engine_y + 14, 160, 12, engine_text,
          TEXT, 9, True, "Noto Sans", center=True, valign=True)

    _rect(reqs, sid, f"{sid}_orc_out", x + 428, output_y, 184, 36, SURFACE, BORDER, 0.4)
    _text(reqs, sid, f"{sid}_orc_out_txt", x + 444, output_y + 12, 152, 12, output_text,
          TEXT, 7.5, True, "Noto Sans", valign=True)

    in_rect = (x, input_y, 120, 44)
    main_rect = (x + 200, main_y, 160, 64)
    r0_rect = (x + 428, right0_y, 184, 36)
    r1_rect = (x + 428, right0_y + 54, 184, 36)
    r2_rect = (x + 428, right0_y + 108, 184, 36)
    eng_rect = (x + 200, engine_y, 160, 40)
    out_rect = (x + 428, output_y, 184, 36)

    main_rx, main_ry = _face_center(*main_rect, "right")
    r0_lx, r0_ly = _face_center(*r0_rect, "left")
    r1_lx, r1_ly = _face_center(*r1_rect, "left")
    r2_lx, r2_ly = _face_center(*r2_rect, "left")
    eng_rx, eng_ry = _face_center(*eng_rect, "right")
    out_lx, out_ly = _face_center(*out_rect, "left")

    connect_boxes(reqs, sid, f"{sid}_orc_c0", in_rect, main_rect, color=BORDER_HI, weight=1.0)
    orth_connector(reqs, sid, f"{sid}_orc_c1", main_rx, main_ry, r0_lx, r0_ly, color=BORDER_HI, weight=1.0)
    orth_connector(reqs, sid, f"{sid}_orc_c2", main_rx, main_ry, r1_lx, r1_ly, color=ORANGE, weight=1.0)
    orth_connector(reqs, sid, f"{sid}_orc_c3", main_rx, main_ry, r2_lx, r2_ly, color=BORDER_HI, weight=1.0)
    connect_boxes(reqs, sid, f"{sid}_orc_c4", main_rect, eng_rect, color=BORDER_HI, weight=1.0)
    orth_connector(reqs, sid, f"{sid}_orc_c5", eng_rx, eng_ry, out_lx, out_ly, color=ORANGE, weight=1.0)


def mk_decision_tree(sid, nodes, reqs, eyebrow="", title="", x=54, y=170):
    """
    Decision tree with a checkpoint and two branches.

    nodes = {
        "input": "CSV 입력",
        "decision": "자동 선택 가능?",
        "yes": "project.json 자동 선택",
        "no": "리스트박스 수동 폴백",
        "output": "PDF 출력",
        "yes_label": "자동",
        "no_label": "수동",
    }
    """
    if eyebrow or title:
        _header(sid, reqs, eyebrow=eyebrow, title=title)
    input_text = nodes.get("input", "")
    decision_text = nodes.get("decision", "")
    yes_text = nodes.get("yes", "")
    no_text = nodes.get("no", "")
    output_text = nodes.get("output", "")
    yes_label = nodes.get("yes_label", "YES")
    no_label = nodes.get("no_label", "NO")

    total_h = _fit_height_to_content(y, 140, min_h=110)
    base_y = min(y, CONTENT_BOTTOM - total_h)

    _rect(reqs, sid, f"{sid}_tree_input", x, base_y + 38, 110, 44, SURFACE, BORDER, 0.4)
    _text(reqs, sid, f"{sid}_tree_input_t", x, base_y + 51, 110, 14, input_text,
          TEXT, 8, True, "Noto Sans", center=True)

    _rect(reqs, sid, f"{sid}_tree_decision", x + 188, base_y + 22, 126, 76, SURFACE_HI, ORANGE, 0.5)
    _text(reqs, sid, f"{sid}_tree_decision_cap", x + 188, base_y + 36, 126, 10, "판단",
          TEXT_FAINT, 7, True, "Proxima Nova", center=True)
    _text(reqs, sid, f"{sid}_tree_decision_t", x + 202, base_y + 56, 98, 14, decision_text,
          TEXT, 8, True, "Noto Sans", center=True)

    _rect(reqs, sid, f"{sid}_tree_yes", x + 396, base_y, 150, 44, ORANGE_DIM, ORANGE, 0.5)
    _text(reqs, sid, f"{sid}_tree_yes_t", x + 396, base_y + 13, 150, 14, yes_text,
          TEXT, 8, True, "Noto Sans", center=True)

    _rect(reqs, sid, f"{sid}_tree_no", x + 396, base_y + 96, 150, 44, SURFACE, BORDER, 0.4)
    _text(reqs, sid, f"{sid}_tree_no_t", x + 396, base_y + 109, 150, 14, no_text,
          TEXT, 8, True, "Noto Sans", center=True)

    _rect(reqs, sid, f"{sid}_tree_output", x + 574, base_y + 38, 74, 44, SURFACE_HI, BORDER, 0.4)
    _text(reqs, sid, f"{sid}_tree_output_t", x + 574, base_y + 51, 74, 14, output_text,
          TEXT, 8, True, "Noto Sans", center=True)

    connector(reqs, sid, f"{sid}_tree_c0", x + 110, base_y + 60, x + 188, base_y + 60, color=BORDER_HI, weight=1.0)
    connector(reqs, sid, f"{sid}_tree_c1", x + 314, base_y + 40, x + 396, base_y + 22, color=ORANGE, weight=1.0)
    connector(reqs, sid, f"{sid}_tree_c2", x + 314, base_y + 80, x + 396, base_y + 118, color=BORDER_HI, weight=1.0)
    connector(reqs, sid, f"{sid}_tree_c3", x + 546, base_y + 22, x + 574, base_y + 60, color=ORANGE, weight=1.0)
    connector(reqs, sid, f"{sid}_tree_c4", x + 546, base_y + 118, x + 574, base_y + 60, color=BORDER_HI, weight=1.0)

    _text(reqs, sid, f"{sid}_tree_yes_lab", x + 336, base_y + 20, 34, 10, yes_label,
          ORANGE, 5, False, "Proxima Nova", center=True)
    _text(reqs, sid, f"{sid}_tree_no_lab", x + 336, base_y + 106, 34, 10, no_label,
          TEXT_FAINT, 5, False, "Proxima Nova", center=True)


def mk_swimlane_mapping(sid, rows, reqs, eyebrow="", title="", x=54, y=148):
    """
    Swimlane mapping for module ↔ data / config relationships.

    rows = [
        {"left": "run.jsx", "middle": "입력", "right": "CSV"},
        {"left": "monday_resolver.py", "middle": "선택 기준", "right": "monday_config.json"},
        {"left": "engine.jsx", "middle": "템플릿 차이", "right": "{ID}_BSspec.json", "accent": True},
    ]
    """
    if eyebrow or title:
        _header(sid, reqs, eyebrow=eyebrow, title=title)
    visible = rows[:3]
    left_w, mid_w, right_w = 220, 120, 236
    total_h = _fit_height_to_content(y, 180, min_h=110)
    row_gap = 8
    row_h = (total_h - 28 - row_gap * (len(visible) - 1)) / len(visible)
    mid_x = x + left_w + 18
    right_x = mid_x + mid_w + 18
    _rect(reqs, sid, f"{sid}_map_left_lane", x, y, left_w, total_h, SURFACE, BORDER, 0.4)
    _rect(reqs, sid, f"{sid}_map_mid_lane", mid_x, y, mid_w, total_h, SURFACE_HI, BORDER, 0.4)
    _rect(reqs, sid, f"{sid}_map_right_lane", right_x, y, right_w, total_h, SURFACE, BORDER, 0.4)
    _text(reqs, sid, f"{sid}_map_head_left", x + 18, y + 16, 100, 10, "실행 모듈",
          ORANGE, 7, True, "Proxima Nova", valign=True)
    _text(reqs, sid, f"{sid}_map_head_mid", mid_x + 16, y + 16, mid_w - 32, 10, "관계",
          TEXT_FAINT, 7, True, "Proxima Nova", center=True, valign=True)
    _text(reqs, sid, f"{sid}_map_head_right", right_x + 18, y + 16, 100, 10, "설정 / 데이터",
          ORANGE, 7, True, "Proxima Nova", valign=True)
    base_y = y + 40
    for i, row in enumerate(visible):
        yy = base_y + i * (row_h + row_gap)
        accent = bool(row.get("primary") or row.get("accent") or row.get("hot"))
        if i < len(visible) - 1:
            _divider(reqs, sid, f"{sid}_map_sep_l{i}", x + 14, yy + row_h + 4, left_w - 28)
            _divider(reqs, sid, f"{sid}_map_sep_m{i}", mid_x + 14, yy + row_h + 4, mid_w - 28)
            _divider(reqs, sid, f"{sid}_map_sep_r{i}", right_x + 14, yy + row_h + 4, right_w - 28)
        _text(reqs, sid, f"{sid}_map_left{i}", x + 18, yy + 8, left_w - 36, 16,
              row.get("left", ""), TEXT, 13, True, "Noto Sans", valign=True)
        _text(reqs, sid, f"{sid}_map_mid{i}", mid_x + 16, yy + 10, mid_w - 32, 12,
              row.get("middle", ""), ORANGE if accent else TEXT_DIM, 7, accent, "Noto Sans", center=True, valign=True)
        _text(reqs, sid, f"{sid}_map_right{i}", right_x + 18, yy + 8, right_w - 36, 16,
              row.get("right", ""), TEXT, 13, True, "Noto Sans", valign=True)


def _dyn_row_h(cells_ws, font_size=7, pad_v=8, line_h=10, min_h=28):
    """셀 내용 기반 동적 행 높이 계산. cells_ws: [(text, col_width), ...]
    한글/CJK 글자는 ASCII 대비 약 1.5배 폭으로 계산해 실제 렌더링 높이 추정.
    """
    max_lines = 1
    char_w = max(1.0, font_size * 0.65)
    for text, col_w in cells_ws:
        if not text:
            continue
        chars_per_line = max(3, int(max(10.0, col_w - 10) / char_w))
        lines = 0
        for para in str(text).split('\n'):
            if not para.strip():
                lines += 1
                continue
            eff_len = sum(1.5 if '가' <= c <= '힣' else 1.0 for c in para)
            lines += max(1, math.ceil(eff_len / chars_per_line))
        max_lines = max(max_lines, max(1, lines))
    return max(min_h, pad_v * 2 + max_lines * line_h)


def mk_kpi_dense_table(sid, rows, reqs, y=96):
    """
    light_dense_table_01 고정 양식 — KPI 핵심과제 상세 테이블.

    light 테마 전용. slide_base() 호출 후 본문을 채운다.
    mk_kpi_status_light()과 세트로 사용한다.

    rows: [
        {
            "kpi":   "연관 KPI 항목명",
            "task":  "핵심과제 (\\n 허용)",
            "plan":  "실행 계획 (\\n 허용)",
            "role":  "나의 역할 (\\n 허용)",
        },
        ...
    ]
    """
    COL_WS  = [100.9, 183.1, 252.9, 93.2]
    TABLE_X = 36.0
    TABLE_W = sum(COL_WS)
    HEAD_H  = 26
    KEYS    = ["kpi", "task", "plan", "role"]
    HEADERS = ["연관 KPI", "핵심과제", "실행 계획", "나의 역할"]
    n       = len(rows)
    tbl_id  = f"{sid}_kdt"

    row_hs = []
    for row in rows:
        cells_ws = [(row.get(k, ""), COL_WS[j]) for j, k in enumerate(KEYS)]
        row_hs.append(_dyn_row_h(cells_ws, font_size=7, pad_v=8, line_h=10, min_h=28))
    total_h = HEAD_H + sum(row_hs)

    reqs.append(table(tbl_id, sid, 1 + n, 4, TABLE_X, y, TABLE_W, total_h))
    reqs.append(table_border(tbl_id, 1 + n, 4, BORDER))

    for j, cw in enumerate(COL_WS):
        reqs.append(table_col_width(tbl_id, j, cw))

    reqs.append(table_row_height(tbl_id, 0, HEAD_H))
    for i, rh in enumerate(row_hs):
        reqs.append(table_row_height(tbl_id, 1 + i, rh))

    reqs.append(table_cell_fill(tbl_id, 0, 0, 1, 4, SURFACE_HI))
    reqs.append(table_cell_valign(tbl_id, 0, 0, 1, 4, "MIDDLE"))

    for i in range(n):
        bg = SURFACE if i % 2 == 0 else SURFACE_HI
        reqs.append(table_cell_fill(tbl_id, 1 + i, 0, 1, 4, bg))
        reqs.append(table_cell_valign(tbl_id, 1 + i, 0, 1, 4, "TOP"))

    for j, htxt in enumerate(HEADERS):
        table_cell_text(reqs, tbl_id, 0, j, htxt, TEXT_FAINT, 7, False, "Noto Sans")

    for i, row in enumerate(rows):
        for j, key in enumerate(KEYS):
            val = row.get(key, "")
            if val:
                table_cell_text(reqs, tbl_id, 1 + i, j, val, TEXT, 7, j == 0, "Noto Sans")


def mk_kpi_status_light(sid, reqs,
                         year="24",
                         period="상반기",
                         kpi_rows=None,
                         def_rows=None,
                         y=99):
    """
    guide_kpi_status_light 고정 양식 — KPI 진행 현황 수치 테이블.

    light 테마 전용. slide_base() 호출 후 본문을 채운다.
    mk_kpi_dense_table()과 세트로 사용한다.

    kpi_rows: [
        {
            "objective": "목표 (KPI 정보 그룹)",
            "kpi":       "KPI 항목명",
            "weight":    "가중치 (예: 20%)",
            "h_target":  "상반기 목표",
            "h_actual":  "상반기 실적",
            "h_rate":    "상반기 달성률",
            "y_target":  "연간 목표",
            "y_actual":  "연간 실적",
            "y_rate":    "연간 달성률",
            "h_done":    True,
            "y_done":    False,
        },
        ...
    ]
    def_rows: [
        {
            "kpi":        "KPI 항목명",
            "definition": "정의 및 선정배경",
            "formula":    "달성률 측정산식",
            "evidence":   "증빙",
        },
        ...
    ]
    year:   연도 표기 (기본 "24")
    period: 반기 구분 (기본 "상반기")
    """
    kpi_rows = kpi_rows or []
    def_rows = def_rows or []

    TOP_COL_WS = [108.8, 102.3, 39.3, 121.7, 39.3, 39.3, 121.7, 39.3, 47.4]
    TABLE_X    = 25.0
    TABLE_W    = sum(TOP_COL_WS)
    GRP_H      = 8
    HEAD_H     = 20
    top_id     = f"{sid}_kst"

    _KEYS_TOP = ["objective", "kpi", "weight",
                 "h_target", "h_actual", "h_rate",
                 "y_target", "y_actual", "y_rate"]
    TOP_ROW_H   = 28   # 고정 행 높이 (guide_kpi_status_light 기준)
    DEF_ROW_H   = 32   # def table 고정 행 높이

    def _row_font(cells_ws, fixed_h, base=7.0, pad_v=6, line_h=10):
        avail = max(1.0, (fixed_h - pad_v * 2) / line_h)
        max_lines = 1
        for text, col_w in cells_ws:
            if not text:
                continue
            char_w = max(1.0, base * 0.65)
            cpl = max(3, int(max(10.0, col_w - 10) / char_w))
            lines = 0
            for para in str(text).split('\n'):
                if not para.strip():
                    lines += 1
                    continue
                eff = sum(1.5 if '가' <= c <= '힣' else 1.0 for c in para)
                lines += max(1, math.ceil(eff / cpl))
            max_lines = max(max_lines, lines)
        if max_lines <= avail:
            return base
        return max(5.0, round(base * avail / max_lines, 1))

    n_top       = len(kpi_rows)
    kpi_row_hs  = [TOP_ROW_H] * n_top
    total_top_h = GRP_H + HEAD_H + sum(kpi_row_hs)

    # ── 상단 테이블 생성 ──────────────────────────────────────────────
    reqs.append(table(top_id, sid, 2 + n_top, 9, TABLE_X, y, TABLE_W, total_top_h))
    reqs.append(table_border(top_id, 2 + n_top, 9, BORDER))

    for j, cw in enumerate(TOP_COL_WS):
        reqs.append(table_col_width(top_id, j, cw))
    reqs.append(table_row_height(top_id, 0, GRP_H))
    reqs.append(table_row_height(top_id, 1, HEAD_H))
    for i, rh in enumerate(kpi_row_hs):
        reqs.append(table_row_height(top_id, 2 + i, rh))

    # ── 배경 채우기 (merge 전) ────────────────────────────────────────
    reqs.append(table_cell_fill(top_id, 0, 0, 1, 9, SURFACE_HI))
    reqs.append(table_cell_fill(top_id, 1, 0, 1, 9, SURFACE_HI))
    for i in range(n_top):
        bg = SURFACE if i % 2 == 0 else SURFACE_HI
        reqs.append(table_cell_fill(top_id, 2 + i, 0, 1, 9, bg))

    # ── valign ────────────────────────────────────────────────────────
    reqs.append(table_cell_valign(top_id, 0, 0, 1, 9, "MIDDLE"))
    reqs.append(table_cell_valign(top_id, 1, 0, 1, 9, "MIDDLE"))
    for i in range(n_top):
        reqs.append(table_cell_valign(top_id, 2 + i, 0, 1, 9, "MIDDLE"))

    # ── 셀 병합 (row 0 그룹 헤더, fill 이후) ─────────────────────────
    reqs.append(merge_cells(top_id, 0, 0, 1, 3))
    reqs.append(merge_cells(top_id, 0, 3, 1, 3))
    reqs.append(merge_cells(top_id, 0, 6, 1, 3))

    # ── 그룹 헤더 텍스트 (병합된 셀 원본 열 인덱스로 접근) ────────────
    table_cell_text(reqs, top_id, 0, 0, "KPI 정보",
                    TEXT_FAINT, 6, False, "Noto Sans", center=True)
    table_cell_text(reqs, top_id, 0, 3, f"{period} 목표/실적",
                    TEXT_FAINT, 6, False, "Noto Sans", center=True)
    table_cell_text(reqs, top_id, 0, 6, "연간 목표/실적",
                    TEXT_FAINT, 6, False, "Noto Sans", center=True)

    # ── 컬럼 헤더 텍스트 (row 1) ─────────────────────────────────────
    COL_HEADERS = ["목표", "KPI", "가중치",
                   "목표", "실적", "달성률",
                   "목표", "실적", "달성률"]
    for j, htxt in enumerate(COL_HEADERS):
        table_cell_text(reqs, top_id, 1, j, htxt,
                        TEXT_FAINT, 6, False, "Noto Sans", center=True)

    # ── 데이터 행 ─────────────────────────────────────────────────────
    KEYS     = ["objective", "kpi", "weight",
                "h_target", "h_actual", "h_rate",
                "y_target", "y_actual", "y_rate"]
    DONE_MAP = {5: "h_done", 8: "y_done"}
    for i, row in enumerate(kpi_rows):
        cells_ws = [(str(row.get(k, "") or ""), TOP_COL_WS[j])
                    for j, k in enumerate(_KEYS_TOP)]
        fs = _row_font(cells_ws, TOP_ROW_H)
        for j, key in enumerate(KEYS):
            val = str(row.get(key, "") or "")
            if not val:
                continue
            done_key = DONE_MAP.get(j)
            if done_key:
                clr  = ORANGE if row.get(done_key, False) else TEXT
                bold = bool(row.get(done_key, False))
            else:
                clr  = TEXT
                bold = (j == 1)
            table_cell_text(reqs, top_id, 2 + i, j, val,
                            clr, fs, bold, "Noto Sans", center=(j >= 2))

    # ── KPI 세부정보 레이블 ────────────────────────────────────────────
    def_label_y = y + total_top_h + 24
    _text(reqs, sid, f"{sid}_ksl_deflabel",
          TABLE_X + 6, def_label_y, 200, 12,
          "■ KPI 세부정보", TEXT_FAINT, 7, False, "Noto Sans")

    # ── 하단 KPI 세부정보 테이블 ──────────────────────────────────────
    DEF_COL_WS  = [125.4, 211.1, 197.6, 124.9]
    DEF_TABLE_X = 25.0
    DEF_TABLE_W = sum(DEF_COL_WS)
    DEF_HEAD_H  = 20
    DEF_KEYS    = ["kpi", "definition", "formula", "evidence"]
    DEF_HEADERS = ["KPI", "정의 및 선정배경", "달성률 측정산식", "증빙"]
    def_id      = f"{sid}_ksd"

    n_def       = len(def_rows)
    def_row_hs  = [DEF_ROW_H] * n_def
    total_def_h = DEF_HEAD_H + sum(def_row_hs)

    def_tbl_y = def_label_y + 24
    reqs.append(table(def_id, sid, 1 + n_def, 4, DEF_TABLE_X, def_tbl_y, DEF_TABLE_W, total_def_h))
    reqs.append(table_border(def_id, 1 + n_def, 4, BORDER))

    for j, cw in enumerate(DEF_COL_WS):
        reqs.append(table_col_width(def_id, j, cw))
    reqs.append(table_row_height(def_id, 0, DEF_HEAD_H))
    for i, rh in enumerate(def_row_hs):
        reqs.append(table_row_height(def_id, 1 + i, rh))

    reqs.append(table_cell_fill(def_id, 0, 0, 1, 4, SURFACE_HI))
    reqs.append(table_cell_valign(def_id, 0, 0, 1, 4, "MIDDLE"))
    for i in range(n_def):
        bg = SURFACE if i % 2 == 0 else SURFACE_HI
        reqs.append(table_cell_fill(def_id, 1 + i, 0, 1, 4, bg))
        reqs.append(table_cell_valign(def_id, 1 + i, 0, 1, 4, "TOP"))

    for j, htxt in enumerate(DEF_HEADERS):
        table_cell_text(reqs, def_id, 0, j, htxt, TEXT_FAINT, 7, False, "Noto Sans")

    for i, row in enumerate(def_rows):
        cells_ws = [(str(row.get(k, "") or ""), DEF_COL_WS[jj])
                    for jj, k in enumerate(DEF_KEYS)]
        fs = _row_font(cells_ws, DEF_ROW_H, base=7.0, pad_v=6, line_h=10)
        for j, key in enumerate(DEF_KEYS):
            val = row.get(key, "")
            if val:
                table_cell_text(reqs, def_id, 1 + i, j, val,
                                TEXT, fs, j == 0, "Noto Sans")

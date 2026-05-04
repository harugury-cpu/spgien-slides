#!/usr/bin/env python3
"""
spigen_verify.py — Google Slides 생성 결과를 template_spec.json 기준으로 검증.

사용법:
    python3 spigen_verify.py <PRESENTATION_ID> [slide_index]

    slide_index 생략 시 전체 슬라이드 검사.

종료 코드:
    0 = 모든 검증 통과 (완료 보고 가능)
    1 = FAIL 또는 MISS 존재 (spigen_lib.py 수정 후 재생성 필요)
"""

import json
import os
import shutil
import subprocess
import sys

GWS = shutil.which("gws") or ""
SPEC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_spec.json")
EMU = 12700


# ── 유틸 ──────────────────────────────────────────────────────────────

def emu_pt(v):
    return v / EMU


def has_korean(text):
    s = str(text or "")
    return any(
        ("\uac00" <= ch <= "\ud7a3")
        or ("\u1100" <= ch <= "\u11ff")
        or ("\u3130" <= ch <= "\u318f")
        for ch in s
    )


def load_spec():
    with open(SPEC_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_presentation(pres_id):
    if not GWS:
        raise RuntimeError("gws 바이너리를 찾을 수 없습니다. 'which gws' 또는 PATH를 확인하세요.")
    cmd = [GWS, "slides", "presentations", "get",
           "--params", json.dumps({"presentationId": pres_id})]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gws 오류:\n{r.stderr.strip()}")
    # keyring 경고 등 JSON 앞 불필요한 출력 제거
    stdout = r.stdout
    idx = stdout.find("{")
    if idx > 0:
        stdout = stdout[idx:]
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"gws 출력 파싱 실패: {e}\n출력(앞 300자): {r.stdout[:300]}")


def parse_el(el):
    """pageElement → {x, y, w, h, font_size, font_family, bold}

    Google Slides API는 크기를 size × scaleX/scaleY 로 인코딩한다.
    실제 렌더 크기 = size.width * scaleX (EMU) / 12700 (pt)

    native table의 경우 elementProperties.size는 createTable 기본값(~236pt)이며
    실제 렌더 크기는 tableRows[].rowHeight 와 tableColumns[].columnWidth 합산이다.
    """
    t = el.get("transform", {})
    sz = el.get("size", {})
    x = emu_pt(t.get("translateX", 0))
    y = emu_pt(t.get("translateY", 0))

    tbl = el.get("table", {})
    if tbl:
        # native table: 실제 크기를 row/col 합산으로 계산
        w = sum(
            emu_pt(col.get("columnWidth", {}).get("magnitude", 0))
            for col in tbl.get("tableColumns", [])
        )
        h = sum(
            emu_pt(row.get("rowHeight", {}).get("magnitude", 0))
            for row in tbl.get("tableRows", [])
        )
    else:
        w = emu_pt(sz.get("width", {}).get("magnitude", 0) * t.get("scaleX", 1.0))
        h = emu_pt(sz.get("height", {}).get("magnitude", 0) * t.get("scaleY", 1.0))

    # 빈 run / paragraphMarker 건너뛰고 실제 내용 있는 첫 textRun 사용
    style = {}
    for te in el.get("shape", {}).get("text", {}).get("textElements", []):
        run = te.get("textRun", {})
        if not run or not run.get("content", "").strip():
            continue
        s = run.get("style", {})
        fs = s.get("fontSize", {}).get("magnitude")
        ff = s.get("fontFamily")
        if fs is not None or ff:
            style = {"font_size": fs, "font_family": ff, "bold": s.get("bold")}
            break

    text_buf = ""
    for te in el.get("shape", {}).get("text", {}).get("textElements", []):
        text_buf += te.get("textRun", {}).get("content", "")

    return {
        "x": round(x, 1), "y": round(y, 1),
        "w": round(w, 1), "h": round(h, 1),
        "text": text_buf.strip(),
        **style,
    }


def build_elmap(slide):
    return {el["objectId"]: parse_el(el) for el in slide.get("pageElements", [])}


def verify_global_bounds(elmap):
    results = []
    for oid, el in elmap.items():
        x = el.get("x", 0)
        y = el.get("y", 0)
        w = el.get("w", 0)
        h = el.get("h", 0)
        if x < -0.1 or y < -0.1 or x + w > 720.1 or y + h > 405.1:
            results.append(("FAIL", f"global_bounds.{oid}: off-canvas x={x}, y={y}, w={w}, h={h}"))
    return results


def verify_cover_contract(slide, idx):
    """
    First slide must use either:
      - the template cover element IDs
      - or the standard mk_cover() element suffixes
    """
    if idx != 0:
        return []
    oids = {el["objectId"] for el in slide.get("pageElements", [])}
    template_cover_dark = {
        "g9001df85b1_0_1",
        "g9001df85b1_0_2",
        "ga85705c0f7_0_1",
    }
    template_cover_dark_v2 = {
        "g9001df85b1_0_3",
        "g3e66e3c2180_1_2",
        "g3e66e3c2180_1_3",
        "g3e66e3c2180_1_4",
    }
    template_cover_dark_v3 = {
        "g3db53c0022e_0_1",
        "g3db53c0022e_0_2",
        "g3db53c0022e_0_3",
        "g3db53c0022e_0_4",
    }
    template_cover_light = {
        "g8f47d50608_1_1",
        "g8f47d50608_1_3",
        "gb12e07a716_0_0",
    }
    helper_cover_suffixes = [
        "_cover_title",
        "_cover_team",
        "_cover_meta",
    ]
    if (
        template_cover_dark.issubset(oids)
        or template_cover_dark_v2.issubset(oids)
        or template_cover_dark_v3.issubset(oids)
        or template_cover_light.issubset(oids)
    ):
        return [("PASS", "cover_contract: template cover IDs detected")]
    if all(any(oid.endswith(sfx) for oid in oids) for sfx in helper_cover_suffixes):
        return [("PASS", "cover_contract: mk_cover helper IDs detected")]
    return [("FAIL", "cover_contract: first slide is not using template cover or mk_cover() structure")]


# ── 체크 헬퍼 ────────────────────────────────────────────────────────

def _chk(results, label, actual, expected, tol=2.5):
    if actual is None:
        results.append(("SKIP", f"{label}: 값 없음"))
        return
    diff = abs(actual - expected)
    if diff <= tol:
        results.append(("PASS", f"{label}: {actual:.1f} ≈ {expected:.1f}"))
    else:
        results.append(("FAIL",
            f"{label}: got {actual:.1f}, expected {expected:.1f}  (차이 {diff:.1f}pt)"))


def _chk_str(results, label, actual, expected):
    if actual is None:
        results.append(("SKIP", f"{label}: 값 없음"))
        return
    if actual == expected:
        results.append(("PASS", f"{label}: '{actual}'"))
    else:
        results.append(("FAIL", f"{label}: got '{actual}', expected '{expected}'"))


def _check_element(results, el, sp, prefix, tol=2.5):
    """공통: sp 딕셔너리의 x/y/w/h/font_size/font_family/bold를 el에서 검증."""
    for dim in ("x", "y", "w", "h"):
        if dim in sp:
            _chk(results, f"{prefix}.{dim}", el.get(dim), sp[dim], tol)
    if "font_size" in sp:
        _chk(results, f"{prefix}.font_size", el.get("font_size"), sp["font_size"], tol=0.6)
    if "font_family" in sp:
        expected_ff = sp["font_family"]
        if expected_ff == "AUTO":
            expected_ff = "Noto Sans" if has_korean(el.get("text", "")) else "Proxima Nova"
        _chk_str(results, f"{prefix}.font_family", el.get("font_family"), expected_ff)
    if "bold" in sp and sp["bold"] is not None:
        actual_bold = el.get("bold")
        if actual_bold is None:
            results.append(("SKIP", f"{prefix}.bold: 값 없음"))
        elif actual_bold == sp["bold"]:
            results.append(("PASS", f"{prefix}.bold: {actual_bold}"))
        else:
            results.append(("FAIL", f"{prefix}.bold: got {actual_bold}, expected {sp['bold']}"))


# ── 컴포넌트 감지 ────────────────────────────────────────────────────

_SID_ANCHOR_SUFFIXES = [
    "_focus_bg0", "_step0", "_leftbox", "_sc0", "_bodybox",
    "_col0", "_kpi_bg0", "_kst", "_kdt", "_quote_mark", "_eyebrow",
    "_cmp_left_label",
]

def _infer_sid(elmap, oid):
    """createSlide objectId(oid)와 mk_* sid가 다를 때 실제 sid를 추론한다."""
    for key in elmap:
        for suf in _SID_ANCHOR_SUFFIXES:
            if key.endswith(suf):
                candidate = key[: -len(suf)]
                if candidate:
                    return candidate
    return oid


def detect_components(elmap, oid):
    sid = _infer_sid(elmap, oid)
    comps = []
    if f"{sid}_num" in elmap and f"{sid}_label" in elmap:
        comps.append("section_divider")
    if f"{sid}_step0" in elmap:
        comps.append("flow")
    if f"{sid}_focus_bg0" in elmap:
        comps.append("flow_focus")
    if f"{sid}_col0" in elmap:
        comps.append("3col")
    if f"{sid}_kpi_bg0" in elmap:
        comps.append("kpi_dashboard")
    if f"{sid}_leftbox" in elmap and f"{sid}_rightbox" in elmap:
        comps.append("split")
    if f"{sid}_cmp_lb0" in elmap:
        comps.append("compare_rows")
    if f"{sid}_sc0" in elmap:
        comps.append("split_cards")
    if f"{sid}_bodybox" in elmap:
        comps.append("text_block")
    if f"{sid}_kst" in elmap:
        comps.append("kpi_status_light")
    if f"{sid}_kdt" in elmap:
        comps.append("kpi_dense_table")
    if f"{sid}_quote_mark" in elmap:
        comps.append("quote")
    if f"{sid}_eyebrow" in elmap:
        comps.append("slide_base")
    elif f"{sid}_title" in elmap and "section_divider" not in comps:
        comps.append("slide_base")
    return comps


# ── 컴포넌트별 검증 함수 ──────────────────────────────────────────────

def verify_slide_base(elmap, oid, spec, tol):
    results = []
    s = spec.get("slide_base", {})
    for suffix, key in [("_eyebrow", "eyebrow"), ("_title", "title")]:
        sp = s.get(key, {})
        el = elmap.get(oid + suffix)
        if el and sp:
            _check_element(results, el, sp, f"slide_base.{key}", tol)
    return results


def verify_section_divider(elmap, oid, spec, tol):
    results = []
    s = spec.get("section_divider", {})
    for suffix, key in [("_num", "num"), ("_vline", "vline"), ("_label", "label"), ("_title", "title")]:
        sp = s.get(key, {})
        el = elmap.get(oid + suffix)
        if not sp:
            continue
        if not el:
            results.append(("MISS", f"section_divider{suffix} 요소 없음"))
            continue
        _check_element(results, el, sp, f"section_divider.{key}", tol)
    return results


def verify_flow(elmap, oid, spec, tol):
    results = []
    layout = spec.get("flow", {}).get("_layout", {})
    x0 = layout.get("x0", 54)
    y0 = layout.get("y0", 132)
    total_w = layout.get("total_w", 612)
    ch = layout.get("ch", 96)

    n = sum(1 for i in range(10) if f"{oid}_step{i}" in elmap)
    if n == 0:
        return results

    gap = layout.get("gap_le4", 12) if n <= 4 else layout.get("gap_gt4", 8)
    cw = (total_w - gap * (n - 1)) / n

    s = spec.get("flow", {})

    for i in range(n):
        x = x0 + i * (cw + gap)
        pfx = f"flow.step{i}"

        # 카드 박스
        card = elmap.get(f"{oid}_step{i}")
        if card:
            _chk(results, f"{pfx}.x", card.get("x"), round(x, 1), tol)
            _chk(results, f"{pfx}.y", card.get("y"), y0, tol)
            _chk(results, f"{pfx}.w", card.get("w"), round(cw, 1), tol)
            if "ch" in layout:
                _chk(results, f"{pfx}.h", card.get("h"), ch, tol)
        else:
            results.append(("MISS", f"{pfx} 카드 요소 없음"))

        # 텍스트 서브요소
        for suffix, key in [("_sn", "sn"), ("_st", "st"), ("_sv", "sv")]:
            sp = s.get(key, {})
            el = elmap.get(f"{oid}{suffix}{i}")
            if not el or not sp:
                continue
            _chk(results, f"{pfx}{suffix}.x", el.get("x"), round(x + sp.get("rel_x", 0), 1), tol)
            if "rel_y" in sp:
                _chk(results, f"{pfx}{suffix}.y", el.get("y"), y0 + sp["rel_y"], tol)
            _chk(results, f"{pfx}{suffix}.w", el.get("w"), round(cw - sp.get("w_shrink", 0), 1), tol)
            if "font_size" in sp:
                _chk(results, f"{pfx}{suffix}.font_size", el.get("font_size"), sp["font_size"], tol=0.6)
            if "font_family" in sp:
                _chk_str(results, f"{pfx}{suffix}.font_family", el.get("font_family"), sp["font_family"])

    return results


def verify_flow_focus(elmap, oid, tol):
    results = []
    n = sum(1 for i in range(10) if f"{oid}_focus_bg{i}" in elmap)
    if n == 0:
        return results

    x0, y0, total_w = 54, 136, 612
    gap = 8
    card_w = (total_w - gap * max(0, n - 1)) / max(1, n)

    for i in range(n):
        x = x0 + i * (card_w + gap)
        card = elmap.get(f"{oid}_focus_bg{i}")
        if card:
            _chk(results, f"flow_focus.card{i}.x", card.get("x"), round(x, 1), tol)
            _chk(results, f"flow_focus.card{i}.y", card.get("y"), y0, tol)
            _chk(results, f"flow_focus.card{i}.w", card.get("w"), round(card_w, 1), tol)
        else:
            results.append(("MISS", f"flow_focus.card{i}: 카드 요소 없음"))

        num = elmap.get(f"{oid}_focus_num{i}")
        if num:
            _chk(results, f"flow_focus.num{i}.x", num.get("x"), round(x + 12, 1), tol)
            _chk(results, f"flow_focus.num{i}.w", num.get("w"), 56, tol)
            _chk(results, f"flow_focus.num{i}.font_size", num.get("font_size"), 7, tol=0.6)

        title = elmap.get(f"{oid}_focus_title{i}")
        if title:
            _chk(results, f"flow_focus.title{i}.x", title.get("x"), round(x + 12, 1), tol)
            _chk(results, f"flow_focus.title{i}.w", title.get("w"), round(card_w - 24, 1), tol)
            _chk(results, f"flow_focus.title{i}.font_size", title.get("font_size"), 12.5, tol=0.6)

        svc = elmap.get(f"{oid}_focus_svc{i}")
        if svc:
            _chk(results, f"flow_focus.svc{i}.x", svc.get("x"), round(x + 12, 1), tol)
            _chk(results, f"flow_focus.svc{i}.w", svc.get("w"), round(card_w - 24, 1), tol)
            _chk(results, f"flow_focus.svc{i}.font_size", svc.get("font_size"), 7, tol=0.6)

    return results


def verify_3col(elmap, oid, spec, tol):
    results = []
    layout = spec.get("3col", {}).get("_layout", {})
    x0 = layout.get("x0", 36)
    y0 = layout.get("y0", 128)
    cw = layout.get("card_w", 206)
    gap = layout.get("gap", 12)
    s = spec.get("3col", {})

    n = sum(1 for i in range(5) if f"{oid}_col{i}" in elmap)
    for i in range(n):
        x = x0 + i * (cw + gap)
        pfx = f"3col.col{i}"

        card = elmap.get(f"{oid}_col{i}")
        if card:
            _chk(results, f"{pfx}.x", card.get("x"), x, tol)
            _chk(results, f"{pfx}.y", card.get("y"), y0, tol)
            _chk(results, f"{pfx}.w", card.get("w"), cw, tol)

        for suffix, key in [("_cl", "cl"), ("_ct", "ct")]:
            sp = s.get(key, {})
            el = elmap.get(f"{oid}{suffix}{i}")
            if not el or not sp:
                continue
            _chk(results, f"{pfx}{suffix}.x", el.get("x"), x + sp.get("rel_x", 0), tol)
            _chk(results, f"{pfx}{suffix}.y", el.get("y"), y0 + sp.get("rel_y", 0), tol)
            if "font_size" in sp:
                _chk(results, f"{pfx}{suffix}.font_size", el.get("font_size"), sp["font_size"], tol=0.6)
            if "font_family" in sp:
                _chk_str(results, f"{pfx}{suffix}.font_family", el.get("font_family"), sp["font_family"])

    return results


def verify_split(elmap, oid, tol):
    results = []
    checks = [
        (f"{oid}_leftbox", 36, 128, 313, 220),
        (f"{oid}_rightbox", 371, 128, 313, 220),
        (f"{oid}_lt", 54, 150, 280, 24),
        (f"{oid}_lb", 54, 184, 280, 140),
        (f"{oid}_rt", 389, 150, 280, 24),
        (f"{oid}_rb", 389, 184, 280, 140),
    ]
    for key, x, y, w, h in checks:
        el = elmap.get(key)
        if not el:
            results.append(("MISS", f"split.{key}: 요소 없음"))
            continue
        label = key.replace(f"{oid}_", "")
        _chk(results, f"split.{label}.x", el.get("x"), x, tol)
        _chk(results, f"split.{label}.y", el.get("y"), y, tol)
        _chk(results, f"split.{label}.w", el.get("w"), w, tol)
        _chk(results, f"split.{label}.h", el.get("h"), h, tol)

    arrow = elmap.get(f"{oid}_arrow")
    if arrow:
        _chk(results, "split.arrow.x", arrow.get("x"), 352, tol)
        _chk(results, "split.arrow.y", arrow.get("y"), 226, tol)
        _chk(results, "split.arrow.w", arrow.get("w"), 16, tol)
        _chk(results, "split.arrow.h", arrow.get("h"), 16, tol)
    return results


def verify_compare_rows(elmap, oid, tol):
    results = []

    left = elmap.get(f"{oid}_cmp_left_label")
    right = elmap.get(f"{oid}_cmp_right_label")
    if left:
        _chk(results, "compare_rows.left_label.x", left.get("x"), 36, tol)
        _chk(results, "compare_rows.left_label.y", left.get("y"), 109, tol)
        _chk(results, "compare_rows.left_label.w", left.get("w"), 120, tol)
        _chk(results, "compare_rows.left_label.h", left.get("h"), 10, tol)
        _chk(results, "compare_rows.left_label.font_size", left.get("font_size"), 7, tol=0.6)
    else:
        results.append(("MISS", "compare_rows.left_label: 요소 없음"))

    if right:
        _chk(results, "compare_rows.right_label.x", right.get("x"), 370.5, tol)
        _chk(results, "compare_rows.right_label.y", right.get("y"), 109, tol)
        _chk(results, "compare_rows.right_label.w", right.get("w"), 120, tol)
        _chk(results, "compare_rows.right_label.h", right.get("h"), 10, tol)
        _chk(results, "compare_rows.right_label.font_size", right.get("font_size"), 7, tol=0.6)
    else:
        results.append(("MISS", "compare_rows.right_label: 요소 없음"))

    row_y0, row_h, row_gap = 125.2, 40, 5
    n = sum(1 for i in range(10) if f"{oid}_cmp_lb{i}" in elmap)
    for i in range(n):
        ry = row_y0 + i * (row_h + row_gap)

        for suffix, x, w in [
            ("_cmp_lb", 36, 313.5),
            ("_cmp_mid", 349.5, 21),
            ("_cmp_rb", 370.5, 313.5),
        ]:
            el = elmap.get(f"{oid}{suffix}{i}")
            name = suffix[1:]
            if not el:
                results.append(("MISS", f"compare_rows.{name}{i}: 요소 없음"))
                continue
            _chk(results, f"compare_rows.{name}{i}.x", el.get("x"), x, tol)
            _chk(results, f"compare_rows.{name}{i}.y", el.get("y"), ry, tol)
            _chk(results, f"compare_rows.{name}{i}.w", el.get("w"), w, tol)
            _chk(results, f"compare_rows.{name}{i}.h", el.get("h"), row_h, tol)

        ar = elmap.get(f"{oid}_cmp_ar{i}")
        if ar:
            _chk(results, f"compare_rows.arrow{i}.x", ar.get("x"), 356, tol)
            _chk(results, f"compare_rows.arrow{i}.y", ar.get("y"), ry + 17, tol)

        item = elmap.get(f"{oid}_cmp_item{i}")
        before = elmap.get(f"{oid}_cmp_before{i}")
        after_label = elmap.get(f"{oid}_cmp_after_label{i}")
        after = elmap.get(f"{oid}_cmp_after{i}")

        if item:
            _chk(results, f"compare_rows.item{i}.x", item.get("x"), 47, tol)
            _chk(results, f"compare_rows.item{i}.y", item.get("y"), ry + 8, tol)
        if before:
            _chk(results, f"compare_rows.before{i}.x", before.get("x"), 47, tol)
            _chk(results, f"compare_rows.before{i}.y", before.get("y"), ry + 18, tol)
        if after_label:
            _chk(results, f"compare_rows.after_label{i}.x", after_label.get("x"), 382, tol)
            _chk(results, f"compare_rows.after_label{i}.y", after_label.get("y"), ry + 8, tol)
        if after:
            _chk(results, f"compare_rows.after{i}.x", after.get("x"), 382, tol)
            _chk(results, f"compare_rows.after{i}.y", after.get("y"), ry + 18, tol)

    return results


def verify_split_cards(elmap, oid, tol):
    results = []
    for i in range(5):
        tl = elmap.get(f"{oid}_tl{i}")
        if not tl:
            continue
        _chk(results, f"split_cards.tl{i}.x", tl.get("x"), 36, tol)
        _chk(results, f"split_cards.tl{i}.y", tl.get("y"), 140 + i * 24, tol)
        _chk(results, f"split_cards.tl{i}.w", tl.get("w"), 260, tol)
        _chk(results, f"split_cards.tl{i}.h", tl.get("h"), 18, tol)

    for i in range(4):
        sc = elmap.get(f"{oid}_sc{i}")
        if not sc:
            continue
        y = 140 + i * (44 + 8)
        _chk(results, f"split_cards.card{i}.x", sc.get("x"), 370, tol)
        _chk(results, f"split_cards.card{i}.y", sc.get("y"), y, tol)
        _chk(results, f"split_cards.card{i}.w", sc.get("w"), 314, tol)
        _chk(results, f"split_cards.card{i}.h", sc.get("h"), 44, tol)
        sct = elmap.get(f"{oid}_sct{i}")
        if sct:
            _chk(results, f"split_cards.title{i}.x", sct.get("x"), 388, tol)
            _chk(results, f"split_cards.title{i}.y", sct.get("y"), y + 13, tol)
            _chk(results, f"split_cards.title{i}.w", sct.get("w"), 278, tol)
            _chk(results, f"split_cards.title{i}.h", sct.get("h"), 18, tol)
            _chk(results, f"split_cards.title{i}.font_size", sct.get("font_size"), 12.5, tol=0.6)

    return results


def verify_text_block(elmap, oid, tol):
    results = []
    bodybox = elmap.get(f"{oid}_bodybox")
    body = elmap.get(f"{oid}_body")
    if not bodybox:
        results.append(("MISS", "text_block.bodybox: 요소 없음"))
        return results

    _chk(results, "text_block.bodybox.x", bodybox.get("x"), 36, tol)
    _chk(results, "text_block.bodybox.y", bodybox.get("y"), 128, tol)
    _chk(results, "text_block.bodybox.w", bodybox.get("w"), 648, tol)
    if body:
        _chk(results, "text_block.body.x", body.get("x"), 56, tol)
        _chk(results, "text_block.body.y", body.get("y"), 150, tol)
        _chk(results, "text_block.body.w", body.get("w"), 608, tol)
    else:
        results.append(("MISS", "text_block.body: 요소 없음"))
    return results


def verify_kpi(elmap, oid, spec, tol):
    results = []
    layout = spec.get("kpi_dashboard", {}).get("_layout", {})
    x0 = layout.get("x0", 36)
    y0 = layout.get("y0", 128)
    gap = layout.get("gap", 12)
    card_h = layout.get("card_h", 128)
    s = spec.get("kpi_dashboard", {})

    n = sum(1 for i in range(5) if f"{oid}_kpi_bg{i}" in elmap)
    canvas_w = 720
    margin = 36
    card_w = (canvas_w - margin * 2 - gap * (n - 1)) / max(1, n)

    for i in range(n):
        x = x0 + i * (card_w + gap)
        pfx = f"kpi.{i}"
        for suffix, key in [("_kpi_label", "kpi_label"), ("_kpi_value", "kpi_value"), ("_kpi_sub", "kpi_sub")]:
            sp = s.get(key, {})
            el = elmap.get(f"{oid}{suffix}{i}")
            if not el or not sp:
                continue
            _chk(results, f"{pfx}{suffix}.x", el.get("x"), round(x + sp.get("rel_x", 0), 1), tol)
            _chk(results, f"{pfx}{suffix}.y", el.get("y"), y0 + sp.get("rel_y", 0), tol)
            if "font_size" in sp:
                _chk(results, f"{pfx}{suffix}.font_size", el.get("font_size"), sp["font_size"], tol=0.6)
            if "font_family" in sp:
                _chk_str(results, f"{pfx}{suffix}.font_family", el.get("font_family"), sp["font_family"])

    return results


def verify_quote(elmap, oid, spec, tol):
    results = []
    s = spec.get("quote", {})
    for suffix, key in [("_quote_mark", "quote_mark"), ("_quote", "quote")]:
        sp = s.get(key, {})
        el = elmap.get(oid + suffix)
        if el and sp:
            _check_element(results, el, sp, f"quote.{key}", tol)
    return results


# ── 오렌지 카운트 + 겹침 감지 ──────────────────────────────────────────

_ORG_R = (0.95, 1.01)   # #FF ≈ 1.0
_ORG_G = (0.36, 0.47)   # #6B ≈ 0.42
_ORG_B = (0.07, 0.14)   # #1A ≈ 0.10


def _is_orange(rgb):
    if not rgb:
        return False
    return (
        _ORG_R[0] <= rgb.get("red", 0) <= _ORG_R[1]
        and _ORG_G[0] <= rgb.get("green", 0) <= _ORG_G[1]
        and _ORG_B[0] <= rgb.get("blue", 0) <= _ORG_B[1]
    )


def _shape_fill_rgb(el):
    sp = el.get("shape", {}).get("shapeProperties", {})
    solid = sp.get("shapeBackgroundFill", {}).get("solidFill", {})
    return solid.get("color", {}).get("rgbColor")


def _shape_outline_rgb(el):
    sp = el.get("shape", {}).get("shapeProperties", {})
    solid = sp.get("outline", {}).get("solidFill", {})
    return solid.get("color", {}).get("rgbColor")


def verify_orange_count(slide, idx):
    """슬라이드당 오렌지(#FF6B1A) fill/outline 요소 수. 3 초과 시 FAIL. Slide 0 제외."""
    if idx == 0:
        return []
    flagged = [
        el.get("objectId", "?")
        for el in slide.get("pageElements", [])
        if _is_orange(_shape_fill_rgb(el)) or _is_orange(_shape_outline_rgb(el))
    ]
    if len(flagged) > 3:
        return [("FAIL", f"orange_overuse: {len(flagged)}개 (한도 3개) → {', '.join(flagged[:6])}")]
    if flagged:
        return [("PASS", f"orange_count: {len(flagged)}개 ≤ 3")]
    return []


def verify_element_overlap(elmap, idx):
    """슬라이드 내 요소 겹침 검사 (배경·완전포함 제외). Slide 0 제외."""
    if idx == 0:
        return []
    results = []
    # 전체화면 배경(w≥680 or h≥380) 및 면적 0 제외
    els = [
        (oid, el) for oid, el in elmap.items()
        if el.get("w", 0) < 680 and el.get("h", 0) < 380
        and el.get("w", 0) > 1 and el.get("h", 0) > 1
    ]
    for i, (oid1, el1) in enumerate(els):
        x1, y1, w1, h1 = el1["x"], el1["y"], el1["w"], el1["h"]
        for oid2, el2 in els[i + 1:]:
            x2, y2, w2, h2 = el2["x"], el2["y"], el2["w"], el2["h"]
            ox = min(x1 + w1, x2 + w2) - max(x1, x2)
            oy = min(y1 + h1, y2 + h2) - max(y1, y2)
            if ox <= 0 or oy <= 0:
                continue
            # 완전 포함(텍스트-인-카드)은 스킵
            if (
                (x1 <= x2 and y1 <= y2 and x1 + w1 >= x2 + w2 and y1 + h1 >= y2 + h2)
                or (x2 <= x1 and y2 <= y1 and x2 + w2 >= x1 + w1 and y2 + h2 >= y1 + h1)
            ):
                continue
            # 겹침 면적이 작은 요소 넓이의 8% 이상이면 FAIL
            smaller = min(w1 * h1, w2 * h2)
            if smaller > 0 and (ox * oy) / smaller >= 0.08:
                results.append(("FAIL",
                    f"overlap: {oid1}[{x1:.0f},{y1:.0f} {w1:.0f}×{h1:.0f}] ∩ "
                    f"{oid2}[{x2:.0f},{y2:.0f} {w2:.0f}×{h2:.0f}] ({ox:.0f}×{oy:.0f}pt)"))
    return results


def verify_text_contrast(slide, idx):
    """dark 배경 슬라이드에서 어두운 텍스트(밝기<0.2) 감지. Slide 0 제외."""
    if idx == 0:
        return []
    bg = slide.get("pageProperties", {}).get("pageBackgroundFill", {})
    bg_rgb = bg.get("solidFill", {}).get("color", {}).get("rgbColor")
    if not bg_rgb:
        return []
    bg_lum = (bg_rgb.get("red", 1) + bg_rgb.get("green", 1) + bg_rgb.get("blue", 1)) / 3.0
    if bg_lum >= 0.30:  # light 테마 슬라이드는 검사 안 함
        return []
    bad = []
    for el in slide.get("pageElements", []):
        for te in el.get("shape", {}).get("text", {}).get("textElements", []):
            style = te.get("textRun", {}).get("style", {})
            fc = style.get("foregroundColor", {}).get("opaqueColor", {}).get("rgbColor")
            if not fc:
                continue
            fc_lum = (fc.get("red", 0) + fc.get("green", 0) + fc.get("blue", 0)) / 3.0
            if fc_lum < 0.20:
                bad.append(el.get("objectId", "?"))
                break
    if bad:
        return [("FAIL", f"dark_text_on_dark_bg: {len(bad)}개 요소 → {', '.join(bad[:4])}")]
    return []


# ── 출력 ─────────────────────────────────────────────────────────────

ICONS = {"PASS": "✓", "FAIL": "✗", "SKIP": "·", "MISS": "?"}


def print_results(results):
    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0, "MISS": 0}
    for status, msg in results:
        counts[status] = counts.get(status, 0) + 1
        icon = ICONS.get(status, " ")
        print(f"    {icon} [{status}] {msg}")
    return counts


# ── 메인 ─────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("사용법: python3 spigen_verify.py <PRESENTATION_ID> [slide_index]")
        sys.exit(1)

    pres_id = sys.argv[1]
    target = None
    if len(sys.argv) > 2:
        try:
            target = int(sys.argv[2])
        except ValueError:
            print(f"오류: slide_index는 정수여야 합니다 (got '{sys.argv[2]}')")
            sys.exit(1)

    spec = load_spec()
    tol = spec.get("_meta", {}).get("tolerance_pt", 2.5)

    print(f"프레젠테이션 로드 중: {pres_id}")
    try:
        data = get_presentation(pres_id)
    except RuntimeError as e:
        print(f"오류: {e}")
        sys.exit(1)
    slides = data.get("slides", [])
    print(f"슬라이드 {len(slides)}장 확인\n")

    total = {"PASS": 0, "FAIL": 0, "SKIP": 0, "MISS": 0}

    for idx, slide in enumerate(slides):
        if target is not None and idx != target:
            continue

        oid = slide.get("objectId", f"slide_{idx}")
        elmap = build_elmap(slide)
        sid = _infer_sid(elmap, oid)  # mk_* 함수에 넘긴 sid — oid와 다를 수 있음
        comps = detect_components(elmap, oid)
        results = []
        results += verify_cover_contract(slide, idx)
        results += verify_global_bounds(elmap)
        results += verify_orange_count(slide, idx)
        results += verify_element_overlap(elmap, idx)
        results += verify_text_contrast(slide, idx)

        sid_note = f" sid={sid}" if sid != oid else ""
        print(f"── Slide {idx}  ({oid}{sid_note})")
        if not comps:
            if results:
                counts = print_results(results)
                print(f"    → PASS:{counts['PASS']} FAIL:{counts['FAIL']} SKIP:{counts['SKIP']} MISS:{counts['MISS']}\n")
                for k, v in counts.items():
                    total[k] = total.get(k, 0) + v
            else:
                print("    (인식된 컴포넌트 없음 — 건너뜀)\n")
            continue
        print(f"    컴포넌트: {', '.join(comps)}")

        if "slide_base" in comps and idx != 0:  # 표지(idx=0)는 template cover — 폰트 체크 제외
            results += verify_slide_base(elmap, sid, spec, tol)
        if "section_divider" in comps:
            results += verify_section_divider(elmap, sid, spec, tol)
        if "flow" in comps:
            results += verify_flow(elmap, sid, spec, tol)
        if "flow_focus" in comps:
            results += verify_flow_focus(elmap, sid, tol)
        if "3col" in comps:
            results += verify_3col(elmap, sid, spec, tol)
        if "split" in comps:
            results += verify_split(elmap, sid, tol)
        if "compare_rows" in comps:
            results += verify_compare_rows(elmap, sid, tol)
        if "split_cards" in comps:
            results += verify_split_cards(elmap, sid, tol)
        if "text_block" in comps:
            results += verify_text_block(elmap, sid, tol)
        if "kpi_dashboard" in comps:
            results += verify_kpi(elmap, sid, spec, tol)
        if "quote" in comps:
            results += verify_quote(elmap, sid, spec, tol)

        counts = print_results(results)
        print(f"    → PASS:{counts['PASS']} FAIL:{counts['FAIL']} SKIP:{counts['SKIP']} MISS:{counts['MISS']}\n")
        for k, v in counts.items():
            total[k] = total.get(k, 0) + v

    print("══════════════════════════════════════════════")
    print(f"최종: PASS={total['PASS']}  FAIL={total['FAIL']}  SKIP={total['SKIP']}  MISS={total['MISS']}")

    total_checks = total["PASS"] + total["FAIL"] + total["SKIP"]
    skip_ratio = total["SKIP"] / total_checks if total_checks > 0 else 0

    if total["FAIL"] > 0 or total["MISS"] > 0:
        print("❌ 검증 실패 — spigen_lib.py 수정 후 슬라이드 재생성 필요")
        sys.exit(1)
    elif total_checks == 0:
        print("⚠  검증 대상 없음 — objectId 패턴 확인 필요")
        sys.exit(0)
    elif skip_ratio > 0.4:
        print(
            f"⚠  SKIP 비율 과다 ({total['SKIP']}건, {skip_ratio:.0%})"
            " — API 응답에 누락된 속성이 많습니다. objectId 패턴 또는 spigen_lib.py 버전을 확인하세요."
        )
        sys.exit(1)
    else:
        if total["SKIP"] > 0:
            print(f"⚠  SKIP {total['SKIP']}건 — 일부 속성이 API 응답에 없습니다.")
        print("✓  모든 검증 통과 — 완료 보고 가능")
        sys.exit(0)


if __name__ == "__main__":
    main()

"""
spigen_build.py — Spigen Slides v5.4

표지: 테마별 템플릿 복사 후 텍스트 교체 (클로징 없음)
중간 콘텐츠 슬라이드: createSlide로 직접 생성
헤더/색/간격 토큰: spigen_tokens 참조
"""
import os, subprocess, json, uuid
from datetime import datetime
import spigen_tokens as _T


# ─────────────────────────────────────────────────────────────────
# V5.8: PID 캐시 헬퍼 — 같은 빌드 이름에 누적 수정 (in-place 업데이트)
# ─────────────────────────────────────────────────────────────────

def _pid_cache_path(name):
    return f"/tmp/spigen_pid_{name}.json"


def load_pid(name, theme):
    """저장된 PRESENTATION_ID 로드 (없으면 None).
    name: 빌드 식별자 (예: 'foldable_qr')
    theme: 'dark' | 'light' | 'kpi'
    """
    path = _pid_cache_path(name)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return data.get(theme)
    except (json.JSONDecodeError, OSError):
        return None


def save_pid(name, theme, pid):
    """PID 저장. 같은 name+theme에 다음 빌드부터 in-place 모드 동작."""
    path = _pid_cache_path(name)
    data = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}
    data[theme] = pid
    with open(path, "w") as f:
        json.dump(data, f)


def clear_pid(name, theme=None):
    """PID 캐시 삭제 — 다음 빌드 시 새 파일 생성.
    theme=None 이면 모든 테마 삭제.
    """
    path = _pid_cache_path(name)
    if not os.path.exists(path):
        return
    if theme is None:
        os.remove(path)
        return
    try:
        with open(path) as f:
            data = json.load(f)
        data.pop(theme, None)
        with open(path, "w") as f:
            json.dump(data, f)
    except (json.JSONDecodeError, OSError):
        pass

# ── 라이트 표지 템플릿 (KPI 기준) ────────────────────────────────
LIGHT_TEMPLATE_ID  = "1BBG9PR6ZBsEABbJLhbUUfRMkgGYQtNMOWAmLQgPhr70"
LIGHT_COVER_TITLE_OID = "g3db629c31e0_0_75"   # V6.0.2: light template cover OID 갱신
LIGHT_COVER_META_OID  = "g3db629c31e0_0_76"
LIGHT_COVER_DATE_OID  = "g3db629c31e0_0_77"
LIGHT_GUIDE_SLIDES    = [
    "test_rule",
    "test_flow",
    "test_arch",
    "test_map",
    "guide_kpi_status_light",
    "guide_kpi_key_tasks_light",
]

# ── 다크 템플릿 ────────────────────────────────────────────────
DARK_TEMPLATE_ID      = "1HJbTWXPCr38gXDQuarglSLrkheDQXAojlrYUKcfVgAc"
DARK_COVER_TITLE_OID  = "g3db53c0022e_0_2"   # V5.9: 사용자가 cover 정리, 새 OID
DARK_COVER_TEAM_OID   = "g3db53c0022e_0_3"   # 부서 | 담당자
DARK_COVER_META_OID   = "g3db53c0022e_0_4"   # 날짜
DARK_GUIDE_SLIDES     = [
    "ref_toc", "g3dab74f0851_0_70", "g3e667bf10ea_0_0",
    "SLIDES_API1345277958_51", "SLIDES_API1345277958_78",
    "SLIDES_API1345277958_156", "g3e667bf10ea_0_97",
    "dsgv31_10_flow", "SLIDES_API1345277958_241",
    "gal_8e928ff12b09", "g3dab74f0851_0_37",
    "SLIDES_API1345277958_269", "SLIDES_API1345277958_296",
    "gal_572682a9c20e", "gal_bf0db096e52a",
    "guide_last_selection_v2", "g3e667bf10ea_0_135",
    "g3e667bf10ea_0_24",
]

KPI_TEMPLATE_ID     = LIGHT_TEMPLATE_ID
KPI_COVER_TITLE_OID = "g3d96284c9ce_0_1"
KPI_COVER_META_OID  = "g3d96284c9ce_0_2"
KPI_COVER_DATE_OID  = "g3d96284c9ce_0_3"
KPI_TEST_SLIDES     = ["test_rule", "test_flow", "test_arch", "test_map"]
KPI_STATUS_EYEBROW  = "guide_kpi_status_light_eyebrow"
KPI_STATUS_TITLE    = "guide_kpi_status_light_title"
KPI_STATUS_TOP_TBL  = "guide_kpi_status_light_kpi_top_tbl"
KPI_STATUS_DTL_TBL  = "guide_kpi_status_light_kpi_detail_tbl"
KPI_TASKS_EYEBROW   = "guide_kpi_key_tasks_light_eyebrow"
KPI_TASKS_TITLE     = "guide_kpi_key_tasks_light_title"
KPI_TASKS_TBL       = "guide_kpi_key_tasks_light_kpi_task_tbl"


def _uid():
    return "ob_" + uuid.uuid4().hex[:12]


def _today_cover_date():
    return datetime.now().strftime("%Y.%m.%d")


# V6.0: Spigen Design System 컬러 토큰 직접 동기화
# 출처: Spigen Dark Design System / Spigen Light Design System (colors_and_type.css)
# 알파(rgba) 토큰은 BG 위 합성 솔리드값으로 변환 (Google Slides는 RGB only).
COLORS = {
    "dark": {
        # 기본
        "bg":            {"red": 0, "green": 0, "blue": 0},               # #000000 (V6.3: 표지와 통일)
        "fg":            {"red": 0.894, "green": 0.894, "blue": 0.894},   # 88% 흰 합성 (#E4E4E4)
        "dim":           {"red": 0.769, "green": 0.769, "blue": 0.769},   # 74% (#C4C4C4)
        "fg_faint":      {"red": 0.604, "green": 0.604, "blue": 0.604},   # 56% (#9A9A9A)
        # 강조
        "accent":        {"red": 1.000, "green": 0.420, "blue": 0.102},   # #FF6B1A
        "accent_bg":     {"red": 0.227, "green": 0.145, "blue": 0.102},   # 14% accent on bg (#3A2519)
        "accent_line":   {"red": 0.596, "green": 0.278, "blue": 0.102},   # 55% (#984712)
        "accent_soft":   {"red": 0.137, "green": 0.114, "blue": 0.102},   # 4% (#231D1A)
        # 표면·라인
        "surface":       {"red": 0.149, "green": 0.149, "blue": 0.149},   # #262626 (★ 24% 밝아짐)
        "surface_hi":    {"red": 0.188, "green": 0.188, "blue": 0.188},   # #303030
        "surface_2":     {"red": 0.165, "green": 0.165, "blue": 0.165},   # #2A2A2A
        "border":        {"red": 0.208, "green": 0.208, "blue": 0.208},   # 12% 합성 (#353535)
        "border_hi":     {"red": 0.282, "green": 0.282, "blue": 0.282},   # 20% 합성 (#484848)
        # 시맨틱
        "good":          {"red": 0.612, "green": 0.890, "blue": 0.490},   # #9CE37D
        "bad":           {"red": 1.000, "green": 0.478, "blue": 0.478},   # #FF7A7A
    },
    "light": {
        # 기본
        "bg":            {"red": 1.000, "green": 1.000, "blue": 1.000},   # #FFFFFF (순백, V6.0.1 사용자 요청)
        "fg":            {"red": 0.184, "green": 0.184, "blue": 0.180},   # 88% 검정 합성 (#2F2F2E)
        "dim":           {"red": 0.412, "green": 0.408, "blue": 0.400},   # 62% (#696867)
        "fg_faint":      {"red": 0.588, "green": 0.584, "blue": 0.569},   # 42% (#969591)
        # 강조 (★ light는 더 어두운 오렌지)
        "accent":        {"red": 0.937, "green": 0.373, "blue": 0.055},   # #EF5F0E
        "accent_strong": {"red": 0.816, "green": 0.306, "blue": 0.027},   # #D04E07
        "accent_bg":     {"red": 0.957, "green": 0.898, "blue": 0.847},   # 9% accent on bg (#F4E5D8)
        "accent_line":   {"red": 0.949, "green": 0.706, "blue": 0.561},   # 42% (#F2B48F)
        "accent_soft":   {"red": 0.957, "green": 0.929, "blue": 0.890},   # 4% (#F4EDE3)
        # 표면·라인
        "surface":       {"red": 0.984, "green": 0.980, "blue": 0.965},   # #FBFAF6
        "surface_hi":    {"red": 0.925, "green": 0.918, "blue": 0.890},   # #ECEAE3
        "surface_2":     {"red": 0.898, "green": 0.886, "blue": 0.851},   # #E5E2D9
        "border":        {"red": 0.894, "green": 0.886, "blue": 0.867},   # 7% 합성 (#E4E2DD)
        "border_hi":     {"red": 0.843, "green": 0.835, "blue": 0.816},   # 13% 합성 (#D7D5D0)
        # 시맨틱
        "good":          {"red": 0.122, "green": 0.651, "blue": 0.290},   # #1FA64A
        "bad":           {"red": 0.773, "green": 0.188, "blue": 0.188},   # #C53030
    },
}


def _pt(v):
    return {"magnitude": v, "unit": "PT"}


def _emu(pt):
    return int(pt * 12700)


def _transform(x, y):
    return {
        "scaleX": 1, "scaleY": 1,
        "translateX": _emu(x), "translateY": _emu(y),
        "unit": "EMU",
    }


def _size(w, h):
    return {
        "width":  {"magnitude": _emu(w), "unit": "EMU"},
        "height": {"magnitude": _emu(h), "unit": "EMU"},
    }


def _rgb(c):
    return {"rgbColor": c}


# ── 오버플로우 방지 헬퍼 ──────────────────────────────────────────
_BODY_H = 310   # slide() 본문 박스 높이 pt
_COL_H  = 274   # two_col() 컬럼 본문 높이 pt
_LINE_H = {10: 14, 11: 15, 12: 17, 13: 18, 14: 20, 16: 23}


def _line_count(text: str) -> int:
    return max(len(text.splitlines()), 1)


def _fits(h_avail: int, lines: int, size: int) -> bool:
    return lines * _LINE_H.get(size, int(size * 1.4)) <= h_avail


def _safe_size(h_avail: int, lines: int, start: int = 14) -> int:
    """박스에 들어오는 최대 font_size 반환. 최소 10pt."""
    for s in (start, 13, 12, 11, 10):
        if _fits(h_avail, lines, s):
            return s
    return 10


class SpigenBuilder:
    def __init__(self, title, theme="dark", template="standard",
                 presentation_id=None, custom_template_id=None):
        """V6.1: cover OID 자동 매핑 + 가이드 슬라이드 자동 식별.

        다른 사용자 환경에서도 동작 — 템플릿이 변경돼도 OID 하드코딩 의존 X.

        Args:
            title:               프레젠테이션 제목
            theme:               "dark" (default V5.7) | "light"
            template:            "standard" | "kpi" (KPI는 시트 OID 의존이 커서 자동화 X)
            presentation_id:     in-place 업데이트 모드 (V5.8)
            custom_template_id:  본인 템플릿 사용 (default 템플릿 무시) — 다른 사용자 공유 시 ★

        Standard 모드 자동 매핑:
            첫 슬라이드 = cover (보존, 텍스트박스 Y 정렬해 title/team/date 매핑)
            나머지 슬라이드 = 가이드 시트 (모두 자동 deleteObject)
        """
        if theme not in COLORS:
            theme = "light"
        self.c = COLORS[theme]
        self.reqs = []
        self._n = 0
        self.template = template

        # KPI 모드 — V6.1.1: cover + KPI 시트 element OID 자동 매핑
        if template == "kpi":
            if presentation_id:
                self.pid = presentation_id
            else:
                tmpl_id = custom_template_id or KPI_TEMPLATE_ID
                self.pid = self._copy_template(tmpl_id, title)
            # cover (slide 0) + status (slide 1) + tasks (slide 2) element 자동 매핑.
            # 그 외 슬라이드는 자동 삭제 (KPI_TEST_SLIDES 하드코드 대체).
            self._discover_kpi_layout(self.pid)
            return

        # Standard 모드 — V6.1 자동 매핑
        if presentation_id:
            # in-place: 기존 파일의 cover OID 동적 매핑
            self.pid = presentation_id
            cover_oids, other = self._autodiscover_cover(presentation_id)
            self._cover_oids = cover_oids
            for oid in other:
                self.reqs.append({"deleteObject": {"objectId": oid}})
            return

        # 신규 빌드: 템플릿 복사 → cover OID 자동 매핑 → 가이드 자동 삭제
        if custom_template_id:
            tmpl_id = custom_template_id
        elif theme == "dark":
            tmpl_id = DARK_TEMPLATE_ID
        else:
            tmpl_id = LIGHT_TEMPLATE_ID
        self.pid = self._copy_template(tmpl_id, title)
        cover_oids, other = self._autodiscover_cover(self.pid)
        self._cover_oids = cover_oids
        for oid in other:
            self.reqs.append({"deleteObject": {"objectId": oid}})

    def _copy_template(self, tmpl_id, title):
        """템플릿 복사 → 새 PRESENTATION_ID 반환."""
        r = subprocess.run(
            ["gws", "drive", "files", "copy",
             "--params", json.dumps({"fileId": tmpl_id}),
             "--json", json.dumps({"name": title})],
            capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"템플릿 복사 실패: {r.stderr or r.stdout}")
        return json.loads(r.stdout)["id"]

    def _autodiscover_cover(self, presentation_id):
        """V6.1.1: cover slide 자동 분석 — size + X 좌표 기반 매핑.

        cover slide 안 텍스트박스 식별 룰:
          - 빈 텍스트박스(페이지번호 placeholder 등)는 제외
          - title  : 폰트 크기가 가장 큰 박스 (보통 36pt)
          - team   : 나머지 중 X 좌표 작은 쪽 (좌측 하단)
          - date   : 나머지 중 X 좌표 큰 쪽 (우측 하단)

        cover 외 슬라이드 OID 리스트도 반환.
        Returns: (cover_oids: tuple of 3, other_slide_oids: list)
        """
        r = subprocess.run(
            ["gws", "slides", "presentations", "get",
             "--params", json.dumps({"presentationId": presentation_id})],
            capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"파일 조회 실패: {r.stderr or r.stdout}")
        raw = r.stdout
        ji = raw.find("{")
        if ji < 0:
            raise RuntimeError(f"응답 파싱 실패: {raw[:200]}")
        data = json.loads(raw[ji:])
        slides = data.get("slides", [])
        if not slides:
            raise RuntimeError("템플릿에 슬라이드가 없음 — 최소 cover 1장 필요")
        cover = slides[0]
        # cover slide 안 텍스트박스 추출 (빈 placeholder 제외)
        text_boxes = []
        for elem in cover.get("pageElements", []):
            sh = elem.get("shape", {})
            if "text" not in sh:
                continue
            # 콘텐츠 + 폰트 사이즈 추출
            has_content = False
            first_size = 0
            for t in sh["text"].get("textElements", []):
                tr = t.get("textRun")
                if tr and tr.get("content", "").strip():
                    has_content = True
                    sz = tr.get("style", {}).get("fontSize", {}).get("magnitude", 0)
                    if sz and not first_size:
                        first_size = sz
            if not has_content:
                continue  # 빈 placeholder (페이지번호 등) 무시
            tx = elem.get("transform", {})
            x = tx.get("translateX", 0)
            y = tx.get("translateY", 0)
            text_boxes.append({
                "oid": elem.get("objectId", ""),
                "x": x, "y": y, "size": first_size,
            })
        if len(text_boxes) < 3:
            raise RuntimeError(
                f"cover slide의 (콘텐츠 있는) 텍스트박스가 3개 미만 "
                f"({len(text_boxes)}개). 제목·부서·날짜 3개 필요. "
                f"cover slide ID: {cover.get('objectId')}"
            )
        # title = 폰트 크기 가장 큰 것
        title_box = max(text_boxes, key=lambda t: t["size"])
        others = [t for t in text_boxes if t["oid"] != title_box["oid"]]
        # team/date = 나머지 중 X 좌측 = team, 우측 = date
        others.sort(key=lambda t: t["x"])
        team_box = others[0]
        date_box = others[1]
        cover_oids = (title_box["oid"], team_box["oid"], date_box["oid"])
        other_slide_oids = [s["objectId"] for s in slides[1:]]
        return cover_oids, other_slide_oids

    def _discover_kpi_layout(self, presentation_id):
        """V6.1.1: KPI 모드 element OID 자동 매핑.

        고정 인덱스:
          slide 0 = cover  → cover_oids 자동 매핑 (title/team/date)
          slide 1 = KPI status → eyebrow/title/top_tbl/detail_tbl 자동 매핑
          slide 2 = KPI tasks  → eyebrow/title/tbl 자동 매핑

        slide 3+ = 가이드/테스트 시트 → 자동 삭제

        매핑 룰 (텍스트 내용 기반 분석 X):
          - title  : 텍스트박스 중 폰트 크기 가장 큼 (보통 22pt)
          - eyebrow: title 아닌 텍스트박스 중 Y 가장 작음
          - tables : TABLE 타입 element를 Y 정렬, 첫 번째 = top_tbl, 두 번째 = detail_tbl
        """
        r = subprocess.run(
            ["gws", "slides", "presentations", "get",
             "--params", json.dumps({"presentationId": presentation_id})],
            capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"KPI 파일 조회 실패: {r.stderr or r.stdout}")
        raw = r.stdout
        ji = raw.find("{")
        if ji < 0:
            raise RuntimeError(f"KPI 응답 파싱 실패: {raw[:200]}")
        data = json.loads(raw[ji:])
        slides = data.get("slides", [])
        if len(slides) < 3:
            raise RuntimeError(
                f"KPI 템플릿 슬라이드 부족 ({len(slides)}개). "
                f"slide 0=cover, 1=status, 2=tasks 최소 3장 필요."
            )

        # cover (slide 0) 자동 매핑 — _autodiscover_cover와 동일 룰
        cover = slides[0]
        cover_text_boxes = []
        for elem in cover.get("pageElements", []):
            sh = elem.get("shape", {})
            if "text" not in sh:
                continue
            has_content = False
            first_size = 0
            for t in sh["text"].get("textElements", []):
                tr = t.get("textRun")
                if tr and tr.get("content", "").strip():
                    has_content = True
                    sz = tr.get("style", {}).get("fontSize", {}).get("magnitude", 0)
                    if sz and not first_size:
                        first_size = sz
            if not has_content:
                continue
            tx = elem.get("transform", {})
            cover_text_boxes.append({
                "oid": elem.get("objectId", ""),
                "x": tx.get("translateX", 0),
                "size": first_size,
            })
        if len(cover_text_boxes) < 3:
            raise RuntimeError(f"KPI cover 텍스트박스 3개 미만 ({len(cover_text_boxes)}개)")
        title_b = max(cover_text_boxes, key=lambda t: t["size"])
        others = [t for t in cover_text_boxes if t["oid"] != title_b["oid"]]
        others.sort(key=lambda t: t["x"])
        self._cover_oids = (title_b["oid"], others[0]["oid"], others[1]["oid"])

        # status slide (slide 1) element 매핑
        status_layout = self._extract_kpi_slide_layout(slides[1], slide_label="status")
        # tasks slide (slide 2) element 매핑
        tasks_layout = self._extract_kpi_slide_layout(slides[2], slide_label="tasks")

        self._kpi_oids = {
            "status_eyebrow": status_layout["eyebrow"],
            "status_title": status_layout["title"],
            "status_top_tbl": status_layout["tables"][0] if status_layout["tables"] else None,
            "status_detail_tbl": status_layout["tables"][1] if len(status_layout["tables"]) > 1 else None,
            "tasks_eyebrow": tasks_layout["eyebrow"],
            "tasks_title": tasks_layout["title"],
            "tasks_tbl": tasks_layout["tables"][0] if tasks_layout["tables"] else None,
        }

        # slide 3+ 자동 삭제 (KPI_TEST_SLIDES 하드코드 대체)
        for s in slides[3:]:
            self.reqs.append({"deleteObject": {"objectId": s["objectId"]}})

    def _extract_kpi_slide_layout(self, slide, slide_label=""):
        """KPI status/tasks slide 안 element 자동 매핑.
        Returns: {"eyebrow": oid, "title": oid, "tables": [oid, ...]}
        """
        text_boxes = []
        tables = []
        for e in slide.get("pageElements", []):
            tx = e.get("transform", {})
            y = tx.get("translateY", 0)
            tbl = e.get("table")
            sh = e.get("shape", {})
            if tbl:
                tables.append((y, e.get("objectId", "")))
                continue
            if "text" not in sh:
                continue
            sz = 0
            has_content = False
            for t in sh["text"].get("textElements", []):
                tr = t.get("textRun")
                if tr and tr.get("content", "").strip():
                    has_content = True
                    s = tr.get("style", {}).get("fontSize", {}).get("magnitude", 0)
                    if s and not sz:
                        sz = s
            if has_content:
                text_boxes.append({"oid": e.get("objectId", ""), "y": y, "size": sz})
        if len(text_boxes) < 2:
            raise RuntimeError(
                f"KPI {slide_label} slide 텍스트박스 2개 미만 ({len(text_boxes)}개)"
            )
        if not tables:
            raise RuntimeError(f"KPI {slide_label} slide TABLE 부재")
        title_b = max(text_boxes, key=lambda t: t["size"])
        eb_candidates = [t for t in text_boxes if t["oid"] != title_b["oid"]]
        eyebrow_b = min(eb_candidates, key=lambda t: t["y"])
        tables.sort()
        return {
            "eyebrow": eyebrow_b["oid"],
            "title": title_b["oid"],
            "tables": [oid for _, oid in tables],
        }

    def _next(self):
        """콘텐츠 슬라이드용 (oid, idx) 반환 후 카운터 증가."""
        oid = _uid()
        idx = 1 + self._n   # 커버(0) 뒤에 순서대로 삽입
        self._n += 1
        return oid, idx

    # ── 기본 프리미티브 ────────────────────────────────────────────

    def _slide(self, oid, idx):
        self.reqs.append({
            "createSlide": {
                "objectId": oid,
                "insertionIndex": idx,
                "slideLayoutReference": {"predefinedLayout": "BLANK"},
            }
        })

    def _bg(self, oid):
        self.reqs.append({
            "updatePageProperties": {
                "objectId": oid,
                "pageProperties": {
                    "pageBackgroundFill": {
                        "solidFill": {"color": _rgb(self.c["bg"])}
                    }
                },
                "fields": "pageBackgroundFill",
            }
        })

    def _shape(self, page_oid, shape_oid, x, y, w, h, valign="MIDDLE"):
        """텍스트박스 생성 + 세로 정렬 자동 적용.
        valign: TOP / MIDDLE / BOTTOM. 기본값 MIDDLE — 모든 텍스트 세로 중앙.
        """
        self.reqs.append({
            "createShape": {
                "objectId": shape_oid,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": page_oid,
                    "size": _size(w, h),
                    "transform": _transform(x, y),
                },
            }
        })
        if valign:
            self.reqs.append({
                "updateShapeProperties": {
                    "objectId": shape_oid,
                    "shapeProperties": {"contentAlignment": valign},
                    "fields": "contentAlignment",
                }
            })

    def _text(self, oid, text):
        self.reqs.append({
            "insertText": {"objectId": oid, "insertionIndex": 0, "text": text}
        })

    def _text_md(self, oid, text):
        """**굵게** 마크업 인식해서 텍스트 삽입 + bold 범위 반환.

        예: '관리 **복잡** 발생' → 'bold_ranges' 에는 (3, 5) 반환.
        호출자는 _style() 후 _apply_bold_ranges(oid, ranges) 호출.
        """
        import re
        parts = re.split(r"(\*\*[^*]+\*\*)", text)
        full_text = ""
        bold_ranges = []
        for part in parts:
            if part.startswith("**") and part.endswith("**") and len(part) > 4:
                inner = part[2:-2]
                start = len(full_text)
                full_text += inner
                bold_ranges.append((start, len(full_text)))
            else:
                full_text += part
        if full_text:
            self._text(oid, full_text)
        return bold_ranges

    def _apply_bold_ranges(self, oid, ranges):
        """_text_md 후 호출 — 지정 범위만 bold 적용."""
        for start, end in ranges:
            self.reqs.append({
                "updateTextStyle": {
                    "objectId": oid,
                    "style": {"bold": True},
                    "textRange": {"type": "FIXED_RANGE",
                                  "startIndex": start, "endIndex": end},
                    "fields": "bold",
                }
            })

    def _style(self, oid, size, bold=False, color=None, italic=False, align="START", font_family="Noto Sans KR"):
        if color is None:
            color = self.c["fg"]
        # V6.3: 9pt 본문(non-bold)에 line spacing 1.5 (150%) 자동 적용
        para_style = {"alignment": align}
        para_fields = "alignment"
        if size == 9 and not bold:
            para_style["lineSpacing"] = 150
            para_fields += ",lineSpacing"
        self.reqs += [
            {
                "updateTextStyle": {
                    "objectId": oid,
                    "style": {
                        "fontSize": _pt(size),
                        "bold": bold,
                        "italic": italic,
                        "foregroundColor": {"opaqueColor": _rgb(color)},
                        "fontFamily": font_family,
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "fontSize,bold,italic,foregroundColor,fontFamily",
                }
            },
            {
                "updateParagraphStyle": {
                    "objectId": oid,
                    "style": para_style,
                    "textRange": {"type": "ALL"},
                    "fields": para_fields,
                }
            },
        ]

    def _hline(self, page_oid, x, y, w, weight=2, color=None):
        if color is None:
            color = self.c["accent"]
        oid = _uid()
        self.reqs.append({
            "createLine": {
                "objectId": oid,
                "lineCategory": "STRAIGHT",
                "elementProperties": {
                    "pageObjectId": page_oid,
                    "size": {"width": {"magnitude": _emu(w), "unit": "EMU"},
                             "height": {"magnitude": 0, "unit": "EMU"}},
                    "transform": _transform(x, y),
                },
            }
        })
        self.reqs.append({
            "updateLineProperties": {
                "objectId": oid,
                "lineProperties": {
                    "lineFill": {"solidFill": {"color": _rgb(color)}},
                    "weight": _pt(weight),
                },
                "fields": "lineFill,weight",
            }
        })

    def _vline(self, page_oid, x, y, h, weight=4, color=None):
        if color is None:
            color = self.c["accent"]
        oid = _uid()
        self.reqs.append({
            "createLine": {
                "objectId": oid,
                "lineCategory": "STRAIGHT",
                "elementProperties": {
                    "pageObjectId": page_oid,
                    "size": {"width": {"magnitude": 0, "unit": "EMU"},
                             "height": {"magnitude": _emu(h), "unit": "EMU"}},
                    "transform": _transform(x, y),
                },
            }
        })
        self.reqs.append({
            "updateLineProperties": {
                "objectId": oid,
                "lineProperties": {
                    "lineFill": {"solidFill": {"color": _rgb(color)}},
                    "weight": _pt(weight),
                },
                "fields": "lineFill,weight",
            }
        })

    # ── 슬라이드 타입 ──────────────────────────────────────────────

    def _replace_text(self, oid, text):
        """shape 텍스트 전체 교체 (deleteText + insertText)."""
        self.reqs += [
            {"deleteText": {"objectId": oid, "textRange": {"type": "ALL"}}},
            {"insertText": {"objectId": oid, "insertionIndex": 0, "text": text}},
        ]

    def _tbl_cell(self, tbl_oid, row, col, text):
        """테이블 셀 텍스트 교체. 빈/None 값은 skip — merged 이차 셀 deleteText 오류 방지."""
        if text is None:
            return
        text = str(text).strip()
        if not text:
            return
        self.reqs += [
            {"deleteText": {
                "objectId": tbl_oid,
                "cellLocation": {"rowIndex": row, "columnIndex": col},
                "textRange": {"type": "ALL"},
            }},
            {"insertText": {
                "objectId": tbl_oid,
                "cellLocation": {"rowIndex": row, "columnIndex": col},
                "insertionIndex": 0,
                "text": text,
            }},
        ]

    def cover(self, title, subtitle="", dept="디자인부문ㅣ패키지디자인팀",
              name="한원진 담당", date=None):
        """표지: 템플릿 커버 슬라이드의 텍스트를 교체.

        V5.9: title + subtitle 합계 2줄 이내 강제.
              합계 3줄 이상이면 subtitle 자동 제거, title도 2줄 초과면 트림.
        """
        # V5.9 가드: title + subtitle 합계 2줄 이내
        title_lines = title.count("\n") + 1
        sub_lines = (subtitle.count("\n") + 1) if subtitle else 0
        total = title_lines + sub_lines
        if total > 2:
            print(f"[WARN] cover title+subtitle 합계 {total}줄 → 2줄 한도 초과, subtitle 자동 제거")
            subtitle = ""
            # title 자체가 2줄 초과면 마저 트림
            if title_lines > 2:
                parts = title.split("\n")
                print(f"[WARN] cover title {title_lines}줄 → 2줄로 트림")
                title = "\n".join(parts[:2])
        title_oid, meta_oid, date_oid = self._cover_oids
        title_text = f"{title}\n{subtitle}" if subtitle else title
        meta_text  = f"{dept}\n{name}"
        date_text = date if date is not None else _today_cover_date()
        # V5.9: 표지 표준 폰트 사이즈 (light template 기준 — dark는 가이드 덱이라 14.5)
        # 일반 표지 표준: title 36 / meta 12 / date 12 (양 테마 통일)
        title_size = 36
        meta_size = 12
        entries = [
            (title_oid, title_text, title_size, True),
            (meta_oid,  meta_text,  meta_size,  False),
            (date_oid,  date_text,  meta_size,  False),
        ]
        for oid, text, size, bold in entries:
            self.reqs += [
                {"deleteText": {"objectId": oid, "textRange": {"type": "ALL"}}},
                {"insertText": {"objectId": oid, "insertionIndex": 0, "text": text}},
                {"updateTextStyle": {
                    "objectId": oid,
                    "style": {
                        "fontSize": _pt(size),
                        "bold": bold,
                        "fontFamily": "Noto Sans KR",
                        "foregroundColor": {"opaqueColor": _rgb(self.c["fg"])},
                    },
                    "textRange": {"type": "ALL"},
                    "fields": "fontSize,bold,fontFamily,foregroundColor",
                }},
            ]

    def slide(self, heading, body, body_size=14):
        """본문: 헤더 + 오렌지 가로선 + 텍스트박스"""
        oid, idx = self._next()
        self._slide(oid, idx)
        self._bg(oid)

        h = _uid()
        self._shape(oid, h, 40, 20, 640, 38)
        self._text(h, heading)
        self._style(h, 22, bold=True)


        b = _uid()
        self._shape(oid, b, 40, 72, 640, 310)
        self._text(b, body)
        self._style(b, body_size)

    def two_col(self, heading, left_title, left_body, right_title, right_body):
        """2단 슬라이드: 헤더 + 왼쪽/오른쪽 패널"""
        oid, idx = self._next()
        self._slide(oid, idx)
        self._bg(oid)

        h = _uid()
        self._shape(oid, h, 40, 20, 640, 38)
        self._text(h, heading)
        self._style(h, 22, bold=True)


        lt = _uid()
        self._shape(oid, lt, 40, 76, 310, 28)
        self._text(lt, left_title)
        self._style(lt, 15, bold=True, color=self.c["accent"])

        lb = _uid()
        self._shape(oid, lb, 40, 108, 310, 274)
        self._text(lb, left_body)
        self._style(lb, 13)

        self._vline(oid, 365, 76, 300, weight=1, color=self.c["dim"])

        rt = _uid()
        self._shape(oid, rt, 375, 76, 310, 28)
        self._text(rt, right_title)
        self._style(rt, 15, bold=True, color=self.c["accent"])

        rb = _uid()
        self._shape(oid, rb, 375, 108, 310, 274)
        self._text(rb, right_body)
        self._style(rb, 13)

    def auto_slide(self, role, heading,
                   body=None,
                   left_title=None, left_body=None,
                   right_title=None, right_body=None,
                   steps=None, items=None,
                   question=None,
                   yes_label=None, yes_body=None,
                   no_label=None, no_body=None):
        """역할 기반 자동 컴포넌트 선택 + 오버플로우 방지.

        role: "설명" | "결정유도" | "비교" | "순서" | "체크" | "분기"
        내용이 박스를 초과하면 font_size를 자동 축소 (최소 10pt).
        내용은 절대 자르지 않는다.
        """
        if role in ("설명", "결정유도"):
            lines = _line_count(body or "")
            size = _safe_size(_BODY_H, lines, start=14)
            self.slide(heading, body or "", body_size=size)

        elif role == "비교":
            self.two_col(
                heading,
                left_title or "", left_body or "",
                right_title or "", right_body or "",
            )

        elif role == "순서":
            self.flow(heading, steps or [])

        elif role == "체크":
            self.checklist(heading, items or [])

        elif role == "분기":
            self.decision(
                heading,
                question or "",
                yes_label or "", yes_body or "",
                no_label or "", no_body or "",
            )

        else:
            lines = _line_count(body or "")
            size = _safe_size(_BODY_H, lines, start=14)
            self.slide(heading, body or "", body_size=size)

    def flow(self, heading, steps):
        """흐름 슬라이드: 헤더 + 번호 단계 목록. steps = [(label, desc), ...]"""
        oid, idx = self._next()
        self._slide(oid, idx)
        self._bg(oid)

        h = _uid()
        self._shape(oid, h, 40, 20, 640, 38)
        self._text(h, heading)
        self._style(h, 22, bold=True)


        step_h = max(16, min(60, 290 // max(len(steps), 1)))
        for i, (label, desc) in enumerate(steps):
            y = 72 + i * (step_h + 6)
            num = _uid()
            self._shape(oid, num, 40, y, 32, step_h)
            self._text(num, str(i + 1))
            self._style(num, 16, bold=True, color=self.c["accent"], align="CENTER")

            self._vline(oid, 80, y + 4, step_h - 8, weight=1, color=self.c["dim"])

            body = _uid()
            self._shape(oid, body, 90, y, 590, step_h)
            self._text(body, f"{label}\n{desc}" if desc else label)
            self._style(body, 13)

    def decision(self, heading, question, yes_label, yes_body, no_label, no_body):
        """분기 슬라이드: 헤더 + 질문 박스 + YES/NO 패널"""
        oid, idx = self._next()
        self._slide(oid, idx)
        self._bg(oid)

        h = _uid()
        self._shape(oid, h, 40, 20, 640, 38)
        self._text(h, heading)
        self._style(h, 22, bold=True)


        q = _uid()
        self._shape(oid, q, 160, 72, 400, 44)
        self._text(q, question)
        self._style(q, 15, bold=True, align="CENTER")
        self._hline(oid, 160, 118, 400, weight=1, color=self.c["dim"])

        yl = _uid()
        self._shape(oid, yl, 40, 130, 300, 28)
        self._text(yl, f"✓  {yes_label}")
        self._style(yl, 14, bold=True, color=self.c["accent"])

        yb = _uid()
        self._shape(oid, yb, 40, 162, 300, 210)
        self._text(yb, yes_body)
        self._style(yb, 13)

        self._vline(oid, 355, 130, 230, weight=1, color=self.c["dim"])

        nl = _uid()
        self._shape(oid, nl, 365, 130, 315, 28)
        self._text(nl, f"✗  {no_label}")
        self._style(nl, 14, bold=True, color=self.c["dim"])

        nb = _uid()
        self._shape(oid, nb, 365, 162, 315, 210)
        self._text(nb, no_body)
        self._style(nb, 13)

    def checklist(self, heading, items, eyebrow=""):
        """체크리스트 슬라이드: 헤더 + 항목 목록.

        V5.9: 헤더 생성을 _make_slide_with_header로 통일 — 좌표 일관성 자동 보장.

        Args:
            heading: 22pt 슬라이드 타이틀
            items: [(label, done), ...]
            eyebrow: 타이틀 위 8pt ORANGE 메타 (선택)
        """
        oid = self._make_slide_with_header(heading=heading, eyebrow=eyebrow)

        # V5.7: 콘텐츠 시작 y=100, 끝 y=373 (위·아래 32pt 빈 여백 대칭)
        content_y_start = 100
        content_y_end = 373  # 405 - 32 (eyebrow 시작과 대칭)
        n = max(len(items), 1)
        gap = 4
        # 마지막 항목 끝 y = start + (n-1)*(item_h+gap) + item_h <= end
        # → item_h <= (end - start - (n-1)*gap) / n
        max_item_h = (content_y_end - content_y_start - (n - 1) * gap) // n
        item_h = max(16, min(52, max_item_h))
        for i, (label, done) in enumerate(items):
            y = content_y_start + i * (item_h + 4)
            mark = _uid()
            self._shape(oid, mark, 40, y, 32, item_h)
            self._text(mark, "●" if done else "○")
            color = self.c["accent"] if done else self.c["dim"]
            # V5.8: 다른 페이지 본문 폰트 위계와 일관 (16→12)
            self._style(mark, 12, color=color, align="CENTER")

            txt = _uid()
            self._shape(oid, txt, 82, y, 598, item_h)
            self._text(txt, label)
            # V5.8: card title 위계(10.5)와 일관 (13→10.5)
            self._style(txt, 10.5, color=self.c["dim"] if done else self.c["fg"])

    def numbered_steps(self, heading, items, eyebrow=""):
        """순서 안내 슬라이드 — 01-NN 숫자 라벨 + 항목 텍스트.

        의도: "이 순서대로 따라해라". checklist(점검)와 의도 분리.

        헬퍼 선택 가이드:
            - "방법", "순서", "단계", "절차", "흐름" 표현 → 이 헬퍼 (numbered_steps)
            - "체크리스트", "점검", "확인 항목" 표현 → checklist
            - 사용자가 마크가 아닌 진행 순서를 보고 싶다면 이 헬퍼

        V6.2: x=48 (자유 빌딩 블록 마진과 정렬, 헤더와 좌측 통일).

        Args:
            heading: 22pt 슬라이드 타이틀
            items: [label, ...] 또는 [(label, done), ...]
                done은 호환 위해 받지만 무시 (모두 활성 라벨)
            eyebrow: 타이틀 위 8pt ORANGE 메타 (선택)
        """
        oid = self._make_slide_with_header(heading=heading, eyebrow=eyebrow)
        content_y_start = 100
        content_y_end = 373
        n = max(len(items), 1)
        gap = 4
        max_item_h = (content_y_end - content_y_start - (n - 1) * gap) // n
        item_h = max(16, min(52, max_item_h))
        for i, item in enumerate(items):
            label = item[0] if isinstance(item, tuple) else item
            y = content_y_start + i * (item_h + 4)
            mark = _uid()
            self._shape(oid, mark, 48, y, 32, item_h)
            self._text(mark, f"{i+1:02d}")
            self._style(mark, 10.5, bold=True, color=self.c["accent"], align="CENTER")

            txt = _uid()
            self._shape(oid, txt, 88, y, 584, item_h)
            self._text(txt, label)
            self._style(txt, 10.5, color=self.c["fg"])

    def kpi_status(self, title="1. KPI 진행 현황", eyebrow="2025년도",
                   top_rows=None, detail_rows=None):
        """KPI 현황 슬라이드: 템플릿 슬라이드 텍스트 교체. template='kpi' 전용.
        top_rows: [[목표, kpi, 가중치, h1목표, h1실적, h1달성률, 연간목표, 연간실적, 연간달성률], ...]  (최대 3행)
        detail_rows: [[kpi, 정의, 측정산식, 증빙], ...]  (최대 3행)
        """
        if self.template != "kpi":
            raise ValueError("kpi_status()는 template='kpi'에서만 사용 가능합니다.")
        # V6.1.1: __init__에서 자동 매핑된 self._kpi_oids 사용
        self._replace_text(self._kpi_oids["status_eyebrow"], eyebrow)
        self._replace_text(self._kpi_oids["status_title"], title)
        for ri, row in enumerate((top_rows or [])[:3]):
            for ci, val in enumerate(row[:9]):
                if ri == 1 and ci == 0:
                    continue  # [2,0] rs=2 merge가 row3 col0을 cover — 쓰기 불가
                self._tbl_cell(self._kpi_oids["status_top_tbl"], ri + 2, ci, val)
        for ri, row in enumerate((detail_rows or [])[:3]):
            for ci, val in enumerate(row[:4]):
                self._tbl_cell(self._kpi_oids["status_detail_tbl"], ri + 1, ci, val)

    def kpi_tasks(self, title="2. 핵심과제", eyebrow="2025", rows=None):
        """주요 과제 슬라이드: 템플릿 슬라이드 텍스트 교체. template='kpi' 전용.
        rows: [[연관kpi, 핵심과제, 실행계획, 나의역할], ...]  (최대 3행)
        """
        if self.template != "kpi":
            raise ValueError("kpi_tasks()는 template='kpi'에서만 사용 가능합니다.")
        # V6.1.1: 자동 매핑된 self._kpi_oids 사용
        self._replace_text(self._kpi_oids["tasks_eyebrow"], eyebrow)
        self._replace_text(self._kpi_oids["tasks_title"], title)
        for ri, row in enumerate((rows or [])[:3]):
            for ci, val in enumerate(row[:4]):
                if ri == 1 and ci == 0:
                    continue  # [1,0] rowSpan=2 → row 2 col 0은 covered cell
                self._tbl_cell(self._kpi_oids["tasks_tbl"], ri + 1, ci, val)

    # ── 빌딩 블록 (자유 레이아웃) ─────────────────────────────────
    # 시트 디자인을 "참고만" 하면서 콘텐츠 구조에 맞게 자유 조합.
    # mk_* 컴포넌트의 슬롯 강제를 우회하고 싶을 때 사용.

    def _rect(self, page_oid, x, y, w, h, fill, border, weight=0.5):
        """채움+테두리가 있는 사각형 한 개 그리기."""
        oid = _uid()
        self.reqs.append({
            "createShape": {
                "objectId": oid,
                "shapeType": "RECTANGLE",
                "elementProperties": {
                    "pageObjectId": page_oid,
                    "size": _size(w, h),
                    "transform": _transform(x, y),
                },
            }
        })
        self.reqs.append({
            "updateShapeProperties": {
                "objectId": oid,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": _rgb(fill)}},
                    "outline": {
                        "outlineFill": {"solidFill": {"color": _rgb(border)}},
                        "weight": _pt(weight),
                    },
                },
                "fields": "shapeBackgroundFill,outline",
            }
        })
        return oid

    def _make_slide_with_header(self, heading="", eyebrow=""):
        """V5.9 단일 진입점 — 모든 슬라이드 생성의 공통 헤더 함수.

        모든 콘텐츠 슬라이드 메서드 (start_slide / checklist / conclusion 등)는
        이 함수를 호출해서 헤더 좌표·폰트·여백 일관성 자동 보장.

        좌표 토큰: spigen_tokens.HEADER 참조
        - eyebrow: y=32, h=10, 8pt bold ORANGE, valign=MIDDLE
        - title (with eyebrow): y=46, h=26, 22pt bold, valign=MIDDLE
        - title (only):         y=20, h=38, 22pt bold, valign=MIDDLE

        반환: 슬라이드 OID
        """
        oid, idx = self._next()
        self._slide(oid, idx)
        self._bg(oid)
        if eyebrow:
            eb = _uid()
            self._shape(oid, eb, 40, 32, 320, 10)
            self._text(eb, eyebrow)
            self._style(eb, 8, bold=True, color=self.c["accent"])
            if heading:
                h = _uid()
                self._shape(oid, h, 40, 46, 640, 26)
                self._text(h, heading)
                self._style(h, 22, bold=True)
        elif heading:
            h = _uid()
            self._shape(oid, h, 40, 20, 640, 38)
            self._text(h, heading)
            self._style(h, 22, bold=True)
        self._current_slide = oid
        return oid

    def start_slide(self, heading="", eyebrow=""):
        """자유 레이아웃 슬라이드 시작 — _make_slide_with_header 의 public 진입점.

        eyebrow: 타이틀 위 8pt bold ORANGE 메타 (선택)
        heading: 22pt bold 슬라이드 타이틀

        반환: 슬라이드 OID. 이후 빌딩 블록(card/flow_step/compare_pair 등) 자유 호출.
        """
        return self._make_slide_with_header(heading=heading, eyebrow=eyebrow)

    def card(self, x, y, w, h, title="", body="", label="", primary=False,
             emphasis=None, footer_label="", footer_body=""):
        """카드 블록 — 카드 높이에 따라 자동 모드 선택.

        - h >= 80 + (label/title/body 3섹션): 시트 표준 좌표
            label_y=16, title_y=39, body_y=79
        - h < 80 또는 단일/이중 섹션: 카드 가득 채워 vertical-center 배치

        폰트:
          - label: 8pt bold
          - title: 10.5pt bold
          - body: 8pt regular

        강조 (emphasis):
          - None / "normal" : surface fill + border (일반)
          - "dim"           : accent_bg + accent border (약한 강조, 기존 primary=True)
          - "full"          : accent 풀 ORANGE 배경 + 검정 텍스트 (강한 강조)

        primary=True 는 emphasis="dim" 호환 유지.
        """
        sid = getattr(self, "_current_slide", None)
        if sid is None:
            raise RuntimeError("card(): start_slide()를 먼저 호출하세요.")
        fg = self.c["fg"]
        # primary 호환
        if primary and emphasis is None:
            emphasis = "dim"
        if emphasis == "full":
            fill = self.c["accent"]
            border = self.c["accent"]
            border_w = 0.5
            # V6.3.3: 풀 오렌지 카드 안 텍스트 = 테마 바탕색
            #   dark → bg=#000000 (검정), light → bg=#FFFFFF (흰색)
            label_color = self.c["bg"]
            title_color = self.c["bg"]
            body_color = self.c["bg"]
        elif emphasis == "dim":
            fill = self.c["accent_bg"]
            border = self.c["accent"]
            border_w = 0.5
            label_color = self.c["accent"]
            title_color = fg
            body_color = self.c["dim"]
        else:
            fill = self.c["surface"]
            border = self.c["border"]
            border_w = 0.4
            label_color = self.c["accent"]  # V6.3: 카드 라벨(eyebrow) 항상 accent (full 제외)
            title_color = fg
            body_color = self.c["dim"]
        self._rect(sid, x, y, w, h, fill, border, border_w)
        pad_x = 18
        sections = [s for s in (label, title, body) if s]
        # 소형 경로: h < 80 → 우선순위 단일 섹션 (title > body > label)
        if h < 80:
            if title:
                to = _uid()
                self._shape(sid, to, x + pad_x, y, w - pad_x * 2, h)
                br = self._text_md(to, title)
                self._style(to, 10.5, bold=True, color=title_color)
                self._apply_bold_ranges(to, br)
            elif body:
                bo = _uid()
                self._shape(sid, bo, x + pad_x, y, w - pad_x * 2, h)
                br = self._text_md(bo, body)
                self._style(bo, 9, color=body_color)
                self._apply_bold_ranges(bo, br)
            elif label:
                lo = _uid()
                self._shape(sid, lo, x + pad_x, y, w - pad_x * 2, h)
                self._text(lo, str(label).upper())
                self._style(lo, 8, bold=True, color=label_color)
            return
        # 3섹션 미만 (h >= 80): 스택 배치 — 대형 고정 좌표 사용 안 함
        if len(sections) < 3:
            pad_v, gap = 16, 6
            if label and title and not body:
                lo = _uid()
                self._shape(sid, lo, x + pad_x, y + pad_v, w - pad_x * 2, 12)
                self._text(lo, str(label).upper())
                self._style(lo, 8, bold=True, color=label_color)
                to = _uid()
                ty = y + pad_v + 12 + gap
                self._shape(sid, to, x + pad_x, ty, w - pad_x * 2, max(16, h - (ty - y) - pad_v))
                br = self._text_md(to, title)
                self._style(to, 10.5, bold=True, color=title_color)
                self._apply_bold_ranges(to, br)
            elif title and body and not label:
                to = _uid()
                self._shape(sid, to, x + pad_x, y + pad_v, w - pad_x * 2, 20)
                br = self._text_md(to, title)
                self._style(to, 10.5, bold=True, color=title_color)
                self._apply_bold_ranges(to, br)
                bo = _uid()
                by = y + pad_v + 20 + gap
                self._shape(sid, bo, x + pad_x, by, w - pad_x * 2, max(16, h - (by - y) - pad_v))
                br = self._text_md(bo, body)
                self._style(bo, 9, color=body_color)
                self._apply_bold_ranges(bo, br)
            elif label and body and not title:
                lo = _uid()
                self._shape(sid, lo, x + pad_x, y + pad_v, w - pad_x * 2, 12)
                self._text(lo, str(label).upper())
                self._style(lo, 8, bold=True, color=label_color)
                bo = _uid()
                by = y + pad_v + 12 + gap
                self._shape(sid, bo, x + pad_x, by, w - pad_x * 2, max(16, h - (by - y) - pad_v))
                br = self._text_md(bo, body)
                self._style(bo, 9, color=body_color)
                self._apply_bold_ranges(bo, br)
            else:  # 1섹션 (h >= 80): 카드 전체 채움
                if title:
                    to = _uid()
                    self._shape(sid, to, x + pad_x, y, w - pad_x * 2, h)
                    br = self._text_md(to, title)
                    self._style(to, 10.5, bold=True, color=title_color)
                    self._apply_bold_ranges(to, br)
                elif body:
                    bo = _uid()
                    self._shape(sid, bo, x + pad_x, y, w - pad_x * 2, h)
                    br = self._text_md(bo, body)
                    self._style(bo, 9, color=body_color)
                    self._apply_bold_ranges(bo, br)
                elif label:
                    lo = _uid()
                    self._shape(sid, lo, x + pad_x, y, w - pad_x * 2, h)
                    self._text(lo, str(label).upper())
                    self._style(lo, 8, bold=True, color=label_color)
            return
        # 3섹션 대형 카드 (h >= 80, label+title+body 모두 있음): 시트 표준 고정 좌표
        # footer 사용 시 본문 영역 줄임
        has_footer = bool(footer_label or footer_body)
        footer_h = 56 if has_footer else 0
        if label:
            lo = _uid()
            self._shape(sid, lo, x + pad_x, y + 16, w - pad_x * 2, 12)
            self._text(lo, str(label).upper())
            self._style(lo, 8, bold=True, color=label_color)
        if title:
            to = _uid()
            self._shape(sid, to, x + pad_x, y + 39, w - pad_x * 2, 28)
            br = self._text_md(to, title)
            self._style(to, 10.5, bold=True, color=title_color)
            self._apply_bold_ranges(to, br)
        if body:
            bo = _uid()
            body_y = y + 79 if (label or title) else y + 16
            body_h = max(16, h - (body_y - y) - 14 - footer_h)
            self._shape(sid, bo, x + pad_x, body_y, w - pad_x * 2, body_h)
            br = self._text_md(bo, body)
            self._style(bo, 9, color=body_color)
            self._apply_bold_ranges(bo, br)
        # footer 섹션 (divider + label + body)
        if has_footer:
            footer_y = y + h - footer_h - 8
            # divider
            self._hline(sid, x + pad_x, footer_y, w - pad_x * 2,
                        weight=0.5, color=self.c["dim"])
            if footer_label:
                flo = _uid()
                self._shape(sid, flo, x + pad_x, footer_y + 6,
                            w - pad_x * 2, 12)
                self._text(flo, str(footer_label).upper())
                self._style(flo, 8, bold=True, color=label_color)
            if footer_body:
                fbo = _uid()
                self._shape(sid, fbo, x + pad_x, footer_y + 22,
                            w - pad_x * 2, 24)
                br = self._text_md(fbo, footer_body)
                self._style(fbo, 10, bold=True, color=title_color)
                self._apply_bold_ranges(fbo, br)

    def flow_step(self, x, y, w, h, num, name, desc="", primary=False):
        """플로우 단계 1개 — mk_flow_focus 시트 표준 좌표 사용.

        시트 측정값:
          - padding_x=16, num_y=14, name_y=36, desc_y=62
          - num=10B (오렌지), name=14B, desc=10 (dim)
          - 일반: surface + border, primary: accent_bg + accent border
        """
        sid = getattr(self, "_current_slide", None)
        if sid is None:
            raise RuntimeError("flow_step(): start_slide()를 먼저 호출하세요.")
        if primary:
            fill = self.c["accent_bg"]
            border = self.c["accent"]
            border_w = 0.5
        else:
            fill = self.c["surface"]
            border = self.c["border"]
            border_w = 0.4
        self._rect(sid, x, y, w, h, fill, border, border_w)
        pad_x = 16
        no = _uid()
        self._shape(sid, no, x + pad_x, y + 14, w - pad_x * 2, 16)
        self._text(no, str(num))
        self._style(no, 10, bold=True, color=self.c["accent"])
        ne = _uid()
        self._shape(sid, ne, x + pad_x, y + 36, w - pad_x * 2, 22)
        self._text(ne, name)
        self._style(ne, 10.5, bold=True, color=self.c["fg"])
        if desc:
            de = _uid()
            self._shape(sid, de, x + pad_x, y + 62, w - pad_x * 2, max(16, h - 76))
            self._text(de, desc)
            self._style(de, 9, color=self.c["dim"])

    def compare_pair(self, y, item, before, after, h=44):
        """비교 행 1개 — mk_compare_rows 시트 비율(140:240:240) 사용.

        좌(item) | 중(before, surface) | 우(after, accent border).
        여러 번 호출하면 세로로 쌓임 (y 좌표를 각자 지정).
        h는 28pt 이상이어야 안전.
        """
        sid = getattr(self, "_current_slide", None)
        if sid is None:
            raise RuntimeError("compare_pair(): start_slide()를 먼저 호출하세요.")
        h = max(28, h)
        x0, total_w = 40, 640
        item_w, before_w, after_w = 140, 240, 240
        gap = (total_w - item_w - before_w - after_w) // 2  # = 10
        v_pad = min(8, max(2, (h - 16) // 2))
        text_h = max(12, h - v_pad * 2)
        # 항목 (좌)
        io = _uid()
        self._shape(sid, io, x0, y + v_pad, item_w, text_h)
        self._text(io, item)
        self._style(io, 10.5, bold=True, color=self.c["fg"])
        # before (중) — surface fill, border weight 0.4
        bx = x0 + item_w + gap
        self._rect(sid, bx, y, before_w, h, self.c["surface"], self.c["border"], 0.4)
        bo = _uid()
        self._shape(sid, bo, bx + 12, y + v_pad, before_w - 24, text_h)
        self._text(bo, before)
        self._style(bo, 9, color=self.c["dim"])
        # after (우, accent_bg + 오렌지 border 0.5)
        ax = bx + before_w + gap
        self._rect(sid, ax, y, after_w, h, self.c["accent_bg"], self.c["accent"], 0.5)
        ao = _uid()
        self._shape(sid, ao, ax + 12, y + v_pad, after_w - 24, text_h)
        self._text(ao, after)
        self._style(ao, 9, color=self.c["fg"])

    def callout(self, text, sub=""):
        """단일 슬라이드 = 강조 메시지. 큰 글씨로 한 문장 + 부연 설명."""
        oid, idx = self._next()
        self._slide(oid, idx)
        self._bg(oid)
        # 좌측 오렌지 세로 바
        self._vline(oid, 60, 130, 145, weight=4)
        # 본문
        to = _uid()
        self._shape(oid, to, 90, 140, 590, 60)
        self._text(to, text)
        self._style(to, 22, bold=True, color=self.c["fg"])
        if sub:
            so = _uid()
            self._shape(oid, so, 90, 210, 590, 50)
            self._text(so, sub)
            self._style(so, 9, color=self.c["dim"])
        self._current_slide = oid
        return oid

    def section_divider(self, number, title, label="Section"):
        """챕터 구분 슬라이드 — 큰 오렌지 숫자 + 작은 라벨 + 큰 제목.

        의도: 발표를 큰 챕터(SECTION 01 / SECTION 02 등)로 나눌 때.
        일반 헤더 슬라이드(start_slide)와 시각 위계가 다름 — 큰 숫자 앵커로 휴지 구간 제공.

        좌표·사이즈 출처: 사용자 직접 수정 슬라이드 8 실측 카피 (V6.2 검증 완료).
            - "01" 박스: pos (50.90, 102.70) 시각 150x110 valign=TOP
                Proxima Nova 100pt bold accent
            - "Section" 라벨: pos (183.23, 163.23) 시각 200x16 valign=MIDDLE
                Proxima Nova 11.5pt dim
            - 제목: pos (183.23, 180.56) 시각 300x32 valign=MIDDLE
                Noto Sans 21pt fg

        주의 — Google Slides API 동작:
            createShape의 size는 항상 default 236.22로 강제되고, 코드 송신한
            size는 transform.scaleX/scaleY로 변환되어 적용됨.
            valign MIDDLE은 시각 박스 기준 가운데 정렬 (transform.x/y가 시각 박스 좌상단).

        Args:
            number: 챕터 번호. int 또는 string.
                - int: 자동 zero-padding (1 → "01")
                - string: 그대로 (예: "01", "Ⅰ")
            title: 큰 흰색 제목 (예: "바커 진행 방법")
            label: 숫자 옆 작은 dim 라벨 (default "Section")
        """
        oid, idx = self._next()
        self._slide(oid, idx)
        self._bg(oid)

        num_str = f"{number:02d}" if isinstance(number, int) else str(number)

        # 큰 오렌지 숫자 — Proxima Nova 100pt bold, valign TOP
        # 박스 사이즈 150x110 (텍스트 실측에 맞게 축소)
        n_oid = _uid()
        self._shape(oid, n_oid, 50.90, 102.70, 150, 110, valign="TOP")
        self._text(n_oid, num_str)
        self._style(n_oid, 100, bold=True, color=self.c["accent"], align="START",
                    font_family="Proxima Nova")

        # 작은 라벨 — Proxima Nova 11.5pt, valign MIDDLE
        # 사용자 직접 수정 좌표 카피 (transform.y는 시각 박스 좌상단)
        lbl_oid = _uid()
        self._shape(oid, lbl_oid, 183.23, 163.23, 200, 16, valign="MIDDLE")
        self._text(lbl_oid, label)
        self._style(lbl_oid, 11.5, color=self.c["dim"], font_family="Proxima Nova")

        # 큰 제목 — Noto Sans 21pt, valign MIDDLE
        # 사용자 직접 수정 좌표 카피
        ttl_oid = _uid()
        self._shape(oid, ttl_oid, 183.23, 180.56, 300, 32, valign="MIDDLE")
        self._text(ttl_oid, title)
        self._style(ttl_oid, 21, color=self.c["fg"], font_family="Noto Sans")

        self._current_slide = oid
        return oid

    def conclusion(self, metric, caption="", details=None, heading="", eyebrow=""):
        """결론 슬라이드 — mk_conclusion_detail 시트 양식 직접 재현.

        좌측: 큰 메트릭(56pt ORANGE) + 캡션(9pt dim)
        우측: 디테일 카드 4개 (라벨 + 본문 + sub-라벨)

        대부분의 덱은 결론 페이지가 필요 없다 — 명시적으로 호출할 때만 사용.

        Args:
            metric:   큰 글씨 — '96.4%' 또는 'QR 1종' 같은 핵심 메시지
            caption:  메트릭 아래 작은 한두 줄 설명 (**굵게** 마크업 가능)
            details:  [{"label": "관리", "body": "...", "sub": "선택사항"}, ...] 최대 4개
            heading:  슬라이드 타이틀 (선택)
            eyebrow:  타이틀 위 메타 (선택)
        """
        self.start_slide(heading=heading, eyebrow=eyebrow)
        sid = self._current_slide

        # 좌측 큰 메트릭 (56pt ORANGE bold)
        mo = _uid()
        self._shape(sid, mo, 36, 130, 290, 80)
        br = self._text_md(mo, metric)
        self._style(mo, 56, bold=True, color=self.c["accent"])
        self._apply_bold_ranges(mo, br)

        # 좌측 캡션 (V5.6 페르소나 합의: 9pt → 11pt 가독성 개선)
        if caption:
            co = _uid()
            self._shape(sid, co, 42, 215, 290, 50)
            br = self._text_md(co, caption)
            self._style(co, 11, color=self.c["dim"])
            self._apply_bold_ranges(co, br)

        # 우측 디테일 카드 4개 (시트 좌표: card 314×44, gap 8)
        # 시트 양식 좌우 2단 — 좌측 라벨, 우측 본문
        # 본문 박스 valign=MIDDLE 자동 적용으로 카드 안 세로 가운데
        for i, d in enumerate((details or [])[:4]):
            cy = 110 + i * (44 + 8)
            self._rect(sid, 370, cy, 314, 44,
                       self.c["surface"], self.c["border"], 0.4)
            # 좌측 라벨 (작은 ORANGE)
            if d.get("label"):
                lo = _uid()
                self._shape(sid, lo, 382, cy + 6, 80, 32)
                self._text(lo, str(d["label"]))
                self._style(lo, 8, bold=True, color=self.c["accent"])
            # 좌측 sub (라벨 아래 작은 dim) — 사용 시 라벨 위치 위로
            if d.get("sub"):
                so = _uid()
                self._shape(sid, so, 382, cy + 24, 80, 14)
                self._text(so, str(d["sub"]))
                self._style(so, 7, color=self.c["dim"])
            # 우측 본문 (메인 메시지) — 박스 h=32 카드 안 세로 가운데
            if d.get("body"):
                bo = _uid()
                self._shape(sid, bo, 470, cy + 6, 210, 32)
                br = self._text_md(bo, d["body"])
                self._style(bo, 9, color=self.c["fg"])
                self._apply_bold_ranges(bo, br)
        return sid

    def text(self, x, y, w, h, content, size=10.5, bold=False, color=None, align="START"):
        """자유 위치 텍스트박스 한 개. **굵게** 마크업 자동 인식.

        용도: 큰 헤더, 라벨, 자유 본문 등 카드/플로우 외 자유 배치 텍스트.
        """
        sid = getattr(self, "_current_slide", None)
        if sid is None:
            raise RuntimeError("text(): start_slide()를 먼저 호출하세요.")
        if color is None:
            color = self.c["fg"]
        oid = _uid()
        self._shape(sid, oid, x, y, w, h)
        br = self._text_md(oid, content)
        self._style(oid, size, bold=bold, color=color, align=align)
        self._apply_bold_ranges(oid, br)
        return oid

    def divider(self, x, y, w, orange=True):
        """수평 구분선. orange=True면 오렌지 헤더선 2pt, False면 dim 0.75pt (시트 표준)."""
        sid = getattr(self, "_current_slide", None)
        if sid is None:
            raise RuntimeError("divider(): start_slide()를 먼저 호출하세요.")
        if orange:
            self._hline(sid, x, y, w, weight=2, color=self.c["accent"])
        else:
            self._hline(sid, x, y, w, weight=0.75, color=self.c["dim"])

    # ── API 플러시 ────────────────────────────────────────────────

    def _validate(self):
        """V5.9 자동 검사 — flush 직전 reqs를 스캔해 룰 위반 검출.

        검사 항목:
          1. 콘텐츠 영역 초과 (y + h > 373, 캔버스 밖 또는 아래 32pt 여백 침범)
          2. 캔버스 우측 초과 (x + w > 720)
          3. 음수 좌표

        경고만 출력 (raise 안 함) — 빌드는 진행, 사용자가 결과로 판단.
        """
        warnings = []
        for r in self.reqs:
            create = r.get("createShape") or r.get("createLine")
            if not create:
                continue
            ep = create.get("elementProperties", {})
            tx = ep.get("transform", {})
            sz = ep.get("size", {})
            x = tx.get("translateX", 0) / 12700
            y = tx.get("translateY", 0) / 12700
            w = sz.get("width", {}).get("magnitude", 0) / 12700
            h = sz.get("height", {}).get("magnitude", 0) / 12700
            oid = create.get("objectId", "?")[:12]
            if x < 0 or y < 0:
                warnings.append(f"shape {oid}: 음수 좌표 (x={x:.0f}, y={y:.0f})")
            if x + w > 720:
                warnings.append(f"shape {oid}: 캔버스 우측 초과 (x+w={x+w:.0f} > 720)")
            if y + h > 405:
                warnings.append(f"shape {oid}: 캔버스 하단 초과 (y+h={y+h:.0f} > 405)")
            elif y + h > 373 + 0.5 and y < 373:  # 0.5 부동소수점 여유
                warnings.append(
                    f"shape {oid}: 콘텐츠 영역 침범 (y+h={y+h:.0f} > 373, 아래 32pt 여백 위반)"
                )
        if warnings:
            print(f"[V5.9 검사] 경고 {len(warnings)}개:")
            for w in warnings[:8]:
                print(f"  ⚠ {w}")
            if len(warnings) > 8:
                print(f"  ... +{len(warnings) - 8}개")
        return len(warnings)

    def flush(self):
        self._validate()
        ok = True
        for i in range(0, len(self.reqs), 50):
            chunk = self.reqs[i:i + 50]
            r = subprocess.run(
                ["gws", "slides", "presentations", "batchUpdate",
                 "--params", json.dumps({"presentationId": self.pid}),
                 "--json",   json.dumps({"requests": chunk})],
                capture_output=True, text=True,
            )
            if r.returncode != 0:
                out = "\n".join(x for x in [r.stdout, r.stderr] if x).strip()[:400]
                print(f"[오류] 청크 {i // 50 + 1}: {out}")
                ok = False
        self.reqs = []
        return ok

"""
spigen_models.py — shared slide/component spec models.

Preview HTML and Google Slides API renderers should consume the same
component payloads. This module defines those shared contracts.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DeckBrief:
    audience: str = ""
    purpose: str = ""
    theme: str = "light"
    default_mode: str = "operational_detail_report"
    detail_level: int = 8
    layout_variance: int = 3
    content_preservation_priority: str = "max"
    execution_clarity_priority: str = "max"
    locale: str = "ko-KR"
    source_kind: str = "user_input"
    ui_evidence: str = "text_only"

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "DeckBrief":
        return cls(
            audience=str(raw.get("audience", "")).strip(),
            purpose=str(raw.get("purpose", "")).strip(),
            theme=str(raw.get("theme", "light") or "light").strip(),
            default_mode=str(raw.get("default_mode", "operational_detail_report") or "operational_detail_report").strip(),
            detail_level=int(raw.get("detail_level", 8) or 8),
            layout_variance=int(raw.get("layout_variance", 3) or 3),
            content_preservation_priority=str(raw.get("content_preservation_priority", "max") or "max").strip(),
            execution_clarity_priority=str(raw.get("execution_clarity_priority", "max") or "max").strip(),
            locale=str(raw.get("locale", "ko-KR") or "ko-KR").strip(),
            source_kind=str(raw.get("source_kind", "user_input") or "user_input").strip(),
            ui_evidence=str(raw.get("ui_evidence", "text_only") or "text_only").strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audience": self.audience,
            "purpose": self.purpose,
            "theme": self.theme,
            "default_mode": self.default_mode,
            "detail_level": self.detail_level,
            "layout_variance": self.layout_variance,
            "content_preservation_priority": self.content_preservation_priority,
            "execution_clarity_priority": self.execution_clarity_priority,
            "locale": self.locale,
            "source_kind": self.source_kind,
            "ui_evidence": self.ui_evidence,
        }


@dataclass
class ComponentSpec:
    type: str
    props: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "ComponentSpec":
        return cls(type=str(raw.get("type", "")).strip(), props=dict(raw.get("props", {}) or {}))

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "props": dict(self.props)}


@dataclass
class SlideSpec:
    slide_id: str
    title: str
    components: List[ComponentSpec]
    eyebrow: str = ""
    label: str = ""
    page_no: Optional[int] = None
    audience: str = ""
    purpose: str = ""
    detail_mode: str = ""
    deck_mode: str = "operational_detail_report"
    detail_level: int = 8
    layout_variance: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "SlideSpec":
        components = [ComponentSpec.from_dict(item) for item in raw.get("components", [])]
        return cls(
            slide_id=str(raw.get("slide_id", "")).strip(),
            title=str(raw.get("title", "")).strip(),
            eyebrow=str(raw.get("eyebrow", "")).strip(),
            label=str(raw.get("label", "")).strip(),
            page_no=raw.get("page_no"),
            audience=str(raw.get("audience", "")).strip(),
            purpose=str(raw.get("purpose", "")).strip(),
            detail_mode=str(raw.get("detail_mode", "")).strip(),
            deck_mode=str(raw.get("deck_mode", "operational_detail_report") or "operational_detail_report").strip(),
            detail_level=int(raw.get("detail_level", 8) or 8),
            layout_variance=int(raw.get("layout_variance", 3) or 3),
            metadata=dict(raw.get("metadata", {}) or {}),
            components=components,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slide_id": self.slide_id,
            "title": self.title,
            "eyebrow": self.eyebrow,
            "label": self.label,
            "page_no": self.page_no,
            "audience": self.audience,
            "purpose": self.purpose,
            "detail_mode": self.detail_mode,
            "deck_mode": self.deck_mode,
            "detail_level": self.detail_level,
            "layout_variance": self.layout_variance,
            "metadata": dict(self.metadata),
            "components": [component.to_dict() for component in self.components],
        }


@dataclass
class SelectionInput:
    content_type: str = ""
    item_count: int = 0
    has_comparison: bool = False
    is_process: bool = False
    has_status: bool = False
    is_bilateral: bool = False
    is_kpi: bool = False
    audience: str = ""
    purpose: str = ""
    detail_mode: str = ""
    deck_mode: str = "operational_detail_report"
    freedom_level: str = "high"
    detail_level: int = 8
    layout_variance: int = 3
    content_preservation_priority: str = "max"
    execution_clarity_priority: str = "max"
    diagram_kind: str = ""
    message_shape: str = ""

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "SelectionInput":
        return cls(
            content_type=str(raw.get("content_type", "")).strip(),
            item_count=int(raw.get("item_count", 0) or 0),
            has_comparison=bool(raw.get("has_comparison", False)),
            is_process=bool(raw.get("is_process", False)),
            has_status=bool(raw.get("has_status", False)),
            is_bilateral=bool(raw.get("is_bilateral", False)),
            is_kpi=bool(raw.get("is_kpi", False)),
            audience=str(raw.get("audience", "")).strip(),
            purpose=str(raw.get("purpose", "")).strip(),
            detail_mode=str(raw.get("detail_mode", "")).strip(),
            deck_mode=str(raw.get("deck_mode", "operational_detail_report") or "operational_detail_report").strip(),
            freedom_level=str(raw.get("freedom_level", "high") or "high").strip(),
            detail_level=int(raw.get("detail_level", 8) or 8),
            layout_variance=int(raw.get("layout_variance", 3) or 3),
            content_preservation_priority=str(raw.get("content_preservation_priority", "max") or "max").strip(),
            execution_clarity_priority=str(raw.get("execution_clarity_priority", "max") or "max").strip(),
            diagram_kind=str(raw.get("diagram_kind", "")).strip(),
            message_shape=str(raw.get("message_shape", "")).strip(),
        )


@dataclass
class SelectionResult:
    component_name: str
    function_name: str
    rationale: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "component_name": self.component_name,
            "function_name": self.function_name,
            "rationale": self.rationale,
        }

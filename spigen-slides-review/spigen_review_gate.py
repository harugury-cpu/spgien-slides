#!/usr/bin/env python3
"""
spigen_review_gate.py

검수 산출물이 모두 모이기 전에는 완료 보고를 막는 게이트.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
POSTGEN = os.path.join(HERE, "spigen_postgen_hook.py")
GWS = shutil.which("gws") or ""


def root_for(presentation_id):
    return f"/tmp/spigen_review_{presentation_id}"


def manifest_path(presentation_id):
    return os.path.join(root_for(presentation_id), "manifest.json")


def load_manifest(presentation_id):
    path = manifest_path(presentation_id)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_manifest(presentation_id, data):
    path = manifest_path(presentation_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json_from_stdout(text):
    idx = text.find("{")
    if idx >= 0:
        text = text[idx:]
    return json.loads(text)


def _norm_text(shape):
    out = []
    text = shape.get("text", {})
    for te in text.get("textElements", []):
        run = te.get("textRun", {})
        if run.get("content"):
            out.append(run.get("content"))
    return "".join(out)


def _norm_page_element(el):
    norm = {
        "objectId": el.get("objectId"),
        "transform": el.get("transform"),
        "size": el.get("size"),
    }
    if "shape" in el:
        shape = el.get("shape", {})
        norm["shape"] = {
            "shapeType": shape.get("shapeType"),
            "text": _norm_text(shape),
        }
    if "table" in el:
        norm["table"] = el.get("table")
    if "image" in el:
        norm["image"] = {
            "hasImage": True,
        }
    return norm


def normalize_presentation_for_hash(data):
    slides = []
    for slide in data.get("slides", []):
        slides.append({
            "objectId": slide.get("objectId"),
            "pageElements": [_norm_page_element(el) for el in slide.get("pageElements", [])],
        })
    return {
        "title": data.get("title"),
        "slides": slides,
    }


def current_presentation_hash(presentation_id):
    if not GWS:
        raise RuntimeError("gws 바이너리를 찾을 수 없습니다.")
    res = subprocess.run(
        [GWS, "slides", "presentations", "get",
         "--params", json.dumps({"presentationId": presentation_id})],
        capture_output=True, text=True,
    )
    try:
        data = load_json_from_stdout(res.stdout)
    except json.JSONDecodeError:
        if res.returncode != 0:
            raise RuntimeError(res.stderr.strip() or res.stdout.strip())
        raise
    normalized = normalize_presentation_for_hash(data)
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def cmd_init(args):
    cmd = [
        sys.executable, POSTGEN, args.presentation_id,
        "--audience", args.audience,
        "--purpose", args.purpose,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(res.stdout)
    sys.stderr.write(res.stderr)
    return res.returncode


def cmd_record(args):
    manifest = load_manifest(args.presentation_id)
    report = manifest["reports"][args.reviewer]
    report["status"] = args.status
    report["summary"] = args.summary
    report["path"] = args.report
    save_manifest(args.presentation_id, manifest)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args):
    manifest = load_manifest(args.presentation_id)
    report_root = root_for(args.presentation_id)
    reports = manifest.get("reports", {})
    thumbs_dir = os.path.join(report_root, "thumbnails")
    verify_ok = bool(manifest.get("verify_pass"))
    thumbs_ok = os.path.isdir(thumbs_dir) and bool(os.listdir(thumbs_dir))
    planner_ok = reports.get("planner", {}).get("status") == "pass"
    designer_ok = reports.get("designer", {}).get("status") == "pass"
    audience_ok = reports.get("audience", {}).get("status") in {"pass", "feedback"}
    saved_hash = manifest.get("presentation_hash")
    current_hash = current_presentation_hash(args.presentation_id)
    content_stable = (saved_hash == current_hash)

    summary = {
        "presentation_id": args.presentation_id,
        "verify_pass": verify_ok,
        "thumbnails_ready": thumbs_ok,
        "planner_pass": planner_ok,
        "designer_pass": designer_ok,
        "audience_ready": audience_ok,
        "content_stable": content_stable,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not args.require_pass:
        return 0
    return 0 if all(summary.values()) else 1


def cmd_cleanup(args):
    root = root_for(args.presentation_id)
    if not os.path.exists(root):
        print(root)
        return 0

    if not args.force:
        manifest = load_manifest(args.presentation_id)
        reports = manifest.get("reports", {})
        verify_ok = bool(manifest.get("verify_pass"))
        thumbs_ok = os.path.isdir(os.path.join(root, "thumbnails")) and bool(os.listdir(os.path.join(root, "thumbnails")))
        planner_ok = reports.get("planner", {}).get("status") == "pass"
        designer_ok = reports.get("designer", {}).get("status") == "pass"
        audience_ok = reports.get("audience", {}).get("status") in {"pass", "feedback"}
        if not all([verify_ok, thumbs_ok, planner_ok, designer_ok, audience_ok]):
            print(json.dumps({
                "presentation_id": args.presentation_id,
                "cleanup": "blocked",
                "reason": "review not fully passed",
            }, ensure_ascii=False, indent=2))
            return 1

    shutil.rmtree(root, ignore_errors=True)
    print(json.dumps({
        "presentation_id": args.presentation_id,
        "cleanup": "done",
    }, ensure_ascii=False, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("presentation_id")
    p_init.add_argument("--audience", default="")
    p_init.add_argument("--purpose", default="")
    p_init.set_defaults(func=cmd_init)

    p_record = sub.add_parser("record")
    p_record.add_argument("presentation_id")
    p_record.add_argument("--reviewer", choices=["planner", "designer", "audience"], required=True)
    p_record.add_argument("--status", choices=["pass", "fail", "feedback"], required=True)
    p_record.add_argument("--report", required=True)
    p_record.add_argument("--summary", default="")
    p_record.set_defaults(func=cmd_record)

    p_status = sub.add_parser("status")
    p_status.add_argument("presentation_id")
    p_status.add_argument("--require-pass", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_cleanup = sub.add_parser("cleanup")
    p_cleanup.add_argument("presentation_id")
    p_cleanup.add_argument("--force", action="store_true")
    p_cleanup.set_defaults(func=cmd_cleanup)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()

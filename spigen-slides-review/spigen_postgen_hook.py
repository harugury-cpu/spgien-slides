#!/usr/bin/env python3
"""
spigen_postgen_hook.py

빌드 직후 디자이너/검수용 아티팩트를 만든다.
- presentation.json 저장
- spigen_verify.py 실행 결과 저장
- 슬라이드 썸네일 PNG 저장
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request


GWS = shutil.which("gws") or ""
HERE = os.path.dirname(os.path.abspath(__file__))
VERIFY = os.path.join(HERE, "spigen_verify.py")


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def load_json_from_stdout(text):
    idx = text.find("{")
    if idx >= 0:
        text = text[idx:]
    return json.loads(text)


def parse_gws_response(res):
    stdout = (res.stdout or "").strip()
    if stdout:
        try:
            return load_json_from_stdout(stdout)
        except json.JSONDecodeError:
            pass
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or stdout or "gws command failed")
    return None


def review_root(presentation_id):
    return f"/tmp/spigen_review_{presentation_id}"


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def get_presentation(presentation_id):
    cmd = [
        GWS, "slides", "presentations", "get",
        "--params", json.dumps({"presentationId": presentation_id}),
    ]
    res = run(cmd)
    data = parse_gws_response(res)
    if not isinstance(data, dict):
        raise RuntimeError("presentation get 응답 파싱 실패")
    return data


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


def presentation_hash(data):
    normalized = normalize_presentation_for_hash(data)
    raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run_verify(presentation_id, out_path):
    res = run([sys.executable, VERIFY, presentation_id])
    with open(out_path, "w", encoding="utf-8") as f:
        f.write((res.stdout or "").strip())
        if res.stderr:
            f.write("\n\n[stderr]\n")
            f.write(res.stderr.strip())
            f.write("\n")
    return res.returncode == 0


def download(url, out_path):
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = resp.read()
    with open(out_path, "wb") as f:
        f.write(data)


def create_thumbnails(presentation_id, presentation, thumb_dir):
    ensure_dir(thumb_dir)
    slides = presentation.get("slides", [])
    created = []
    for idx, slide in enumerate(slides, start=1):
        page_id = slide.get("objectId")
        if not page_id:
            continue
        params = {
            "presentationId": presentation_id,
            "pageObjectId": page_id,
        }
        res = run([
            GWS, "slides", "presentations", "pages", "getThumbnail",
            "--params", json.dumps(params),
        ])
        payload = parse_gws_response(res)
        if not isinstance(payload, dict):
            raise RuntimeError(f"thumbnail 응답 파싱 실패: slide {idx}")
        url = payload.get("contentUrl")
        if not url:
            raise RuntimeError(f"thumbnail URL 없음: slide {idx}")
        out_path = os.path.join(thumb_dir, f"slide_{idx}.png")
        download(url, out_path)
        created.append(out_path)
    return created


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("presentation_id")
    parser.add_argument("--audience", default="")
    parser.add_argument("--purpose", default="")
    args = parser.parse_args()

    if not GWS:
        raise SystemExit("gws 바이너리를 찾을 수 없습니다.")

    root = review_root(args.presentation_id)
    reports_dir = os.path.join(root, "reports")
    thumbs_dir = os.path.join(root, "thumbnails")
    ensure_dir(root)
    ensure_dir(reports_dir)

    presentation = get_presentation(args.presentation_id)
    save_json(os.path.join(root, "presentation.json"), presentation)
    verify_ok = run_verify(args.presentation_id, os.path.join(root, "verify.txt"))
    thumbs = create_thumbnails(args.presentation_id, presentation, thumbs_dir)

    manifest = {
        "presentation_id": args.presentation_id,
        "audience": args.audience,
        "purpose": args.purpose,
        "slide_count": len(presentation.get("slides", [])),
        "presentation_hash": presentation_hash(presentation),
        "verify_pass": verify_ok,
        "thumbnail_count": len(thumbs),
        "reports": {
            "planner": {"path": os.path.join(reports_dir, "planner.md"), "status": "pending"},
            "designer": {"path": os.path.join(reports_dir, "designer.md"), "status": "pending"},
            "audience": {"path": os.path.join(reports_dir, "audience.md"), "status": "pending"},
        },
    }
    save_json(os.path.join(root, "manifest.json"), manifest)
    print(root)


if __name__ == "__main__":
    main()

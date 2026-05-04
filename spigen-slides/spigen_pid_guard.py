#!/usr/bin/env python3
"""
spigen_pid_guard.py

spigen-slides 수정 작업에서 PRESENTATION_ID가 불필요하게 바뀌는 것을 막는다.
"""

import argparse
import json
import os
import sys


def pid_cache_path(name):
    return f"/tmp/spigen_pid_{name}.json"


def guard_path(name, theme):
    return f"/tmp/spigen_pid_guard_{name}_{theme}.json"


def load_pid(name, theme):
    path = pid_cache_path(name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    return data.get(theme)


def cmd_expect_stable(args):
    before = load_pid(args.build_name, args.theme)
    payload = {
        "build_name": args.build_name,
        "theme": args.theme,
        "before_pid": before,
    }
    with open(guard_path(args.build_name, args.theme), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_assert_stable(args):
    path = guard_path(args.build_name, args.theme)
    if not os.path.exists(path):
        print("guard file not found", file=sys.stderr)
        return 1

    with open(path, encoding="utf-8") as f:
        payload = json.load(f)

    before = payload.get("before_pid")
    after = load_pid(args.build_name, args.theme)
    result = {
        "build_name": args.build_name,
        "theme": args.theme,
        "before_pid": before,
        "after_pid": after,
    }

    if before and after and before != after and not args.allow_new:
        result["status"] = "fail"
        result["reason"] = "presentation_id_changed"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    result["status"] = "ok"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("expect-stable")
    p1.add_argument("build_name")
    p1.add_argument("theme")
    p1.set_defaults(func=cmd_expect_stable)

    p2 = sub.add_parser("assert-stable")
    p2.add_argument("build_name")
    p2.add_argument("theme")
    p2.add_argument("--allow-new", action="store_true")
    p2.set_defaults(func=cmd_assert_stable)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Prepare an E4B scene from an owner-created GitHub Issue or workflow_dispatch.

Scene and results are public in this repository. Never submit real secrets.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import re

MAX_INPUT_BYTES = 12288
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"github_pat_[A-Za-z0-9_]{16,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
]


def validate_scene(scene: object) -> dict:
    if not isinstance(scene, dict) or not isinstance(scene.get("characters"), list):
        raise ValueError("Scene must be a JSON object with a characters array")
    serialized = json.dumps(scene, ensure_ascii=False)
    if len(serialized.encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValueError("Scene too large: split into smaller scenes")
    if any(not isinstance(c, dict) for c in scene["characters"]):
        raise ValueError("Each character must be a JSON object")
    if any(pattern.search(serialized) for pattern in SECRET_PATTERNS):
        raise ValueError("Possible credential in scene. Refusing to transmit.")
    return scene


def parse_scene(raw: str) -> dict:
    if not raw:
        raise ValueError("Scene JSON cannot be empty")
    return validate_scene(json.loads(raw))


def decode_input(value: str) -> dict:
    if len(value) > 18000:
        raise ValueError("Base64 input too large")
    try:
        decoded = base64.b64decode(value, validate=True)
    except binascii.Error as exc:
        raise ValueError("Invalid Base64") from exc
    if len(decoded) > MAX_INPUT_BYTES:
        raise ValueError("Scene too large: split into smaller scenes")
    return parse_scene(decoded.decode("utf-8"))


def validate_max_tokens(value: object) -> int:
    if type(value) is not int or not 64 <= value <= 1000:
        raise ValueError("max_tokens must be an integer from 64 to 1000")
    return value


def issue_scene_request(payload: dict, sample: Path) -> tuple[dict, int]:
    issue = payload.get("issue") or {}
    repository = payload.get("repository") or {}
    author = (issue.get("user") or {}).get("login", "")
    owner = (repository.get("owner") or {}).get("login", "")
    if not author or not owner or author.lower() != owner.lower():
        raise ValueError("Only repository owner can request an E4B Issue job")
    title = issue.get("title") or ""
    if title.startswith("[E4B DEMO]"):
        print("Using committed public demonstration scene.")
        return parse_scene(sample.read_text(encoding="utf-8")), 720
    if not title.startswith("[E4B SCENE]"):
        raise ValueError("Unknown E4B Issue request")
    body = issue.get("body") or ""
    if len(body.encode("utf-8")) > MAX_INPUT_BYTES + 512:
        raise ValueError("Request too large")
    try:
        obj = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError("Issue body must be raw JSON, without Markdown fences") from exc
    if not isinstance(obj, dict) or "scene" not in obj:
        raise ValueError("Issue body must include a scene object")
    scene = validate_scene(obj["scene"])
    max_tokens = validate_max_tokens(obj.get("max_tokens", 720))
    print("Using owner-submitted PUBLIC scene from Issue.")
    return scene, max_tokens


def prepare_scene(
    source: Path, destination: Path, encoded_input: str,
    event_path: Path | None = None, max_tokens: int = 720,
    token_destination: Path | None = None,
) -> int:
    if event_path is not None:
        scene, requested_tokens = issue_scene_request(
            json.loads(event_path.read_text(encoding="utf-8")), source
        )
    elif encoded_input.strip():
        scene = decode_input(encoded_input.strip())
        requested_tokens = validate_max_tokens(max_tokens)
        print("Using PUBLIC workflow_dispatch scene.")
    else:
        scene = parse_scene(source.read_text(encoding="utf-8"))
        requested_tokens = validate_max_tokens(max_tokens)
        print("Using repository sample scene.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(scene, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if token_destination is not None:
        token_destination.parent.mkdir(parents=True, exist_ok=True)
        token_destination.write_text(str(requested_tokens) + "\n", encoding="ascii")
    return requested_tokens


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default="samples/test-scene.json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-tokens-file", default="input/max_tokens.txt")
    args = parser.parse_args()
    issue_event = os.environ.get("GITHUB_EVENT_NAME") == "issues"
    event_path = Path(os.environ["GITHUB_EVENT_PATH"]) if issue_event else None
    dispatch_tokens = int(os.environ.get("DISPATCH_MAX_TOKENS") or "720")
    prepare_scene(
        Path(args.sample), Path(args.output), os.environ.get("SCENE_BASE64", ""),
        event_path=event_path, max_tokens=dispatch_tokens,
        token_destination=Path(args.max_tokens_file),
    )


if __name__ == "__main__":
    main()

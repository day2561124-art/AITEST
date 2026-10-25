#!/usr/bin/env python3
"""Prepare a scene, rejecting custom inputs in a public repository.

Base64 and GitHub workflow inputs are never a confidentiality mechanism.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
from pathlib import Path

MAX_INPUT_BYTES = 32768


def parse_scene(raw: str) -> dict:
    if not raw:
        raise ValueError("Scene JSON cannot be empty")
    scene = json.loads(raw)
    if not isinstance(scene, dict) or not isinstance(scene.get("characters"), list):
        raise ValueError("Scene must be a JSON object with a characters list")
    return scene


def decode_input(value: str) -> dict:
    if len(value) > 48000:
        raise ValueError("Base64 input too large")
    try:
        decoded = base64.b64decode(value, validate=True)
    except binascii.Error as exc:
        raise ValueError("Invalid Base64") from exc
    if len(decoded) > MAX_INPUT_BYTES:
        raise ValueError("Scene exceeds 32 KiB limit")
    return parse_scene(decoded.decode("utf-8"))


def prepare_scene(source: Path, destination: Path, encoded_input: str, private_repo: bool = False) -> None:
    if encoded_input.strip() and not private_repo:
        raise ValueError("Refusing custom scene in PUBLIC repository. Base64 is NOT encryption.")
    if encoded_input.strip():
        scene = decode_input(encoded_input.strip())
        print("Using custom scene in private repository; avoid logging scene data.")
    else:
        scene = parse_scene(source.read_text(encoding="utf-8"))
        print("Using repository sample scene.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(scene, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default="samples/test-scene.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    private_repo = os.environ.get("REPOSITORY_PRIVATE", "").strip().lower() == "true"
    prepare_scene(Path(args.sample), Path(args.output), os.environ.get("SCENE_BASE64", ""), private_repo=private_repo)


if __name__ == "__main__":
    main()

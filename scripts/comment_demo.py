#!/usr/bin/env python3
"""Publish publicly visible E4B scene results back to their owner-created Issue.

Never use this mechanism for credentials or secret personal information.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
from urllib import request, error

REPO_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")
MAX_SCENE_CHARS = 12000


def render_comment(scene: str, metrics: dict, repo: str, run_id: int) -> str:
    if not REPO_PATTERN.fullmatch(repo):
        raise ValueError("Invalid repository full name")
    if run_id <= 0:
        raise ValueError("Run ID must be positive")
    scene = scene.strip()
    if not scene or len(scene) > MAX_SCENE_CHARS:
        raise ValueError("Public sample output missing or too long")
    duration = metrics.get("generation_seconds", "unknown")
    speed = metrics.get("end_to_end_tokens_per_second", "unknown")
    return (
        "<!-- e4b-public-demo-result -->\n"
        "### E4B 場景｜生成結果\n\n"
        "**提醒：本留言公開可見，場景與生成內容不是私密資料。**\n\n"
        + scene
        + "\n\n---\n"
        + f"生成耗時：{duration} 秒；速度：約 {speed} tokens/s。\n\n"
        + f"執行紀錄：https://github.com/{repo}/actions/runs/{run_id}\n"
    )


def post_comment(token: str, repo: str, issue_number: int, body: str) -> None:
    if not token:
        raise ValueError("Missing GITHUB_TOKEN")
    if not REPO_PATTERN.fullmatch(repo) or issue_number <= 0:
        raise ValueError("Invalid GitHub issue target")
    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    payload = json.dumps({"body": body}, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url, data=payload, method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "e4b-public-demo",
        },
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            if resp.status != 201:
                raise RuntimeError(f"GitHub comment returned HTTP {resp.status}")
    except error.HTTPError as exc:
        raise RuntimeError(f"GitHub comment failed: HTTP {exc.code}") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()
    scene = args.scene.read_text(encoding="utf-8")
    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    comment = render_comment(scene, metrics, args.repo, args.run_id)
    post_comment(os.environ.get("GITHUB_TOKEN", ""), args.repo, args.issue_number, comment)
    print("Published E4B output to owner-created Issue.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Optional stand-alone GitHub Actions API bridge for E4B.

This is for use in an authorized cloud worker, app, or CLI. Running this script on
someone's Windows machine does NOT make the ChatGPT conversation able to run it.

Custom scenes are allowed in a public repo only when public visibility is acceptable.
Never send credentials, private keys, or sensitive personal data.
"""
from __future__ import annotations

import argparse
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import time
from urllib import request, error, parse
from uuid import uuid4
import zipfile

API = "https://api.github.com"
WORKFLOW = "e4b-cpu-test.yml"
ALLOWED_ARTIFACT_FILES = {"scene.md", "metrics.json", "download_seconds.txt", "model_cache_hit.txt", "model_load_seconds.txt", "model_start_epoch.txt"}


class SafeRedirect(request.HTTPRedirectHandler):
    """Never forward the GitHub bearer token to signed artifact blob URLs."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected and parse.urlparse(newurl).hostname != parse.urlparse(req.full_url).hostname:
            redirected.remove_header("Authorization")
            redirected.remove_unredirected_header("Authorization")
        return redirected


class GitHub:
    def __init__(self, token: str):
        if not token:
            raise ValueError("Set GH_TOKEN or GITHUB_TOKEN in the environment. Do not put tokens in source code.")
        self.token = token
        self.opener = request.build_opener(SafeRedirect())

    def call(self, method: str, path: str, payload: dict | None = None, binary: bool = False):
        url = API + path
        raw = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "e4b-github-bridge",
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"
        req = request.Request(url, data=raw, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=60) as resp:
                blob = resp.read()
                if binary:
                    return blob
                return json.loads(blob.decode("utf-8")) if blob else {}
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"GitHub API {exc.code} on {method} {path}: {message}") from exc


def extract_artifact_safely(data: bytes, dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    exported = []
    with zipfile.ZipFile(BytesIO(data)) as archive:
        for member in archive.infolist():
            if member.filename not in ALLOWED_ARTIFACT_FILES or member.file_size > 1024 * 1024:
                continue
            (dest / member.filename).write_bytes(archive.read(member))
            exported.append(member.filename)
    return exported


def run_bridge(args: argparse.Namespace) -> int:
    gh = GitHub(os.environ.get("GH_TOKEN", "") or os.environ.get("GITHUB_TOKEN", ""))
    repo = gh.call("GET", f"/repos/{args.repo}")
    scene_path = Path(args.scene) if args.scene else None
    scene_b64 = ""
    if scene_path is not None:
        raw = scene_path.read_bytes()
        if len(raw) > 12288:
            raise ValueError("Scene exceeds 12 KiB. Split into smaller scenes.")
        scene = json.loads(raw.decode("utf-8"))
        if not isinstance(scene, dict) or not isinstance(scene.get("characters"), list):
            raise ValueError("Scene must contain a characters array")
        scene_b64 = base64.b64encode(raw).decode("ascii")
    request_id = uuid4().hex[:16]
    print(f"Dispatching E4B job for {args.repo}; request_id={request_id}", flush=True)
    gh.call("POST", f"/repos/{args.repo}/actions/workflows/{WORKFLOW}/dispatches", {
        "ref": repo.get("default_branch", "main"),
        "inputs": {"request_id": request_id, "scene_base64": scene_b64, "max_tokens": str(args.max_tokens)},
    })
    deadline = time.monotonic() + args.timeout
    run_id = None
    while time.monotonic() < deadline:
        if run_id is None:
            batch = gh.call("GET", f"/repos/{args.repo}/actions/workflows/{WORKFLOW}/runs?event=workflow_dispatch&per_page=25")
            for r in batch.get("workflow_runs", []):
                if request_id in r.get("display_title", ""):
                    run_id = r["id"]
                    print(f"Matched run #{r['run_number']}: {r.get('html_url')}", flush=True)
                    break
        else:
            run = gh.call("GET", f"/repos/{args.repo}/actions/runs/{run_id}")
            if run.get("status") == "completed":
                print(f"Run completed: {run.get('conclusion')}", flush=True)
                artifacts = gh.call("GET", f"/repos/{args.repo}/actions/runs/{run_id}/artifacts")
                archive = next((a for a in artifacts.get("artifacts", []) if a["name"] == "e4b-cpu-result" and not a.get("expired")), None)
                if archive:
                    zipped = gh.call("GET", f"/repos/{args.repo}/actions/artifacts/{archive['id']}/zip", binary=True)
                    extracted = extract_artifact_safely(zipped, Path(args.out))
                    print(f"Saved {', '.join(extracted) or 'no matching files'} under {args.out}")
                return 0 if run.get("conclusion") == "success" else 1
        time.sleep(args.poll_seconds)
    raise TimeoutError("GitHub workflow not completed before timeout; check Actions UI")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="day2561124-art/AITEST")
    parser.add_argument("--scene", help="JSON scene file. In PUBLIC repo, scene and generated output are public.")
    parser.add_argument("--out", default="output-github")
    parser.add_argument("--max-tokens", type=int, default=720)
    parser.add_argument("--timeout", type=int, default=5400)
    parser.add_argument("--poll-seconds", type=int, default=15)
    args = parser.parse_args()
    if not 64 <= args.max_tokens <= 1000:
        parser.error("--max-tokens must be from 64 to 1000")
    raise SystemExit(run_bridge(args))


if __name__ == "__main__":
    main()

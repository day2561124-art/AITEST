#!/usr/bin/env python3
"""Generate a single scene through either a local llama.cpp server or Ollama."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib import error, request

SYSTEM = (
    "你是負責角色演出與場景敘述的繁體中文劇情寫手。"
    "你只能依照提供的場景安排、人物性格、記憶及知情範圍，"
    "寫出自然的人物台詞、對話反應、動作和旁白。"
    "你不能更改劇情大方向、替角色發明記憶、亂加事件或破壞角色能力。"
    "保留原作角色的智力、觀察力、推理及戰鬥水準，不得為了配合劇情而降智。"
    "不要替等待玩家發言的主角擅自決定台詞或重要行動。"
    "角色可以依本人的動機自由反應，事件因果必須完整。"
    "避免公式化台詞、說教、重複解釋與抽象謎語。"
    "直接輸出完成的正文，不要標題、解釋、分析、選項或事後評語."
)


def build_messages(scene: dict) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "請依以下場景設定撰寫人物對話及旁白：\n" + json.dumps(scene, ensure_ascii=False, indent=2)},
    ]


def post_json(endpoint: str, data: dict, timeout: int = 1200) -> dict:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = request.Request(endpoint, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API HTTP {exc.code}: {response_body[:1200]}") from exc


def generate(provider: str, endpoint: str, model: str, messages: list[dict[str, str]], max_tokens: int) -> tuple[str, dict]:
    if provider == "llama.cpp":
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 1.0,
            "top_p": 0.95,
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": False, "conversational_mode": False},
        }
        result = post_json(endpoint, payload)
        output = result["choices"][0]["message"].get("content") or ""
        usage = dict(result.get("usage", {}))
        usage["finish_reason"] = result["choices"][0].get("finish_reason")
    elif provider == "ollama":
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"num_predict": max_tokens, "temperature": 1.0, "top_p": 0.95, "num_ctx": 2048},
        }
        result = post_json(endpoint, payload)
        output = result["message"].get("content") or ""
        usage = {
            "prompt_tokens": result.get("prompt_eval_count"),
            "completion_tokens": result.get("eval_count"),
        }
    else:
        raise ValueError(f"Unknown provider: {provider}")
    if not output.strip():
        raise RuntimeError("Model returned no visible text. Check chat template / reasoning settings.")
    return output.strip(), usage


def run(args: argparse.Namespace) -> dict:
    scene = json.loads(Path(args.scene).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    output, usage = generate(args.provider, args.endpoint, args.model, build_messages(scene), args.max_tokens)
    elapsed = round(time.perf_counter() - start, 2)
    result_file = out / "scene.md"
    result_file.write_text(output + "\n", encoding="utf-8")
    completion = usage.get("completion_tokens")
    tokens_per_second = round(completion / elapsed, 2) if isinstance(completion, int) and elapsed > 0 else None
    metrics = {
        "provider": args.provider,
        "model": args.model,
        "generation_seconds": elapsed,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": completion,
        "end_to_end_tokens_per_second": tokens_per_second,
        "characters_generated": len(output),
        "finish_reason": usage.get("finish_reason"),
        "note": "速度包含提示處理與生成耗時，不是純解碼速度。",
    }
    (out / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(output)} characters in {elapsed} seconds, approx {tokens_per_second} total tokens/s")
    print(f"Text saved to: {result_file}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["llama.cpp", "ollama"], default="llama.cpp")
    parser.add_argument("--endpoint", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--scene", default="samples/test-scene.json")
    parser.add_argument("--out", default="output")
    parser.add_argument("--max-tokens", type=int, default=720)
    args = parser.parse_args()
    if not args.endpoint:
        args.endpoint = "http://127.0.0.1:8080/v1/chat/completions" if args.provider == "llama.cpp" else "http://127.0.0.1:11434/api/chat"
    if not args.model:
        args.model = "nemotron-bolt" if args.provider == "llama.cpp" else "nemotron-3.5-bolt:e4b"
    run(args)


if __name__ == "__main__":
    main()

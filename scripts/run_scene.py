#!/usr/bin/env python3
"""Generate a single scene through either a local llama.cpp server or Ollama."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib import error, request

SYSTEM = (
    "你正在參與即時角色扮演，不是小說寫手，也不是旁觀解說員。"
    "你的任務是扮演場景中的所有非玩家角色，讓每個人依照自己的性格、記憶、"
    "知情範圍、目標與彼此關係，當場說話、回應和採取行動。"
    "GPT只提供世界設定、既有事實與劇情事件節點，不負責替你寫人物台詞或旁白。"
    "事件節點不是文章大綱；不要逐條複述，要透過角色實際互動讓事情發生。"
    "直接呈現現場：人物實際說出的台詞、動作、反應，以及必要且具體的環境旁白。"
    "不要用旁白解釋人物性格或心理，不要替事件下結論、總結意義、預告劇情或寫作者評語。"
    "每個角色都要保持原作的智力、觀察力、推理、技術與戰鬥水準，不能憑空知道情報。"
    "角色能依自身動機自然反應，但不能改寫已確定的事件因果、能力和人物記憶。"
    "絕對不要替玩家控制的主角發言、移動、做決定或擅自同步情報。"
    "若輪到玩家回應，就停在等待玩家行動的自然時刻，不必強迫每一幕都有結局。"
    "使用繁體中文；台詞像真人交談，依不同角色調整語氣，避免官腔、套話和刻意修辭。"
    "只輸出角色扮演現場的對話、動作與必要旁白，不要標題、分析、選項或事後解說。"
)

def build_messages(scene: dict) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "請直接扮演這個場景裡的非玩家角色，從眼前狀況開始自然互動，呈現台詞、動作與必要旁白。以下是導演提供的場景和事實限制，不是要你改寫成小說：\n" + json.dumps(scene, ensure_ascii=False, indent=2)},
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

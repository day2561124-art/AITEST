#!/usr/bin/env python3
"""Wait until llama.cpp server has loaded its GGUF model."""
import argparse
import time
from pathlib import Path
from urllib.request import urlopen


def wait(url: str, timeout: int, interval: int = 5) -> int:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            with urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return int(time.monotonic() - start)
        except Exception:
            pass
        time.sleep(interval)
    raise TimeoutError(f"Model was not ready within {timeout}s: {url}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--start-file")
    parser.add_argument("--out", default="output/model_load_seconds.txt")
    args = parser.parse_args()
    seconds = wait(args.url, args.timeout)
    if args.start_file:
        seconds = max(0, int(time.time()) - int(Path(args.start_file).read_text().strip()))
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(str(seconds) + "\n", encoding="utf-8")
    print(f"Model ready. Load time: ~{seconds}s")


if __name__ == "__main__":
    main()

import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from types import SimpleNamespace

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_scene.py"
spec = importlib.util.spec_from_file_location("run_scene", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SceneTests(TestCase):
    def test_prompt_contains_constraints(self):
        scene = {"characters": [{"name": "甲"}], "plot_beats": ["練習"]}
        messages = mod.build_messages(scene)
        self.assertIn("人物台詞", messages[0]["content"])
        self.assertIn("甲", messages[1]["content"])

    def test_llama_response_and_output(self):
        args = SimpleNamespace(scene=None, out=None, provider="llama.cpp", endpoint="http://127.0.0.1:8080", model="nemotron-bolt", max_tokens=64)
        with TemporaryDirectory() as temp:
            args.scene = str(Path(temp) / "scene.json")
            args.out = str(Path(temp) / "result")
            Path(args.scene).write_text(json.dumps({"setting": "走廊"}), encoding="utf-8")
            with patch.object(mod, "post_json", return_value={"choices": [{"message": {"content": "阿明：走吧。"}}], "usage": {"completion_tokens": 8, "prompt_tokens": 25}}) as mocked:
                report = mod.run(args)
            self.assertEqual(report["characters_generated"], 6)
            self.assertIn("阿明", Path(args.out, "scene.md").read_text(encoding="utf-8"))
            self.assertFalse(mocked.call_args.args[1]["chat_template_kwargs"]["enable_thinking"])

    def test_ollama_response(self):
        with patch.object(mod, "post_json", return_value={"message": {"content": "下雨了。"}, "eval_count": 5, "prompt_eval_count": 15}):
            text, usage = mod.generate("ollama", "http://local", "e4b", [], 128)
        self.assertEqual(text, "下雨了。")
        self.assertEqual(usage["completion_tokens"], 5)

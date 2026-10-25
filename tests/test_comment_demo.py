import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "comment_demo.py"
spec = importlib.util.spec_from_file_location("comment_demo", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PublicDemoCommentTests(TestCase):
    def test_render_result_contains_sample_and_run_reference(self):
        body = mod.render_comment("小葵：下雨了。", {"generation_seconds": 12, "end_to_end_tokens_per_second": 5.2}, "day2561124-art/AITEST", 123)
        self.assertIn("小葵：下雨了。", body)
        self.assertIn("/actions/runs/123", body)
        self.assertIn("公開可見", body)

    def test_warn_when_completion_is_truncated(self):
        body = mod.render_comment(
            "未完的一段", {"finish_reason": "length"}, "day2561124-art/AITEST", 123
        )
        self.assertIn("max_tokens 上限", body)

    def test_refuse_empty_or_oversized_public_result(self):
        for scene in [" ", "字" * 12001]:
            with self.subTest(size=len(scene)), self.assertRaises(ValueError):
                mod.render_comment(scene, {}, "day2561124-art/AITEST", 123)

    def test_refuse_invalid_target_and_missing_token(self):
        with self.assertRaises(ValueError):
            mod.render_comment("hello", {}, "../escape", 123)
        with self.assertRaises(ValueError):
            mod.post_comment("", "day2561124-art/AITEST", 1, "demo")

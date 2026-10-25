import base64
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_scene.py"
spec = importlib.util.spec_from_file_location("prepare_scene", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def example_scene():
    return {"setting": "書店", "characters": [{"name": "小葵"}], "plot_beats": ["下雨"]}


def event_payload(body, title="[E4B SCENE]", author="day2561124-art"):
    return {"repository": {"owner": {"login": "day2561124-art"}},
            "issue": {"title": title, "user": {"login": author}, "body": body}}


class PrepareSceneTests(TestCase):
    def test_custom_scene_base64(self):
        data = example_scene()
        encoded = base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode()
        self.assertEqual(mod.decode_input(encoded), data)

    def test_invalid_base64_rejected(self):
        with self.assertRaises(ValueError):
            mod.decode_input("***")

    def test_missing_characters_rejected(self):
        with self.assertRaises(ValueError):
            mod.parse_scene('{"x":1}')

    def test_public_custom_scene_allowed_by_user(self):
        with TemporaryDirectory() as d:
            s, out, tokens = [Path(d) / n for n in ("sample.json", "scene.json", "tokens.txt")]
            s.write_text('{"characters":[]}', encoding="utf-8")
            encoded = base64.b64encode(json.dumps(example_scene()).encode()).decode()
            mod.prepare_scene(s, out, encoded, max_tokens=256, token_destination=tokens)
            self.assertEqual(json.loads(out.read_text())["characters"][0]["name"], "小葵")
            self.assertEqual(tokens.read_text().strip(), "256")

    def test_owner_issue_receives_custom_scene(self):
        with TemporaryDirectory() as d:
            s, out, event, tokens = [Path(d) / n for n in ("sample.json", "scene.json", "event.json", "tokens.txt")]
            s.write_text('{"characters":[]}', encoding="utf-8")
            envelope = {"max_tokens": 320, "scene": example_scene()}
            event.write_text(json.dumps(event_payload(json.dumps(envelope))), encoding="utf-8")
            n = mod.prepare_scene(s, out, "", event_path=event, token_destination=tokens)
            self.assertEqual(n, 320)
            self.assertEqual(json.loads(out.read_text())["plot_beats"], ["下雨"])
            self.assertEqual(tokens.read_text().strip(), "320")

    def test_demo_issue_ignores_body(self):
        with TemporaryDirectory() as d:
            s = Path(d) / "sample.json"
            s.write_text(json.dumps(example_scene()), encoding="utf-8")
            scene, tokens = mod.issue_scene_request(
                event_payload("not-json", title="[E4B DEMO] sample"), s
            )
            self.assertEqual(scene, example_scene())
            self.assertEqual(tokens, 720)

    def test_non_owner_refused(self):
        with TemporaryDirectory() as d:
            s = Path(d) / "sample.json"
            with self.assertRaisesRegex(ValueError, "owner"):
                mod.issue_scene_request(
                    event_payload('{"scene":{"characters":[]}}', author="other"), s
                )

    def test_invalid_issue_json_or_missing_scene_rejected(self):
        with TemporaryDirectory() as d:
            s = Path(d) / "sample.json"
            for body in ["{}", "~~~json\n{}\n~~~", "none"]:
                with self.subTest(body=body), self.assertRaises(ValueError):
                    mod.issue_scene_request(event_payload(body), s)

    def test_invalid_max_tokens(self):
        for value in [True, 0, 1001, "720", None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                mod.validate_max_tokens(value)

    def test_detects_obvious_credentials(self):
        for value in ["-----BEGIN PRIVATE KEY-----", "github_pat_" + "a"*35, "sk-"+"x"*30]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "credential"):
                mod.validate_scene({"characters": [], "notes": value})

    def test_large_scene_rejected(self):
        with self.assertRaisesRegex(ValueError, "large"):
            mod.validate_scene({"characters": [], "notes": "中" * 5000})

    def test_sample_fallback(self):
        with TemporaryDirectory() as d:
            s, out = Path(d) / "sample.json", Path(d) / "output.json"
            s.write_text('{"characters":[]}', encoding="utf-8")
            mod.prepare_scene(s, out, "")
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), {"characters": []})

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


class PrepareSceneTests(TestCase):
    def test_custom_scene_base64(self):
        data = {"characters": [{"name": "小葵"}], "plot_beats": ["下雨"]}
        encoded = base64.b64encode(json.dumps(data, ensure_ascii=False).encode()).decode()
        self.assertEqual(mod.decode_input(encoded), data)

    def test_invalid_base64_rejected(self):
        with self.assertRaises(ValueError):
            mod.decode_input("***")

    def test_missing_characters_rejected(self):
        data = base64.b64encode(b'{"x":1}').decode()
        with self.assertRaises(ValueError):
            mod.decode_input(data)

    def test_public_repo_rejects_custom_scene_before_writing(self):
        import base64
        with TemporaryDirectory() as d:
            s, out = Path(d) / "sample.json", Path(d) / "output.json"
            s.write_text('{"characters":[]}', encoding="utf-8")
            encoded = base64.b64encode(b'{"characters":[]}').decode()
            with self.assertRaisesRegex(ValueError, "PUBLIC repository"):
                mod.prepare_scene(s, out, encoded, private_repo=False)
            self.assertFalse(out.exists())

    def test_private_repo_accepts_custom_scene(self):
        import base64
        with TemporaryDirectory() as d:
            s, out = Path(d) / "sample.json", Path(d) / "output.json"
            s.write_text('{"characters":[]}', encoding="utf-8")
            encoded = base64.b64encode(b'{"characters":[{"name":"X"}]}').decode()
            mod.prepare_scene(s, out, encoded, private_repo=True)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["characters"][0]["name"], "X")

    def test_sample_fallback(self):
        with TemporaryDirectory() as d:
            s, out = Path(d) / "sample.json", Path(d) / "output.json"
            s.write_text('{"characters":[]}', encoding="utf-8")
            mod.prepare_scene(s, out, "")
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), {"characters": []})

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from io import BytesIO
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "github_bridge.py"
spec = importlib.util.spec_from_file_location("github_bridge", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class GitHubBridgeTests(TestCase):
    def test_public_repo_rejects_custom_scene(self):
        with self.assertRaisesRegex(ValueError, "PUBLIC repository"):
            mod.require_private_for_custom_scene(False, Path("private-scene.json"))

    def test_demo_allowed_in_public(self):
        mod.require_private_for_custom_scene(False, None)

    def test_private_repo_allows_custom_scene(self):
        mod.require_private_for_custom_scene(True, Path("fiction.json"))

    def test_artifact_safe_extraction(self):
        raw = BytesIO()
        with zipfile.ZipFile(raw, "w") as z:
            z.writestr("scene.md", "這是測試。")
            z.writestr("../escape.txt", "NO")
            z.writestr("metrics.json", "{}")
        with TemporaryDirectory() as d:
            paths = mod.extract_artifact_safely(raw.getvalue(), Path(d))
            self.assertEqual(set(paths), {"scene.md", "metrics.json"})
            self.assertFalse((Path(d).parent / "escape.txt").exists())

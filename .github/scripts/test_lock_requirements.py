#!/usr/bin/env python3

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("lock_requirements.py")
SPEC = importlib.util.spec_from_file_location("lock_requirements", SCRIPT)
lock_requirements = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(lock_requirements)


class LockRequirementsTests(unittest.TestCase):
    def test_render_preserves_direct_extras_and_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "requirements.in"
            source.write_text("example[feature]==1.2.3\n", encoding="utf-8")
            lock = root / "pylock.toml"
            lock.write_text(
                """
lock-version = "1.0"

[[packages]]
name = "example"
version = "1.2.3"

[[packages.wheels]]
name = "example.whl"
url = "https://example.invalid/example.whl"

[packages.wheels.hashes]
sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
""".strip(),
                encoding="utf-8",
            )

            rendered = lock_requirements.render(source, lock)

            self.assertIn("example[feature]==1.2.3", rendered)
            self.assertIn("--hash=sha256:" + ("a" * 64), rendered)

    def test_validate_output_rejects_stale_direct_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "requirements.in"
            source.write_text("example==2.0.0\n", encoding="utf-8")
            output = root / "requirements.txt"
            output.write_text(
                "example==1.0.0 \\\n    --hash=sha256:" + ("a" * 64) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                lock_requirements.validate_output(source, output)


if __name__ == "__main__":
    unittest.main()

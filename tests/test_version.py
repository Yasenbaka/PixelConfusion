"""Version resolution and packaging metadata tests."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build
from pixelconfusion.version import (
    ENV_VAR,
    VERSION,
    VERSION_CONFIG_NAME,
    VERSION_LABELS,
    VERSION_PARTS,
    ResolvedVersion,
    VersionError,
    bump_version,
    format_version,
    parse_version,
    read_version_config,
    read_version_parts,
    resolve_version,
    version_detail,
    write_version_config,
    write_version_source,
)

SAMPLE_VERSION_SOURCE = """'''Sample version module.'''

VERSION_PARTS: tuple[int, int, int] = (1, 2, 3)
"""


class VersionValueTests(unittest.TestCase):
    def test_code_version_is_major_minor_patch(self):
        self.assertEqual(len(VERSION_PARTS), 3)
        self.assertEqual(VERSION, format_version(VERSION_PARTS))
        self.assertRegex(VERSION, r"^\d+\.\d+\.\d+$")
        self.assertEqual(VERSION, format_version(parse_version(VERSION)))

    def test_parse_version(self):
        self.assertEqual(parse_version("0.0.1"), (0, 0, 1))
        self.assertEqual(parse_version(" 12.34.56 "), (12, 34, 56))
        for invalid in ("1.0", "1.0.0.0", "v1.0.0", "", "1..0", "1.0.-1"):
            with self.subTest(value=invalid):
                with self.assertRaises(VersionError):
                    parse_version(invalid)

    def test_format_version_rejects_negative_parts(self):
        with self.assertRaises(VersionError):
            format_version((1, -1, 0))

    def test_bump_resets_less_significant_parts(self):
        self.assertEqual(bump_version((1, 4, 2), "major"), (2, 0, 0))
        self.assertEqual(bump_version((1, 4, 2), "minor"), (1, 5, 0))
        self.assertEqual(bump_version((1, 4, 2), "patch"), (1, 4, 3))
        with self.assertRaises(VersionError):
            bump_version((1, 4, 2), "build")

    def test_labels_and_detail_use_project_vocabulary(self):
        self.assertEqual(len(VERSION_LABELS), 3)
        resolved = ResolvedVersion((2, 1, 3), "test")
        self.assertEqual(resolved.text, "2.1.3")
        self.assertEqual(
            resolved.components(), "大更新 2 · 中期更新 1 · 小更新 3")
        self.assertEqual(
            resolved.detail(), "2.1.3（大更新 2 · 中期更新 1 · 小更新 3）")
        self.assertIn(VERSION, version_detail())


class VersionSourceTests(unittest.TestCase):
    def test_read_version_parts_from_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "version.py"
            path.write_text(SAMPLE_VERSION_SOURCE, encoding="utf-8")
            self.assertEqual(read_version_parts(path), (1, 2, 3))

    def test_read_version_parts_reports_missing_assignment(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "version.py"
            path.write_text("VERSION_PARTS = '1.0.0'\n", encoding="utf-8")
            with self.assertRaises(VersionError):
                read_version_parts(path)

    def test_write_version_source_preserves_the_rest_of_the_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "version.py"
            path.write_text(SAMPLE_VERSION_SOURCE, encoding="utf-8")
            write_version_source(path, (4, 5, 6))
            self.assertEqual(read_version_parts(path), (4, 5, 6))
            text = path.read_text(encoding="utf-8")
            self.assertIn("'''Sample version module.'''", text)
            self.assertIn("VERSION_PARTS: tuple[int, int, int] = (4, 5, 6)", text)


class VersionConfigTests(unittest.TestCase):
    def test_missing_config_returns_none(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(
                read_version_config(Path(directory) / VERSION_CONFIG_NAME))

    def test_config_contains_a_version_field(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / VERSION_CONFIG_NAME
            path.write_text('{"version": "3.2.1"}', encoding="utf-8")
            self.assertEqual(read_version_config(path), (3, 2, 1))

    def test_invalid_configs_are_rejected(self):
        payloads = ("{", '{"minor": 1}', '{"version": "1.0"}', '["1.0.0"]')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / VERSION_CONFIG_NAME
            for payload in payloads:
                with self.subTest(payload=payload):
                    path.write_text(payload, encoding="utf-8")
                    with self.assertRaises(VersionError):
                        read_version_config(path)

    def test_write_version_config_keeps_existing_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / VERSION_CONFIG_NAME
            path.write_text(
                json.dumps({"version": "1.0.0", "channel": "beta"}),
                encoding="utf-8")
            write_version_config(path, (2, 0, 0))
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload, {"version": "2.0.0", "channel": "beta"})


class VersionResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        source = self.root / "pixelconfusion"
        source.mkdir()
        (source / "version.py").write_text(
            SAMPLE_VERSION_SOURCE, encoding="utf-8")

    def tearDown(self):
        self.temporary.cleanup()

    def test_code_is_the_fallback(self):
        resolved = resolve_version(self.root, environ={})
        self.assertEqual(resolved.parts, (1, 2, 3))
        self.assertEqual(resolved.source, "pixelconfusion/version.py")

    def test_config_overrides_code(self):
        (self.root / VERSION_CONFIG_NAME).write_text(
            '{"version": "4.5.6"}', encoding="utf-8")
        resolved = resolve_version(self.root, environ={})
        self.assertEqual(resolved.text, "4.5.6")
        self.assertEqual(resolved.source, VERSION_CONFIG_NAME)

    def test_environment_overrides_config(self):
        (self.root / VERSION_CONFIG_NAME).write_text(
            '{"version": "4.5.6"}', encoding="utf-8")
        resolved = resolve_version(
            self.root, environ={ENV_VAR: "7.8.9"})
        self.assertEqual(resolved.text, "7.8.9")
        self.assertEqual(resolved.source, f"环境变量 {ENV_VAR}")

    def test_cli_overrides_everything(self):
        (self.root / VERSION_CONFIG_NAME).write_text(
            '{"version": "4.5.6"}', encoding="utf-8")
        resolved = resolve_version(
            self.root, cli_version="9.9.9",
            environ={ENV_VAR: "7.8.9"})
        self.assertEqual(resolved.text, "9.9.9")
        self.assertEqual(resolved.source, "命令行 --version")

    def test_invalid_environment_value_is_reported(self):
        with self.assertRaises(VersionError):
            resolve_version(self.root, environ={ENV_VAR: "latest"})

    def test_persist_targets_the_active_config_source(self):
        config_path = self.root / VERSION_CONFIG_NAME
        config_path.write_text('{"version": "4.5.6"}', encoding="utf-8")
        written = build._persist_version(self.root, (5, 0, 0))
        self.assertEqual(written, VERSION_CONFIG_NAME)
        self.assertEqual(read_version_config(config_path), (5, 0, 0))
        self.assertEqual(
            read_version_parts(self.root / "pixelconfusion" / "version.py"),
            (1, 2, 3))

    def test_persist_writes_back_to_code_without_config(self):
        written = build._persist_version(self.root, (5, 0, 0))
        self.assertEqual(written, "pixelconfusion/version.py")
        self.assertEqual(
            read_version_parts(self.root / "pixelconfusion" / "version.py"),
            (5, 0, 0))


class BuildMetadataTests(unittest.TestCase):
    def test_version_resource_is_valid_python_with_expected_values(self):
        text = build.render_version_resource(
            ResolvedVersion((1, 0, 0), "test"),
            "PixelConfusion-1.0.0.exe")
        compile(text, "<version resource>", "exec")
        self.assertIn("filevers=(1, 0, 0, 0)", text)
        self.assertIn("StringStruct('ProductVersion', '1.0.0')", text)
        self.assertIn("StringStruct('FileVersion', '1.0.0')", text)
        self.assertIn("PixelConfusion-1.0.0.exe", text)
        self.assertIn("像素混淆器", text)

    def test_version_resource_escapes_quotes(self):
        text = build.render_version_resource(
            ResolvedVersion((1, 2, 3), "test"), "it's.exe")
        self.assertIn("it\\'s.exe", text)
        compile(text, "<version resource>", "exec")

    def test_print_version_flag_prints_only_the_version(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(build.main(["--print-version"]), 0)
        self.assertEqual(output.getvalue().strip(), VERSION)

    def test_conflicting_version_flags_are_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                build._parse_args(
                    ["--version", "1.0.0", "--bump", "patch"])

    def test_dry_run_bump_does_not_touch_the_version_source(self):
        source = build.ROOT / "pixelconfusion" / "version.py"
        config = build.ROOT / VERSION_CONFIG_NAME
        before = (source.read_bytes(),
                  config.read_bytes() if config.is_file() else None)
        output = io.StringIO()
        with patch.dict(os.environ, {ENV_VAR: ""}):
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    build.main(["--bump", "patch", "--dry-run"]), 0)
        after = (source.read_bytes(),
                 config.read_bytes() if config.is_file() else None)
        self.assertEqual(before, after)
        expected = format_version(bump_version(parse_version(VERSION), "patch"))
        self.assertIn(f"PixelConfusion-{expected}.exe", output.getvalue())


if __name__ == "__main__":
    unittest.main()

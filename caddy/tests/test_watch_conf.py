import contextlib
import io
import logging
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


CADDY_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CADDY_DIR))

from watch_conf import snapshot, watch_directory


class WatchConfTests(unittest.TestCase):
    def test_snapshot_hashes_only_caddy_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            (directory / "site.caddy").write_text("reverse_proxy a:80", encoding="utf-8")
            (directory / "notes.txt").write_text("ignored", encoding="utf-8")
            (directory / "nested.caddy").mkdir()

            result = snapshot(directory)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "site.caddy")

    def test_missing_directory_has_empty_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(snapshot(Path(temp_dir) / "missing"), ())

    def test_watcher_reloads_once_when_a_dropin_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir) / "conf.d"
            directory.mkdir()
            dropin = directory / "site.caddy"
            dropin.write_text("reverse_proxy first:80", encoding="utf-8")
            runner = Mock(return_value=SimpleNamespace(returncode=0, stderr=""))
            slept = False

            def tick(_interval):
                nonlocal slept
                if not slept:
                    dropin.write_text("reverse_proxy second:80", encoding="utf-8")
                    slept = True

            watch_directory(directory, Path(temp_dir) / "Caddyfile", interval=0,
                            sleep=tick, runner=runner, max_iterations=1)

        runner.assert_called_once()
        self.assertEqual(runner.call_args.args[0], [
            "/usr/bin/caddy", "reload", "--config", str(Path(temp_dir) / "Caddyfile"),
            "--adapter", "caddyfile",
        ])

    def test_failed_reload_does_not_log_command_output_or_repeat(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir) / "conf.d"
            directory.mkdir()
            dropin = directory / "site.caddy"
            dropin.write_text("reverse_proxy first:80", encoding="utf-8")
            runner = Mock(return_value=SimpleNamespace(returncode=1, stderr="secret-config-token"))
            changed = False

            def tick(_interval):
                nonlocal changed
                if not changed:
                    dropin.write_text("invalid config", encoding="utf-8")
                    changed = True

            output = io.StringIO()
            handler = logging.StreamHandler(output)
            logger = logging.getLogger("watch_conf")
            logger.addHandler(handler)
            try:
                with contextlib.redirect_stderr(output):
                    watch_directory(directory, Path(temp_dir) / "Caddyfile", interval=0,
                                    sleep=tick, runner=runner, max_iterations=3)
            finally:
                logger.removeHandler(handler)

        runner.assert_called_once()
        self.assertNotIn("secret-config-token", output.getvalue())
        self.assertIn("previous configuration remains active", output.getvalue())


if __name__ == "__main__":
    unittest.main()

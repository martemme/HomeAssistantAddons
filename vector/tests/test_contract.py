import pathlib
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[2]
ADDON = ROOT / "vector"


class VectorAddonContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = yaml.safe_load((ADDON / "config.yaml").read_text(encoding="utf-8"))
        cls.vector = yaml.safe_load((ADDON / "vector.yaml").read_text(encoding="utf-8"))
        cls.dockerfile = (ADDON / "Dockerfile").read_text(encoding="utf-8")
        cls.run_script = (ADDON / "run.sh").read_text(encoding="utf-8")

    def test_manifest_mounts_journald_and_exposes_documented_options(self):
        self.assertEqual("vector", self.manifest["slug"])
        self.assertIs(self.manifest["journald"], True)
        self.assertEqual({"amd64", "aarch64"}, set(self.manifest["arch"]))
        self.assertEqual(
            {"victorialogs_url": "http://10.30.20.20:9428", "host_label": "homeassistant"},
            self.manifest["options"],
        )
        self.assertEqual(
            {"victorialogs_url": "url", "host_label": "str"},
            self.manifest["schema"],
        )

    def test_journal_transform_separates_container_and_system_logs(self):
        self.assertEqual("journald", self.vector["sources"]["haos_journal"]["type"])
        self.assertEqual(
            "__JOURNAL_DIRECTORY__",
            self.vector["sources"]["haos_journal"]["journal_directory"],
        )
        transform = self.vector["transforms"]["normalize_haos_journal"]
        self.assertEqual(["haos_journal"], transform["inputs"])
        for required in ("CONTAINER_NAME", "haos_addon", "haos_system", "SYSLOG_IDENTIFIER", "_SYSTEMD_UNIT"):
            self.assertIn(required, transform["source"])
        self.assertEqual(
            {"normalize_haos_journal"},
            set(self.vector["sinks"]["victorialogs"]["inputs"]),
        )
        sink_uri = self.vector["sinks"]["victorialogs"]["uri"]
        self.assertIn("http://victorialogs.local:9428/insert/jsonline", sink_uri)
        self.assertIn("_stream_fields=host,source_type,service", sink_uri)
        self.assertIn("__HOST_LABEL__", transform["source"])

    def test_vector_native_tests_cover_core_and_system_journal_entries(self):
        names = {test["name"] for test in self.vector.get("tests", [])}
        self.assertEqual(
            {
                "classify Home Assistant container journal entry",
                "classify HAOS add-on container journal entry",
                "classify HAOS system journal entry",
                "fall back to the HAOS systemd unit without an identifier",
            },
            names,
        )

    def test_image_provides_journalctl_and_pins_the_vector_source_image(self):
        self.assertEqual(
            {
                "amd64": "ghcr.io/home-assistant/base-debian:trixie",
                "aarch64": "ghcr.io/home-assistant/base-debian:trixie",
            },
            self.manifest["build_from"],
        )
        self.assertIn("systemd", self.dockerfile)
        self.assertIn("timberio/vector:0.44.0-debian@sha256:", self.dockerfile)
        self.assertIn("/usr/local/bin/vector", self.dockerfile)
        self.assertIn("command -v journalctl", self.run_script)

    def test_entrypoint_validates_options_and_executes_rendered_config(self):
        for required in (
            "/data/options.json",
            "victorialogs_url",
            "host_label",
            "victorialogs.local:9428",
            "__JOURNAL_DIRECTORY__",
            "JOURNAL_DIRECTORY",
            "/var/log/journal",
            "/run/log/journal",
            "__HOST_LABEL__",
            "vector validate",
            "exec /usr/local/bin/vector",
        ):
            self.assertIn(required, self.run_script)


if __name__ == "__main__":
    unittest.main()

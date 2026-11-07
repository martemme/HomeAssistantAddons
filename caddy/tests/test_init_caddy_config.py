import re
import unittest
from pathlib import Path


CADDY_DIR = Path(__file__).resolve().parents[1]
INIT_SCRIPT = CADDY_DIR / "rootfs/etc/s6-overlay/s6-rc.d/init-caddy-config/run"


class InitCaddyConfigTests(unittest.TestCase):
    def test_custom_header_secrets_are_installed_for_caddy_and_watcher_environment(self):
        script = INIT_SCRIPT.read_text(encoding="utf-8")

        self.assertIn("--secrets-output /data/caddy-secrets.env", script)
        self.assertIn("--environment-directory /var/run/s6/container_environment", script)
        self.assertIn("/var/run/s6/container_environment/CF_API_TOKEN", script)

        for service in ("caddy", "watch-config"):
            entrypoint = (
                CADDY_DIR / "rootfs/etc/s6-overlay/s6-rc.d" / service / "run"
            ).read_text(encoding="utf-8")
            self.assertIn("#!/command/with-contenv bashio", entrypoint)

    def test_caddy_service_uses_config_generated_by_init_service(self):
        run_script = (CADDY_DIR / "run.sh").read_text(encoding="utf-8")

        self.assertNotIn("generate_caddyfile.py", run_script)
        self.assertIn("/usr/bin/caddy run --config /data/Caddyfile --adapter caddyfile", run_script)

    def test_cloudflare_token_is_scoped_to_caddy_validation(self):
        script = INIT_SCRIPT.read_text(encoding="utf-8")
        token_read = script.index(
            'token="$(bashio::config \'cloudflare_api_token\')'
        )
        token_file_write = script.index(
            'printf \'%s\' "${token}" > /var/run/s6/container_environment/CF_API_TOKEN'
        )
        token_unset = re.search(r'(?m)^unset CF_API_TOKEN\s*$', script)
        generator = script.index("python3 /usr/local/bin/generate_caddyfile.py")
        validation = re.search(
            r'(?m)^if ! CF_API_TOKEN="\$\{token\}" /usr/bin/caddy validate',
            script,
        )

        self.assertIsNotNone(
            validation,
            "only caddy validate should receive the token in its process environment",
        )
        if validation is None:
            return
        self.assertNotRegex(script, r'(?m)^export\s+CF_API_TOKEN\b')
        self.assertIsNotNone(token_unset, "clear inherited Cloudflare token before config generation")
        if token_unset is None:
            return
        self.assertLess(token_read, token_file_write)
        self.assertLess(token_file_write, token_unset.start())
        self.assertLess(token_unset.start(), generator)
        self.assertLess(generator, validation.start())


if __name__ == "__main__":
    unittest.main()

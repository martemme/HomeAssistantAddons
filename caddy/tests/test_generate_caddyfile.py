import json
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CADDY_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CADDY_DIR.parent
sys.path.insert(0, str(CADDY_DIR))

from generate_caddyfile import generate_caddyfile, main  # noqa: E402


class GenerateCaddyfileTests(unittest.TestCase):
    def valid_options(self):
        return {
            "domain": "example.com",
            "cloudflare_api_token": "secret-token-do-not-print",
            "routes": [
                {"subdomain": "ha", "target": "homeassistant:8123"},
                {"subdomain": "photos", "target": "https://photos.internal:8443"},
            ],
        }

    def test_generates_domain_wildcard_routes_and_import(self):
        output = generate_caddyfile(self.valid_options())

        self.assertIn("example.com, *.example.com", output)
        self.assertIn("dns cloudflare {env.CF_API_TOKEN}", output)
        self.assertIn("resolvers 1.1.1.1", output)
        self.assertIn("@route_0 host ha.example.com", output)
        self.assertIn("reverse_proxy @route_0 homeassistant:8123", output)
        self.assertIn("@route_1 host photos.example.com", output)
        self.assertIn("reverse_proxy @route_1 https://photos.internal:8443", output)
        self.assertIn("import /share/caddy/conf.d/*.caddy", output)
        self.assertNotIn("secret-token-do-not-print", output)

    def test_import_directive_is_inside_the_site_block(self):
        output = generate_caddyfile(self.valid_options())
        site_start = output.index("example.com, *.example.com {")
        site_end = output.index("\n}", site_start)
        import_position = output.index("import /share/caddy/conf.d/*.caddy")

        self.assertLess(site_start, import_position)
        self.assertLess(import_position, site_end)

    def test_domain_defaults_when_omitted(self):
        options = self.valid_options()
        del options["domain"]

        self.assertIn("example.com, *.example.com", generate_caddyfile(options))

    def test_email_is_optional_and_included_when_supplied(self):
        options = self.valid_options()
        without_email = generate_caddyfile(options)
        options["email"] = "admin@example.org"
        with_email = generate_caddyfile(options)

        self.assertNotIn("email admin@example.org", without_email)
        self.assertIn("email admin@example.org", with_email)

    def test_empty_optional_email_is_omitted(self):
        options = self.valid_options()
        options["email"] = ""

        self.assertNotIn("email ", generate_caddyfile(options))

    def test_rejects_email_caddyfile_injection(self):
        options = self.valid_options()
        options["email"] = "admin@example.org;respond"

        with self.assertRaises(ValueError):
            generate_caddyfile(options)

    def test_rejects_duplicate_route_host(self):
        options = self.valid_options()
        options["routes"].append({"subdomain": "ha", "target": "other:80"})

        with self.assertRaises(ValueError):
            generate_caddyfile(options)

    def test_rejects_route_hostname_over_dns_length_limit(self):
        options = self.valid_options()
        options["domain"] = "a" * 63 + "." + "b" * 63 + "." + "c" * 63 + "." + "d" * 61
        options["routes"] = [{"subdomain": "app", "target": "upstream:80"}]

        with self.assertRaises(ValueError):
            generate_caddyfile(options)

    def test_rejects_invalid_subdomain_and_caddyfile_injection(self):
        for subdomain in ("bad_label", "ha; respond 200", "a..b", "*.ha", " ha"):
            with self.subTest(subdomain=subdomain):
                options = self.valid_options()
                options["routes"] = [{"subdomain": subdomain, "target": "upstream:80"}]
                with self.assertRaises(ValueError):
                    generate_caddyfile(options)

    def test_rejects_invalid_domain(self):
        for domain in ("https://example.org", "example.org/path", "a..b", " example.org"):
            with self.subTest(domain=domain):
                options = self.valid_options()
                options["domain"] = domain
                with self.assertRaises(ValueError):
                    generate_caddyfile(options)

    def test_rejects_invalid_upstream_targets(self):
        for target in (
            "upstream",
            "http://upstream",
            "upstream:0",
            "upstream:65536",
            "upstream:abc",
            "upstream:80 other:80",
            "upstream:80\nrespond 200",
            "http://upstream/path:80",
        ):
            with self.subTest(target=target):
                options = self.valid_options()
                options["routes"] = [{"subdomain": "app", "target": target}]
                with self.assertRaises(ValueError):
                    generate_caddyfile(options)

    def test_accepts_bracketed_ipv6_upstream(self):
        options = self.valid_options()
        options["routes"] = [{"subdomain": "app", "target": "[2001:db8::1]:443"}]

        self.assertIn("reverse_proxy @route_0 [2001:db8::1]:443", generate_caddyfile(options))

    def test_missing_token_fails_without_leaking_other_values(self):
        options = self.valid_options()
        del options["cloudflare_api_token"]

        with self.assertRaises(ValueError) as caught:
            generate_caddyfile(options)
        self.assertNotIn("secret-token-do-not-print", str(caught.exception))

    def test_cli_writes_output_atomically_and_does_not_leak_token(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            options_path = Path(temp_dir) / "options.json"
            output_path = Path(temp_dir) / "Caddyfile"
            options_path.write_text(json.dumps(self.valid_options()), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(CADDY_DIR / "generate_caddyfile.py"),
                 "--options", str(options_path), "--output", str(output_path)],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_path.is_file())
            self.assertNotIn("secret-token-do-not-print", output_path.read_text(encoding="utf-8"))
            self.assertNotIn("secret-token-do-not-print", result.stdout + result.stderr)

    def test_cli_returns_nonzero_for_invalid_options(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            options_path = Path(temp_dir) / "options.json"
            output_path = Path(temp_dir) / "Caddyfile"
            options = self.valid_options()
            options["routes"] = [{"subdomain": "app", "target": "bad target"}]
            options_path.write_text(json.dumps(options), encoding="utf-8")

            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = main(["--options", str(options_path), "--output", str(output_path)])

            self.assertNotEqual(status, 0)
            self.assertFalse(output_path.exists())
            self.assertNotIn("secret-token-do-not-print", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

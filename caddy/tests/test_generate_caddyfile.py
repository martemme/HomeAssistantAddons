import json
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


CADDY_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = CADDY_DIR.parent
sys.path.insert(0, str(CADDY_DIR))

import generate_caddyfile as generator_module  # noqa: E402
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

    def test_sends_ip_only_x_forwarded_for_to_each_upstream(self):
        output = generate_caddyfile(self.valid_options())

        self.assertEqual(
            output.count("header_up X-Forwarded-For {http.request.remote.host}"),
            2,
        )

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

    def test_config_schema_declares_optional_generic_route_auth_fields(self):
        config = json.loads((CADDY_DIR / "config.json").read_text(encoding="utf-8"))
        route_schema = config["schema"]["routes"][0]

        self.assertEqual(route_schema["basic_auth_username"], "str?")
        self.assertEqual(route_schema["basic_auth_password"], "password?")
        self.assertEqual(route_schema["custom_header_name"], "str?")
        self.assertEqual(route_schema["custom_header_value"], "password?")

    def test_cli_exports_custom_header_secret_to_s6_environment_private_file(self):
        options = self.valid_options()
        token = "test-header-token_123"
        options["routes"] = [{
            "subdomain": "ai",
            "target": "router:8765",
            "custom_header_name": "X-Gitlab-Token",
            "custom_header_value": token,
        }]
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            options_path = root / "options.json"
            output_path = root / "Caddyfile"
            secrets_path = root / "caddy-secrets.env"
            environment_dir = root / "container_environment"
            options_path.write_text(json.dumps(options), encoding="utf-8")

            status = main([
                "--options", str(options_path),
                "--output", str(output_path),
                "--secrets-output", str(secrets_path),
                "--environment-directory", str(environment_dir),
            ])

            runtime_secret = environment_dir / "CADDY_CUSTOM_HEADER_0"
            self.assertEqual(status, 0)
            self.assertEqual(secrets_path.read_text(encoding="utf-8"), f"CADDY_CUSTOM_HEADER_0={token}\n")
            self.assertEqual(runtime_secret.read_text(encoding="utf-8"), token)
            self.assertEqual(secrets_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(runtime_secret.stat().st_mode & 0o777, 0o600)
            self.assertNotIn(token, output_path.read_text(encoding="utf-8"))

    def test_authentication_hash_and_custom_header_use_safe_process_boundaries(self):
        options = self.valid_options()
        password = "not-a-real-basic-auth-password"
        header_token = "test-header-token_123"
        options["routes"] = [{
            "subdomain": "ai",
            "target": "router:8765",
            "basic_auth_username": "ado-hook",
            "basic_auth_password": password,
            "custom_header_name": "X-Gitlab-Token",
            "custom_header_value": header_token,
        }]

        with tempfile.TemporaryDirectory() as temp_dir:
            fake_caddy = Path(temp_dir) / "caddy"
            capture_path = Path(temp_dir) / "hash-process.json"
            fake_caddy.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "with open(os.environ['CADDY_TEST_CAPTURE'], 'w', encoding='utf-8') as output:\n"
                "    json.dump({'argv': sys.argv[1:], 'stdin': sys.stdin.read(), "
                "'cf_token': os.environ.get('CF_API_TOKEN')}, output)\n"
                "print('$argon2id$v=19$m=65536,t=3,p=2$YWJj$ZGVm')\n",
                encoding="utf-8",
            )
            fake_caddy.chmod(0o755)
            with mock.patch.object(generator_module, "CADDY_BINARY", str(fake_caddy), create=True):
                with mock.patch.dict(os.environ, {
                    "CF_API_TOKEN": "synthetic-cloudflare-token",
                    "CADDY_TEST_CAPTURE": str(capture_path),
                }):
                    output = generate_caddyfile(options)

            hash_process = json.loads(capture_path.read_text(encoding="utf-8"))

        self.assertIn("basic_auth @route_0 argon2id {", output)
        self.assertIn("$argon2id$v=19$m=65536,t=3,p=2$YWJj$ZGVm", output)
        self.assertIn("header_up X-Gitlab-Token {env.CADDY_CUSTOM_HEADER_0}", output)
        self.assertIn("header_up -Authorization", output)
        self.assertNotIn(password, output)
        self.assertNotIn(header_token, output)
        self.assertEqual(hash_process["argv"], ["hash-password", "--algorithm", "argon2id"])
        self.assertEqual(hash_process["stdin"], password + "\n")
        self.assertIsNone(hash_process["cf_token"])

    def test_rejects_incomplete_basic_auth_pair(self):
        options = self.valid_options()
        options["routes"][0]["basic_auth_username"] = "ado-hook"

        with self.assertRaises(ValueError):
            generate_caddyfile(options)

    def test_rejects_incomplete_custom_header_pair(self):
        options = self.valid_options()
        options["routes"][0]["custom_header_name"] = "X-Webhook-Token"

        with self.assertRaises(ValueError):
            generate_caddyfile(options)

    def test_rejects_authorization_and_caddyfile_injection_custom_headers(self):
        for header_name, header_value in (
            ("Authorization", "safe_token"),
            ("authorization", "safe_token"),
            ("X-Test\nrespond", "safe_token"),
            ("X-Test", "value with spaces"),
            ("X-Test", "value\nrespond 200"),
            ("X-Test", "{env.CF_API_TOKEN}"),
        ):
            with self.subTest(header_name=header_name, header_value=header_value):
                options = self.valid_options()
                options["routes"][0].update({
                    "custom_header_name": header_name,
                    "custom_header_value": header_value,
                })
                with self.assertRaises(ValueError):
                    generate_caddyfile(options)

    def test_password_hash_failure_does_not_expose_process_errors(self):
        options = self.valid_options()
        options["routes"][0].update({
            "basic_auth_username": "webhook",
            "basic_auth_password": "synthetic-password-sentinel",
        })
        error_sentinel = "hash-error-password-sentinel"
        failed = subprocess.CompletedProcess(
            args=["caddy", "hash-password"],
            returncode=1,
            stdout="",
            stderr=error_sentinel,
        )

        with mock.patch.object(generator_module.subprocess, "run", return_value=failed) as run:
            with self.assertRaises(ValueError) as caught:
                generate_caddyfile(options)

        self.assertNotIn("hash-error-password-sentinel", str(caught.exception))
        self.assertNotIn("synthetic-password-sentinel", str(caught.exception))
        self.assertNotIn("synthetic-password-sentinel", repr(run.call_args.args[0]))
        self.assertNotIn("synthetic-password-sentinel", str(run.call_args.kwargs.get("env")))
        self.assertEqual(run.call_args.kwargs.get("input"), "synthetic-password-sentinel\n")

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
            secrets_path = Path(temp_dir) / "caddy-secrets.env"
            options_path.write_text(json.dumps(self.valid_options()), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(CADDY_DIR / "generate_caddyfile.py"),
                 "--options", str(options_path), "--output", str(output_path),
                 "--secrets-output", str(secrets_path),
                 "--environment-directory", str(Path(temp_dir) / "container_environment")],
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
                status = main([
                    "--options", str(options_path),
                    "--output", str(output_path),
                    "--secrets-output", str(Path(temp_dir) / "caddy-secrets.env"),
                    "--environment-directory", str(Path(temp_dir) / "container_environment"),
                ])

            self.assertNotEqual(status, 0)
            self.assertFalse(output_path.exists())
            self.assertNotIn("secret-token-do-not-print", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

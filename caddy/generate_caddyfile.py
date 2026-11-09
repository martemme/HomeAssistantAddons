import argparse
import ipaddress
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


_DEFAULT_DOMAIN = "example.com"
_IMPORT_DIRECTIVE = "import /share/caddy/conf.d/*.caddy"
CADDY_BINARY = "/usr/bin/caddy"
_DOMAIN_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")
_TARGET = re.compile(
    r"(?:(https?)://)?(\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?):([0-9]+)\Z"
)
_USERNAME = re.compile(r"[A-Za-z0-9._@+-]{1,128}\Z")
_HEADER_NAME = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]{1,128}\Z")
_HEADER_VALUE = re.compile(r"[A-Za-z0-9._~-]{1,512}\Z")
_HASHED_PASSWORD = re.compile(r"\$argon2id\$[A-Za-z0-9$=,+/._-]+\Z")


def _valid_dns_name(value):
    if not isinstance(value, str) or not value or len(value) > 253:
        return False
    labels = value.split(".")
    return all(_DOMAIN_LABEL.fullmatch(label) for label in labels)


def _valid_email(value):
    if not isinstance(value, str) or len(value) > 254 or value.count("@") != 1:
        return False
    local, domain = value.split("@")
    if (
        not 1 <= len(local) <= 64
        or not re.fullmatch(r"[A-Za-z0-9._%+-]+", local)
        or local.startswith(".")
        or local.endswith(".")
        or ".." in local
        or "." not in domain
    ):
        return False
    return _valid_dns_name(domain)


def _validate_target(target):
    if not isinstance(target, str):
        raise ValueError("Invalid route target.")
    match = _TARGET.fullmatch(target)
    if not match:
        raise ValueError("Invalid route target.")

    host = match.group(2)
    if host.startswith("["):
        try:
            ipaddress.IPv6Address(host[1:-1])
        except ipaddress.AddressValueError as exc:
            raise ValueError("Invalid route target.") from exc
    elif not _valid_dns_name(host):
        try:
            ipaddress.IPv4Address(host)
        except ipaddress.AddressValueError as exc:
            raise ValueError("Invalid route target.") from exc

    port = int(match.group(3))
    if not 1 <= port <= 65535:
        raise ValueError("Invalid route target.")


def _validated_options(options):
    if not isinstance(options, dict):
        raise ValueError("Invalid options.")

    token = options.get("cloudflare_api_token")
    if not isinstance(token, str) or not token.strip():
        raise ValueError("Missing Cloudflare API token.")

    domain = options.get("domain", _DEFAULT_DOMAIN)
    if not _valid_dns_name(domain):
        raise ValueError("Invalid domain.")

    email = options.get("email")
    if email == "":
        email = None
    elif email is not None and not _valid_email(email):
        raise ValueError("Invalid email.")

    routes = options.get("routes", [])
    if not isinstance(routes, list):
        raise ValueError("Invalid routes.")

    normalized = []
    seen = set()
    for route in routes:
        if not isinstance(route, dict):
            raise ValueError("Invalid route.")
        subdomain = route.get("subdomain")
        target = route.get("target")
        if not isinstance(subdomain, str) or not _valid_dns_name(subdomain):
            raise ValueError("Invalid route subdomain.")
        hostname = f"{subdomain}.{domain}".lower()
        if not _valid_dns_name(hostname):
            raise ValueError("Invalid route hostname.")
        if hostname in seen:
            raise ValueError("Duplicate route hostname.")
        seen.add(hostname)
        _validate_target(target)

        username = route.get("basic_auth_username")
        password = route.get("basic_auth_password")
        if (username is None) != (password is None):
            raise ValueError("Incomplete route Basic Auth credentials.")
        if username is not None:
            if not isinstance(username, str) or not _USERNAME.fullmatch(username):
                raise ValueError("Invalid route Basic Auth username.")
            if (
                not isinstance(password, str)
                or not password
                or any(ord(char) < 32 or ord(char) == 127 for char in password)
            ):
                raise ValueError("Invalid route Basic Auth password.")

        header_name = route.get("custom_header_name")
        header_value = route.get("custom_header_value")
        if (header_name is None) != (header_value is None):
            raise ValueError("Incomplete custom route header.")
        if header_name is not None:
            if (
                not isinstance(header_name, str)
                or not _HEADER_NAME.fullmatch(header_name)
                or header_name.casefold() == "authorization"
            ):
                raise ValueError("Invalid custom route header name.")
            if not isinstance(header_value, str) or not _HEADER_VALUE.fullmatch(header_value):
                raise ValueError("Invalid custom route header value.")

        normalized.append((hostname, target, username, password, header_name, header_value))

    return domain, email, normalized


def _hash_password(password):
    environment = os.environ.copy()
    environment.pop("CF_API_TOKEN", None)
    try:
        result = subprocess.run(
            [CADDY_BINARY, "hash-password", "--algorithm", "argon2id"],
            input=f"{password}\n",
            capture_output=True,
            text=True,
            check=False,
            env=environment,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        raise ValueError("Unable to hash Basic Auth password.") from None
    hashed = result.stdout.strip()
    if result.returncode != 0 or not _HASHED_PASSWORD.fullmatch(hashed):
        raise ValueError("Unable to hash Basic Auth password.")
    return hashed


def _compile_configuration(options):
    domain, email, routes = _validated_options(options)
    lines = []
    secrets = []
    if email:
        lines.extend(("{", f"\temail {email}", "}", ""))

    lines.extend((f"{domain}, *.{domain} {{", "\ttls {", "\t\tdns cloudflare {env.CF_API_TOKEN}", "\t\tresolvers 1.1.1.1", "\t}"))
    for index, (hostname, target, username, password, header_name, header_value) in enumerate(routes):
        matcher = f"@route_{index}"
        lines.append(f"\t{matcher} host {hostname}")
        if username is not None:
            hashed = _hash_password(password)
            lines.extend((
                f"\tbasic_auth {matcher} argon2id {{",
                f"\t\t{username} {hashed}",
                "\t}",
            ))
        lines.extend((
            f"\treverse_proxy {matcher} {target} {{",
            "\t\theader_up X-Forwarded-For {http.request.remote.host}",
            "\t\theader_up -Authorization",
        ))
        if header_name is not None:
            variable = f"CADDY_CUSTOM_HEADER_{index}"
            lines.append(f"\t\theader_up {header_name} {{env.{variable}}}")
            secrets.append(f"{variable}={header_value}")
        lines.append("\t}")
    lines.extend((f"\t{_IMPORT_DIRECTIVE}", "}", ""))
    return "\n".join(lines), "\n".join(secrets) + ("\n" if secrets else "")


def generate_caddyfile(options):
    return _compile_configuration(options)[0]


def _atomic_write(path, content):
    destination = Path(path)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(destination.parent),
            prefix=f".{destination.name}.",
            delete=False,
        ) as temporary:
            temporary_path = temporary.name
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def _export_runtime_secrets(content, directory):
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    entries = {}
    for line in content.splitlines():
        name, separator, value = line.partition("=")
        if (
            not separator
            or not re.fullmatch(r"CADDY_CUSTOM_HEADER_[0-9]+", name)
            or not _HEADER_VALUE.fullmatch(value)
            or name in entries
        ):
            raise ValueError("Invalid generated header secrets.")
        entries[name] = value

    for previous in destination.glob("CADDY_CUSTOM_HEADER_*"):
        if previous.is_file():
            previous.unlink()
    for name, value in entries.items():
        _atomic_write(destination / name, value)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a Caddyfile from add-on options.")
    parser.add_argument("--options", required=True, help="Path to options.json")
    parser.add_argument("--output", required=True, help="Path to generated Caddyfile")
    parser.add_argument("--secrets-output", required=True, help="Path to private generated header secrets")
    parser.add_argument("--environment-directory", required=True, help="S6 container environment directory")
    args = parser.parse_args(argv)

    try:
        with open(args.options, "r", encoding="utf-8") as source:
            options = json.load(source)
        content, secrets = _compile_configuration(options)
        _atomic_write(args.secrets_output, secrets)
        _export_runtime_secrets(secrets, args.environment_directory)
        _atomic_write(args.output, content)
    except (OSError, ValueError, json.JSONDecodeError):
        print("Unable to generate Caddyfile from options.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

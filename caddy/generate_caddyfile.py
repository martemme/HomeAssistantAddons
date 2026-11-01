import argparse
import ipaddress
import json
import os
import re
import sys
import tempfile
from pathlib import Path


_DEFAULT_DOMAIN = "example.com"
_IMPORT_DIRECTIVE = "import /share/caddy/conf.d/*.caddy"
_DOMAIN_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")
_TARGET = re.compile(
    r"(?:(https?)://)?(\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?):([0-9]+)\Z"
)


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
        normalized.append((hostname, target))

    return domain, email, normalized


def generate_caddyfile(options):
    domain, email, routes = _validated_options(options)
    lines = []
    if email:
        lines.extend(("{", f"\temail {email}", "}", ""))

    lines.extend((f"{domain}, *.{domain} {{", "\ttls {", "\t\tdns cloudflare {env.CF_API_TOKEN}", "\t\tresolvers 1.1.1.1", "\t}"))
    for index, (hostname, target) in enumerate(routes):
        lines.extend(
            (
                f"\t@route_{index} host {hostname}",
                f"\treverse_proxy @route_{index} {target} {{",
                "\t\theader_up X-Forwarded-For {http.request.remote.host}",
                "\t}",
            )
        )
    lines.extend((f"\t{_IMPORT_DIRECTIVE}", "}", ""))
    return "\n".join(lines)


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
        os.replace(temporary_path, destination)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a Caddyfile from add-on options.")
    parser.add_argument("--options", required=True, help="Path to options.json")
    parser.add_argument("--output", required=True, help="Path to generated Caddyfile")
    args = parser.parse_args(argv)

    try:
        with open(args.options, "r", encoding="utf-8") as source:
            options = json.load(source)
        content = generate_caddyfile(options)
        _atomic_write(args.output, content)
    except (OSError, ValueError, json.JSONDecodeError):
        print("Unable to generate Caddyfile from options.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

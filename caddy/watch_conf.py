import argparse
import hashlib
import logging
import subprocess
import time
from pathlib import Path


_LOGGER = logging.getLogger("watch_conf")


def snapshot(directory):
    path = Path(directory)
    if not path.is_dir():
        return ()
    files = []
    for item in sorted(path.glob("*.caddy")):
        if item.is_file():
            digest = hashlib.sha256(item.read_bytes()).hexdigest()
            files.append((item.name, digest))
    return tuple(files)


def _reload(config, runner):
    command = [
        "/usr/bin/caddy",
        "reload",
        "--config",
        str(config),
        "--adapter",
        "caddyfile",
    ]
    try:
        result = runner(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        _LOGGER.warning("Caddy reload failed; previous configuration remains active.")
        return False

    if result.returncode != 0:
        # Do not log Caddy's stderr: imported configuration may contain secrets.
        _LOGGER.warning("Caddy reload failed; previous configuration remains active.")
        return False
    _LOGGER.info("Caddy configuration reloaded.")
    return True


def watch_directory(directory, config, interval=2, sleep=time.sleep,
                    runner=subprocess.run, max_iterations=None):
    current = snapshot(directory)
    iteration = 0
    while max_iterations is None or iteration < max_iterations:
        sleep(interval)
        iteration += 1
        try:
            updated = snapshot(directory)
        except OSError:
            _LOGGER.warning("Unable to read Caddy drop-ins; keeping the active configuration.")
            continue
        if updated == current:
            continue

        _LOGGER.info("Caddy drop-in change detected; reloading configuration.")
        _reload(config, runner)
        # Avoid retry loops on a rejected file. A subsequent edit triggers a new attempt.
        current = updated


def main(argv=None):
    parser = argparse.ArgumentParser(description="Reload Caddy when drop-ins change.")
    parser.add_argument("--directory", required=True, help="Directory containing .caddy files")
    parser.add_argument("--config", required=True, help="Path to the generated Caddyfile")
    parser.add_argument("--interval", type=float, default=2, help="Polling interval in seconds")
    args = parser.parse_args(argv)
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    watch_directory(args.directory, args.config, interval=args.interval)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

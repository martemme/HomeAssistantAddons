#!/usr/bin/env python3
"""Verify ADO router bundle, installed skill, and Hermes runtime copies."""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import types
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = (
    "SKILL.md",
    "references/ado-webhook-prompt.md",
    "scripts/normalize_ado_webhook.py",
    "scripts/prepare_ado_webhook.py",
    "scripts/test_normalize_ado_webhook.py",
    "scripts/test_prepare_ado_webhook.py",
    "scripts/verify_installation.py",
)
RUNTIME_SCRIPTS = ("normalize_ado_webhook.py", "prepare_ado_webhook.py")
TEST_FILES = ("test_normalize_ado_webhook.py", "test_prepare_ado_webhook.py")


def _compare(label: str, expected: Path, actual: Path) -> bool:
    if not expected.is_file() or not actual.is_file():
        print(f"[FAIL] {label}: missing {expected if not expected.is_file() else actual}")
        return False
    expected_bytes = expected.read_bytes()
    actual_bytes = actual.read_bytes()
    expected_hash = hashlib.sha256(expected_bytes).hexdigest()
    actual_hash = hashlib.sha256(actual_bytes).hexdigest()
    if expected_bytes != actual_bytes:
        print(f"[FAIL] {label}: {expected_hash[:12]} != {actual_hash[:12]}")
        return False
    print(f"[OK]   {label}: {expected_hash[:12]}")
    return True


def _run_active_tests(bundle: Path, active_scripts: Path) -> bool:
    success = True
    original_path = list(sys.path)
    sys.path.insert(0, str(active_scripts))
    try:
        for test_name in TEST_FILES:
            test_path = bundle / "scripts" / test_name
            if not test_path.is_file():
                print(f"[FAIL] active runtime tests: missing {test_path}")
                success = False
                continue
            for module_name in ("prepare_ado_webhook", "normalize_ado_webhook"):
                sys.modules.pop(module_name, None)
            module_name = f"_ado_router_runtime_{Path(test_name).stem}"
            test_module = types.ModuleType(module_name)
            test_module.__file__ = str(active_scripts / test_name)
            sys.modules[module_name] = test_module
            try:
                source = test_path.read_text(encoding="utf-8")
                exec(compile(source, str(test_path), "exec"), test_module.__dict__)
                cases = [
                    value for value in vars(test_module).values()
                    if isinstance(value, type)
                    and value is not unittest.TestCase
                    and value.__module__ == module_name
                    and issubclass(value, unittest.TestCase)
                ]
                suite = unittest.TestSuite(
                    unittest.defaultTestLoader.loadTestsFromTestCase(case)
                    for case in cases
                )
                if not cases:
                    print(f"[FAIL] active runtime tests: no test cases in {test_name}")
                    success = False
                    continue
                result = unittest.TextTestRunner(verbosity=1).run(suite)
                success = result.wasSuccessful() and success
            except Exception as exc:
                print(f"[FAIL] active runtime tests: {test_name} raised {type(exc).__name__}")
                success = False
            finally:
                sys.modules.pop(module_name, None)
                for imported in ("prepare_ado_webhook", "normalize_ado_webhook"):
                    sys.modules.pop(imported, None)
    finally:
        sys.path[:] = original_path
    return success


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path, help="ADO router bundle root")
    parser.add_argument("--run-active-tests", action="store_true", help="run bundle tests against $HERMES_HOME/scripts copies")
    args = parser.parse_args()

    bundle = args.bundle.expanduser().resolve()
    active_home = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser().resolve()
    active_scripts = active_home / "scripts"
    ok = True
    for relative in ARTIFACTS:
        ok = _compare(relative, bundle / relative, SKILL_ROOT / relative) and ok
    for relative in RUNTIME_SCRIPTS:
        ok = _compare(f"runtime/{relative}", bundle / "scripts" / relative, active_scripts / relative) and ok
    if args.run_active_tests:
        ok = _run_active_tests(bundle, active_scripts) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

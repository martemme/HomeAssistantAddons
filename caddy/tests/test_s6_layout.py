import unittest
from pathlib import Path


CADDY_DIR = Path(__file__).resolve().parents[1]
S6_ROOT = CADDY_DIR / "rootfs/etc/s6-overlay"
SERVICE_NAMES = ("init-caddy-config", "caddy", "watch-config")


class S6LayoutTests(unittest.TestCase):
    def test_services_are_registered_in_the_s6_user_bundle(self):
        contents = S6_ROOT / "user-bundles.d/user/contents.d"
        self.assertTrue(contents.is_dir(), f"missing S6 user bundle: {contents}")
        for name in SERVICE_NAMES:
            with self.subTest(service=name):
                self.assertTrue((contents / name).is_file())
                self.assertTrue((S6_ROOT / "s6-rc.d" / name / "type").is_file())

    def test_user_bundle_is_not_nested_under_s6_rc_service_directory(self):
        misplaced = S6_ROOT / "s6-rc.d/user-bundles.d"
        self.assertFalse(misplaced.exists(), f"misplaced S6 user bundle: {misplaced}")


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path


CADDY_DIR = Path(__file__).resolve().parents[1]
EXAMPLE = CADDY_DIR / "examples/ado-workitem-webhook.caddy"
ROUTER_PROMPT = CADDY_DIR / "examples/ado-workitem-router/references/ado-webhook-prompt.md"


class AdoWebhookExampleTests(unittest.TestCase):
    def test_example_scopes_public_path_and_rewrites_to_hermes_route(self):
        source = EXAMPLE.read_text(encoding="utf-8")

        self.assertIn("host ai.mt-home.uk", source)
        self.assertIn("path /webhook /webhook/", source)
        self.assertIn("rewrite @ado_workitem_webhook /webhooks/ado-workitems", source)
        self.assertNotIn("password", source.casefold())
        self.assertNotIn("basic_auth", source.casefold())
        self.assertNotIn("header_up", source.casefold())

    def test_router_prompt_includes_the_serialized_prepared_context(self):
        prompt = ROUTER_PROMPT.read_text(encoding="utf-8")

        self.assertIn("{initial_message}", prompt)
        self.assertIn("{agent_context}", prompt)
        self.assertIn("run_mode", prompt)
        self.assertIn("side_effects_allowed", prompt)


if __name__ == "__main__":
    unittest.main()

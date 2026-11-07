# Optional ADO work-item router bundle

This versioned folder contains the `ado-workitem-router` Hermes skill and its tests as copied byte-for-byte from the currently installed skill. It is an optional companion to the generic Caddy add-on; it does not install a listener or receiver and is not required for other Caddy routes.

## Install

1. Copy the complete `ado-workitem-router` directory to `$HERMES_HOME/skills/homelab-ops/ado-workitem-router/`, preserving `SKILL.md`, `references/`, and `scripts/`.
2. Copy `scripts/normalize_ado_webhook.py` and `scripts/prepare_ado_webhook.py` to `$HERMES_HOME/scripts/` so the registered Hermes route can invoke them. Keep those runtime copies byte-identical to this bundle.
3. Register the webhook route with the Hermes webhook adapter and use `references/ado-webhook-prompt.md` as its situational prompt. Follow the active `ado-workitem-router` skill and the applicable `homelab-ops` skill before taking any action. The prepared workflow is read-only and `DRY_RUN` by default.
4. Verify the installation and run the installed skill's tests against the runtime script copies:

   ```bash
   python3 "$HERMES_HOME/skills/homelab-ops/ado-workitem-router/scripts/verify_installation.py" \
     --bundle /path/to/ado-workitem-router --run-active-tests
   ```

The verifier compares the skill, itself, prompt, route scripts, tests, and runtime script copies. Re-run it after every change; do not edit the installed copy without updating this versioned bundle and re-verifying.

## Caddy example

The matching drop-in is `../ado-workitem-webhook.caddy`. Copy it to `/share/caddy/conf.d/ado-workitem-webhook.caddy` only when using the matching ADO example. Configure the generic `ai` Caddy route separately as documented in `../../DOCS.md`; keep Basic Auth credentials separate from the Hermes token header and use HTTPS. The Caddy add-on routes to the existing Hermes webhook adapter; this bundle does not provide an HTTP service.

Never put real credentials in this bundle, a prompt, or the Caddyfile drop-in. Store secrets in Home Assistant's `secrets.yaml` (referenced through Supervisor `!secret` options) and the Hermes runtime's secret store as applicable.

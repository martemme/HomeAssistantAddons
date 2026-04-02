# Changelog

## 1.0.1 - 2026-04-02

- fix: act_runner binary path — official image places binary at `/act_runner`, not `/usr/local/bin/act_runner`
- fix: Dockerfile now symlinks `/act_runner` → `/usr/local/bin/act_runner` at build time
- fix: run.sh now auto-detects binary location at runtime as a fallback safety net

## 1.0.0 - 2026-04-01

- Initial release
- Self-registers to Gitea on first boot using options from HA supervisor
- Persists `.runner` registration file in `/data/` across restarts
- Generates `act_runner_config.yaml` at runtime from configured options
- Docker socket access via `full_access: true` for job container spawning
- Configurable: `gitea_url`, `runner_token`, `runner_name`, `runner_labels`, `log_level`

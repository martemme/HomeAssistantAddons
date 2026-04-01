# Gitea act_runner — Home Assistant Addon

Runs the [Gitea Actions runner](https://gitea.com/gitea/act_runner) as a native Home Assistant addon, allowing your HAOS machine to execute Gitea CI/CD jobs.

---

## Prerequisites

1. A running **Gitea instance** (version ≥ 1.21) with Actions enabled.  
   In Gitea: **Site Administration → Configuration** — confirm `[actions] ENABLED = true`.
2. A **runner registration token** from your Gitea instance (see below).
3. The Gitea instance must be reachable from your HA machine by a **LAN IP address** (e.g. `http://192.168.1.50:3000`), not `localhost`.

---

## Getting the Registration Token

1. Log in to Gitea as a **site administrator**.
2. Navigate to **Site Administration → Actions → Runners**.
3. Click **Create new runner**.
4. Copy the displayed registration token — you will paste it into the addon options.

> **Tip:** Tokens can also be scoped to an organisation or a single repository via the respective *Settings → Actions → Runners* page if you don't want a global runner.

---

## Configuration Options

| Option | Required | Default | Description |
|---|---|---|---|
| `gitea_url` | ✅ | — | Full URL of your Gitea instance, e.g. `http://192.168.1.50:3000` |
| `runner_token` | ✅ | — | Registration token from the Gitea Runners page |
| `runner_name` | | `haos-runner` | Display name shown in Gitea's runner list |
| `runner_labels` | | `ubuntu-latest:docker://catthehacker/ubuntu:act-22.04` | Comma-separated list of labels this runner accepts |
| `log_level` | | `info` | Verbosity: `debug`, `info`, `warn`, or `error` |

---

## Runner Labels Format

Labels tell Gitea which job `runs-on:` values this runner handles, and which Docker image to use for each:

```
<label>:docker://<image>
```

**Examples:**

```
ubuntu-latest:docker://catthehacker/ubuntu:act-22.04
ubuntu-22.04:docker://catthehacker/ubuntu:act-22.04,ubuntu-20.04:docker://catthehacker/ubuntu:act-20.04
```

The label on the left must match the `runs-on:` string in your workflow YAML. Multiple labels are comma-separated.

---

## Why `full_access: true`?

`full_access: true` in the addon manifest mounts `/var/run/docker.sock` inside the container. This is required so `act_runner` can communicate with the host Docker daemon to **spawn and manage job containers** for each CI run.

Without this, the runner starts but will fail every job that uses a `container:` or `docker://` image.

> ⚠️ This grants the addon broad access to the host Docker daemon. Only install this addon if you trust the Gitea instance and the workflow definitions it will run.

---

## Persistent State

The runner's registration file (`.runner`) and the generated runtime config are stored in `/data/` inside the addon, which is **persisted across restarts and updates**. The runner will **not** re-register on every boot.

To force re-registration (e.g. if the token is revoked):
1. Stop the addon.
2. SSH into HAOS and delete `/data/addon_configs/gitea_act_runner/.runner` (exact path may vary).
3. Update the `runner_token` option with a new token.
4. Start the addon.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Runner shows **Offline** in Gitea immediately | `gitea_url` uses `localhost` or `127.0.0.1` | Use the LAN IP of the Gitea machine |
| `[ERROR] runner_token is not configured` | Token field is blank | Paste the token from Gitea Runners page |
| Jobs fail with *"Cannot connect to the Docker daemon"* | `full_access` not effective | Verify the addon config has `full_access: true` and restart |
| Runner registers but jobs stay **Waiting** | Labels mismatch | Ensure workflow `runs-on:` matches a label configured in `runner_labels` |
| Want more detail in logs | — | Set `log_level` to `debug` and restart |

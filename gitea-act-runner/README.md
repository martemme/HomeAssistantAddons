# Home Assistant Add-on: Gitea act_runner

![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]

This add-on runs the **[Gitea Actions runner](https://gitea.com/gitea/act_runner)** natively on your Home Assistant machine, perfect for:

- Running CI/CD pipelines defined in your Gitea repositories
- Building and testing software directly on your home server
- Executing Docker-based job containers without a separate runner host

It self-registers to your Gitea instance on first boot, persists the registration across restarts, and is fully configurable from the HA add-on UI.

## ⚙️ Configuration

```yaml
gitea_url: "http://192.168.1.50:3000"
runner_token: "your-registration-token"
runner_name: "haos-runner"
runner_labels: "ubuntu-latest:docker://catthehacker/ubuntu:act-22.04"
log_level: "info"
```

### Parameters

| Variable        | Default                                                               | Description                                                                                      |
|-----------------|-----------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `gitea_url`     | *(required)*                                                          | Full URL of your Gitea instance. **Must be a LAN IP**, not `localhost`.                          |
| `runner_token`  | *(required)*                                                          | Registration token from Gitea → Site Admin → Actions → Runners → Create new runner.             |
| `runner_name`   | `haos-runner`                                                         | Display name shown in the Gitea runner list.                                                     |
| `runner_labels` | `ubuntu-latest:docker://catthehacker/ubuntu:act-22.04`                | Comma-separated `<label>:docker://<image>` pairs. Must match the `runs-on:` in your workflows.  |
| `log_level`     | `info`                                                                | Verbosity level: `debug`, `info`, `warn`, or `error`.                                            |

## 🚀 Installation

1. Go to Home Assistant → **Settings → Add-ons → Add-on Store**
2. Click **⋮ → Repositories** and add: `https://github.com/martemme/HomeAssistantAddons`
3. Find **Gitea act_runner**, install it
4. Fill in `gitea_url` and `runner_token` in the **Configuration** tab
5. Start the add-on

## 🏃 Getting the Registration Token

1. Log in to Gitea as a **site administrator**
2. Navigate to **Site Administration → Actions → Runners**
3. Click **Create new runner** and copy the token

> Tokens can also be scoped to an organisation or a single repository via the respective *Settings → Actions → Runners* page.

## 🔖 Runner Labels Format

Labels map a workflow `runs-on:` value to a Docker image:

```
<label>:docker://<image>
```

Multiple labels are comma-separated:

```
ubuntu-latest:docker://catthehacker/ubuntu:act-22.04,ubuntu-20.04:docker://catthehacker/ubuntu:act-20.04
```

## 📂 Repository Structure

```
gitea-act-runner/
├── config.yaml     # Add-on definition
├── Dockerfile      # Extends gitea/act_runner:latest
├── run.sh          # Startup & registration script
├── README.md
└── DOCS.md
```

## 🧾 Requirements

- Home Assistant OS or Supervised
- A running Gitea instance (≥ 1.21) with Actions enabled
- Supported architecture: `amd64`, `aarch64`

## 🔒 Security — Why `full_access: true`?

`full_access: true` mounts `/var/run/docker.sock` inside the container so `act_runner` can spawn and manage job containers on the host Docker daemon. Without it, every CI job fails with *"Cannot connect to the Docker daemon"*.

> ⚠️ Only install this add-on if you trust the Gitea instance and the workflow definitions it will run.

## 🛠 Troubleshooting

| Symptom | Fix |
|---|---|
| Runner shows **Offline** in Gitea | Use the LAN IP in `gitea_url`, not `localhost` |
| Jobs fail with *"Cannot connect to Docker"* | Confirm `full_access: true` is present in config and restart |
| Runner registers but jobs stay **Waiting** | Check that `runner_labels` matches the workflow `runs-on:` value |
| Need more detail in logs | Set `log_level` to `debug` and restart |

## Changelog & Releases

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

---

[semver]: http://semver.org/spec/v2.0.0.html
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[repository-badge]: https://img.shields.io/badge/Add%20repository%20to%20my-Home%20Assistant-41BDF5?logo=home-assistant&style=for-the-badge
[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmartemme%2FHomeAssistantAddons

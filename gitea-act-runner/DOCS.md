# Gitea act_runner

Runs the Gitea Actions runner on your Home Assistant machine.  
The runner self-registers on first boot and persists its state across restarts.

## Setup

1. Get a registration token: **Gitea → Site Admin → Actions → Runners → Create new runner**
2. Set `gitea_url` to your Gitea LAN IP, e.g. `http://192.168.1.50:3000` — **not** `localhost`
3. Paste the token into `runner_token`
4. Start the add-on

## Runner Labels

Labels map a workflow `runs-on:` value to a Docker image:

```
ubuntu-latest:docker://catthehacker/ubuntu:act-22.04
```

Multiple labels are comma-separated.

## Persistent State

`.runner` is stored in `/data/` and survives restarts — the runner will not re-register on every boot.  
To force re-registration: stop the add-on, delete `/data/.runner`, update the token, and restart.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Runner **Offline** in Gitea | Use the LAN IP in `gitea_url`, not `localhost` |
| Jobs fail with *"Cannot connect to Docker"* | Ensure `full_access: true` is set and restart |
| Jobs stay **Waiting** | Check `runner_labels` matches the workflow `runs-on:` value |
| Need more detail | Set `log_level: debug` and restart |

Full documentation: [README.md](https://github.com/martemme/HomeAssistantAddons/tree/main/gitea-act-runner)

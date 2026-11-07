# Vector Log Forwarder

Vector Log Forwarder collects log streams directly from the Home Assistant OS (HAOS) system journal and forwards them in real-time to a central **VictoriaLogs** instance using high-performance newline-delimited JSON (`/insert/jsonline`) over HTTP(S) with gzip compression.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Home Assistant OS                    │
│                                                        │
│  ┌───────────────────────┐  ┌───────────────────────┐  │
│  │  HA Core & Supervisor │  │    Docker Add-ons     │  │
│  │   (systemd units)     │  │  (caddy, minio, etc.) │  │
│  └───────────┬───────────┘  └───────────┬───────────┘  │
│              │                          │              │
│              ▼                          ▼              │
│       ┌────────────────────────────────────────┐       │
│       │      systemd-journald on host host     │       │
│       │     (/var/log/journal, /run/log/...)   │       │
│       └───────────────────┬────────────────────┘       │
└───────────────────────────┼────────────────────────────┘
                            │ (Supervisor journald: true)
┌───────────────────────────┼────────────────────────────┐
│ Vector Add-on Container   ▼                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Vector 0.44.0 (journald source -> Remap -> HTTP) │  │
│  └────────────────────────┬─────────────────────────┘  │
└───────────────────────────┼────────────────────────────┘
                            │ gzip NDJSON (/insert/jsonline)
                            ▼
         ┌──────────────────────────────────────┐
         │     VictoriaLogs Central Ingestion   │
         │         http://<host>:9428           │
         └──────────────────────────────────────┘
```

The add-on requires `journald: true` in its add-on manifest (`config.yaml`). Home Assistant Supervisor mounts the host journal into the add-on container as a read-only volume (`/var/log/journal` or `/run/log/journal`).

The startup script (`run.sh`) detects the active journal directory, substitutes configuration variables into `/etc/vector/vector.yaml`, executes a configuration validation check (`vector validate --no-environment`), and launches Vector.

---

## ⚙️ Configuration

Set the following options in the add-on configuration tab:

```yaml
victorialogs_url: "http://10.30.20.20:9428"
host_label: "homeassistant"
```

### Parameters

| Name | Type | Default | Description |
|---|---|---|---|
| `victorialogs_url` | string (url) | `http://10.30.20.20:9428` | Base HTTP or HTTPS URL of the VictoriaLogs ingestion instance. Must not contain paths, query parameters, or credentials. The add-on automatically constructs the target endpoint `.../insert/jsonline?_stream_fields=host,source_type,service&_msg_field=_msg&_time_field=timestamp`. |
| `host_label` | string | `homeassistant` | Identifier assigned to the `host` stream field in VictoriaLogs. Alphanumeric characters, dots, underscores, and hyphens are supported (max 63 chars). |

---

## 📊 Ingestion Schema & Stream Fields

VictoriaLogs organizes logs into **streams** based on low-cardinality metadata fields. The Vector transformation (`transforms.normalize_haos_journal`) normalizes systemd records into the following fields:

### Stream Fields (Indexed for fast scoping)

- `host`: The configured `host_label` (default: `homeassistant`).
- `source_type`:
  - `haos_addon`: Records originating from Docker containers running add-ons (identified by the presence of `CONTAINER_NAME`).
  - `haos_system`: Records originating from HAOS base system services, kernel, systemd units, or core OS components.
- `service`:
  - For containers: The container name (e.g., `homeassistant`, `addon_local_caddy`, `addon_local_minio`).
  - For system services: The `SYSLOG_IDENTIFIER` (e.g., `systemd`, `dockerd`, `NetworkManager`) or `_SYSTEMD_UNIT` (e.g., `systemd-journald.service`), falling back to `system`.

### Message & Timestamp Fields

- `_msg`: The normalized message string extracted from `MESSAGE` or `message` (original field deleted to avoid duplication).
- `_time`: Systemd event timestamp automatically indexed via header `VL-Time-Field: timestamp`.

---

## 🔍 LogsQL Query Recipes

In VictoriaLogs Web UI (`http://<victorialogs>:9428/select/vmui/`) or via API, use these LogsQL queries:

### 1. View all logs from Home Assistant OS
```logsql
host: "homeassistant"
```

### 2. View only Home Assistant Core logs
```logsql
host: "homeassistant" AND service: "homeassistant"
```

### 3. View all Add-on Container logs
```logsql
host: "homeassistant" AND source_type: "haos_addon"
```

### 4. Inspect Caddy Dynamic Ingress Add-on logs
```logsql
host: "homeassistant" AND service: "addon_*caddy*"
```

### 5. Inspect HAOS Systemd and Kernel logs
```logsql
host: "homeassistant" AND source_type: "haos_system"
```

### 6. Filter for Errors and Exceptions across HAOS
```logsql
host: "homeassistant" AND (_msg: "ERROR" OR _msg: "CRITICAL" OR _msg: "Exception" OR _msg: "Traceback")
```

---

## 🛠️ Troubleshooting

### No logs arriving in VictoriaLogs
1. Check add-on logs in **Settings → Add-ons → Vector Log Forwarder → Log**.
2. Verify that `victorialogs_url` is accessible from the Home Assistant host network (check firewall rules, routing, or port 9428 accessibility).
3. Check the warning `No journal files found in /var/log/journal`: verify that Home Assistant OS has persistent or volatile systemd journal files enabled.

### Validating Configuration Locally
From the repository root:
```bash
python3 -m unittest discover -s vector/tests -v
bash ci/scripts/lint_addon.sh ./vector
```

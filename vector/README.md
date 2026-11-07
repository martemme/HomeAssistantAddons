# Home Assistant Add-on: Vector Log Forwarder

![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]
[![Version][version-shield]][changelog]
[![License][license-shield]][license]

Forward **Home Assistant OS**, **Home Assistant Core**, and **Add-on container journal logs** directly to a central **VictoriaLogs** instance using high-performance **Vector 0.44.0**.

![Vector Log Forwarder Banner](logo.png)

---

## 🚀 Features

- **Direct Journal Ingestion**: Reads host and container events from `systemd-journald` via the Supervisor read-only mount (`journald: true`).
- **Zero Host Tampering**: Non-intrusive containerized agent running inside Home Assistant OS.
- **Smart Stream Categorization**:
  - Automatically tags add-on containers with `source_type=haos_addon` and sets `service` to the container name (e.g. `homeassistant`, `addon_local_caddy`).
  - Tags base operating system services with `source_type=haos_system` and resolves `service` from systemd unit or syslog identifier.
- **VictoriaLogs Optimized**: Delivers newline-delimited JSON (`/insert/jsonline`) over HTTP(S) with gzip compression and low-cardinality indexing.
- **High Efficiency**: Extremely low CPU and memory footprint powered by Rust-based Vector runtime.

---

## ⚙️ Configuration

In the Home Assistant add-on **Configuration** tab, specify your VictoriaLogs instance:

```yaml
victorialogs_url: "http://10.30.20.20:9428"
host_label: "homeassistant"
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `victorialogs_url` | `url` | `http://10.30.20.20:9428` | Base HTTP(S) URL of your VictoriaLogs endpoint (without query string or subpaths). |
| `host_label` | `str` | `homeassistant` | Value written to the `host` stream field in VictoriaLogs. |

Detailed configuration and query examples can be found in [DOCS.md](DOCS.md).

---

## 🚀 Installation

1. In Home Assistant, navigate to **Settings → Add-ons → Add-on Store**.
2. Click the three dots **⋮** (top right) → **Repositories**, and add:
   ```
   https://github.com/martemme/HomeAssistantAddons
   ```
3. Locate **Vector Log Forwarder** in the list and click **Install**.
4. In the **Configuration** tab, adjust `victorialogs_url` to match your VictoriaLogs address.
5. Start the add-on and check the **Log** tab to verify connection.

---

## 🔍 Verifying Logs in VictoriaLogs

Once the add-on is running, you can immediately query logs in VictoriaLogs Web UI (`http://<victorialogs-ip>:9428/select/vmui/`):

```logsql
# All events from this Home Assistant instance
host: "homeassistant"

# Filter by specific add-on (e.g. Caddy Ingress)
host: "homeassistant" AND service: "addon_*caddy*"

# Search for errors across all HAOS components
host: "homeassistant" AND (_msg: "ERROR" OR _msg: "Exception")
```

---

## 🧪 Development & Testing

From the repository root:

```bash
# Run unit & contract tests
python3 -m unittest discover -s vector/tests -v

# Run add-on linter
bash ci/scripts/lint_addon.sh ./vector

# Run vector configuration test suite
docker run --rm \
  --volume "$PWD/vector/vector.yaml:/etc/vector/vector.yaml:ro" \
  timberio/vector:0.44.0-debian@sha256:f8933ff1a3ec08df45abc6130947938d98dc85792a25592ec1aa6fe83a7f562c \
  test /etc/vector/vector.yaml
```

---

## 📄 License

MIT License. See [LICENSE](../../LICENSE) for details.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[version-shield]: https://img.shields.io/badge/version-1.0.0-blue.svg
[changelog]: CHANGELOG.md
[license-shield]: https://img.shields.io/badge/license-MIT-blue.svg
[license]: https://github.com/martemme/HomeAssistantAddons/blob/main/LICENSE

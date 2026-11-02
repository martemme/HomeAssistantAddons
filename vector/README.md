# Vector Log Forwarder for Home Assistant OS

This add-on reads the HAOS system journal and forwards it to VictoriaLogs using Vector 0.44.0. With `journald: true`, the Supervisor exposes the host journal read-only inside the add-on; HAOS journal records cover the OS, Supervisor, Home Assistant Core, and add-on containers.

## Options

- `victorialogs_url`: VictoriaLogs base URL; defaults to `http://10.30.20.20:9428`. The add-on appends `/insert/jsonline` and requires an HTTP(S) URL without credentials, path, query, or fragment.
- `host_label`: the `host` field written to VictoriaLogs; defaults to `homeassistant`.

The startup script selects `/var/log/journal` when it contains journal files and falls back to `/run/log/journal`; those mount locations vary by HAOS host. Container journal records with `CONTAINER_NAME` are tagged `source_type=haos_addon` and use that value as `service`. Other journal records are tagged `source_type=haos_system` and use `SYSLOG_IDENTIFIER`, `_SYSTEMD_UNIT`, or `system` as `service`. Both classes are sent as newline-delimited JSON with gzip compression.

The add-on uses the Home Assistant Debian base because Vector's journald source executes `journalctl`, which is not included in the Alpine base. The Vector binary is copied from the same pinned Vector 0.44.0 Debian image used by `monitoring-stack`.

## Validation

From the repository root (the Python environment must have PyYAML, also used by the repository linter):

```sh
python3 -m unittest discover -s vector/tests -v
bash ci/scripts/lint_addon.sh ./vector

docker run --rm \
  --volume "$PWD/vector/vector.yaml:/etc/vector/vector.yaml:ro" \
  timberio/vector:0.44.0-debian@sha256:f8933ff1a3ec08df45abc6130947938d98dc85792a25592ec1aa6fe83a7f562c \
  test /etc/vector/vector.yaml
```

The Dockerfile build also installs `systemd` to provide `journalctl`; do not switch the image to Alpine without replacing the journald reader.

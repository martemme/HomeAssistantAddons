# Changelog

## 1.0.0

- Initial release of Vector Log Forwarder for Home Assistant OS based on Vector 0.44.0.
- Native systemd journal ingestion via Supervisor read-only journald mount (`journald: true`).
- Automatic container and system log classification into VictoriaLogs streams (`host`, `source_type`, `service`).
- High-performance HTTP streaming sink using newline-delimited JSON (`/insert/jsonline`) with gzip compression.
- Home Assistant community standard assets (icon, logo, documentation, and UI translations).
- Pre-flight template validation and comprehensive unit/contract testing suite.

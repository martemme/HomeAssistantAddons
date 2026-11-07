# Martin's Home Assistant Add-ons Repository

## Installation

[![Add repository on my Home Assistant][repository-badge]][repository-url]

If you want to add the repository manually, please follow the procedure highlighted in the [Home Assistant website](https://home-assistant.io/hassio/installing_third_party_addons). Use the following URL to add this repository: `https://github.com/martemme/HomeAssistantAddons`

---

## Active Add-ons

### [Vector Log Forwarder](./vector)

![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]

_Forwards Home Assistant OS, Core, and add-on container journal logs in real-time to VictoriaLogs via Vector 0.44.0._

Detailed documentation, schema, and configuration options are available in [vector/README.md](./vector/README.md) and [vector/DOCS.md](./vector/DOCS.md).

### [Caddy 2 Dynamic Ingress](./caddy)

![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]

_Route configured subdomains to internal services and automatically obtain and renew wildcard TLS certificates via Cloudflare DNS-01. Supports per-route Basic Auth (Argon2id) and private upstream secret headers._

Detailed documentation, configuration options, and integration examples are available in [caddy/README.md](./caddy/README.md) and [caddy/DOCS.md](./caddy/DOCS.md).

### [MinIO](./minio)

![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]

_MinIO is a High Performance Object Storage released under GNU Affero General Public License v3.0. It is API compatible with Amazon S3 cloud storage service._

[Official Repo](https://github.com/minio/minio)

### [NFS Server](./nfs)

![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]
![Supports armv7 Architecture][armv7-shield]

_Expose Home Assistant folders (media, share, config, backup) via NFS to other devices on the network._

---

## ⚠️ Deprecated Add-ons (Dismissione Programmata: 01 Dicembre 2026)

> [!WARNING]
> Gli add-on elencati in questa sezione sono formalmente **deprecati** e verranno **completamente rimossi dal catalogo e dismessi il 01 dicembre 2026**. Non riceveranno ulteriori aggiornamenti o correzioni di sicurezza. Si raccomanda di pianificare la migrazione dei carichi di lavoro.

### [Gitea act_runner](./gitea-act-runner)

[![Status: Deprecated](https://img.shields.io/badge/status-deprecated-critical.svg)](./gitea-act-runner/README.md)
[![Decommission Date](https://img.shields.io/badge/decommission-01%20Dec%202026-orange.svg)](./gitea-act-runner/README.md)
![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]

_Runs the Gitea Actions runner natively on your Home Assistant machine._  
**Nota:** Deprecato e dismesso il 01/12/2026. Migrare su runner standalone o agent pool dedicato.

### [GVM (OpenVAS)](./gvm)

[![Status: Deprecated](https://img.shields.io/badge/status-deprecated-critical.svg)](./gvm/README.md)
[![Decommission Date](https://img.shields.io/badge/decommission-01%20Dec%202026-orange.svg)](./gvm/README.md)
![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]

_OpenVAS full-featured vulnerability scanner inside a Docker container._  
**Nota:** Deprecato e dismesso il 01/12/2026. Migrare le scansioni di vulnerabilità su nodi dedicati.

[Official Repo](https://github.com/greenbone/openvas-scanner)

### [SonarQube](./sonarqube)

[![Status: Deprecated](https://img.shields.io/badge/status-deprecated-critical.svg)](./sonarqube/README.md)
[![Decommission Date](https://img.shields.io/badge/decommission-01%20Dec%202026-orange.svg)](./sonarqube/README.md)
![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]

_SonarQube Server helps you comply with common code security standards (NIST SSDF, OWASP, CWE, STIG, CASA)._  
**Nota:** Deprecato e dismesso il 01/12/2026. Migrare l'analisi statica su server/container dedicato.

[Official Repo](https://github.com/SonarSource/sonarqube)

---

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
[repository-badge]: https://img.shields.io/badge/Add%20repository%20to%20my-Home%20Assistant-41BDF5?logo=home-assistant&style=for-the-badge
[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmartemme%2FHomeAssistantAddons

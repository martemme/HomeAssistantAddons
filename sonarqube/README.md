# Home Assistant Add-on: SonarQube

![Supports amd64 Architecture](https://img.shields.io/badge/amd64-yes-green.svg)
![Supports aarch64 Architecture](https://img.shields.io/badge/aarch64-yes-green.svg)

This add-on provides a **SonarQube** server that helps you comply with common code security standards such as the NIST SSDF, OWASP, CWE, STIG, and CASA. It is designed to be **production-ready**, secure, and lightweight, and integrates seamlessly with Home Assistant.

## ⚙️ Configuration

The add-on uses the following configuration which is defined in the `config.json` file:

```yaml
data_path: /share/sonarqube/data
extensions_path: /share/sonarqube/extensions
ui_port: 9000
jdbc_url: "jdbc:postgresql://sonarqube_db:5432/sonar"
jdbc_username: ""
jdbc_password: ""
TZ: "Europe/Rome"
```

### Parameters

| Variable           | Default                       | Description                                                     |
|--------------------|-------------------------------|-----------------------------------------------------------------|
| `data_path`        | `/share/sonarqube/data`       | Directory where SonarQube data is stored                        |
| `extensions_path`  | `/share/sonarqube/extensions` | Directory for SonarQube extensions                              |
| `ui_port`          | `9000`                        | Port for the SonarQube web interface                            |
| `jdbc_url`         | (Required)                    | JDBC URL for the database connection (e.g., PostgreSQL)         |
| `jdbc_username`    | (Required)                    | Username for the JDBC database connection                       |
| `jdbc_password`    | (Required)                    | Password for the JDBC database connection                       |
| `TZ`               | `Europe/Rome`                 | Timezone setting for the add-on                                 |

## 🚀 Installation

1. Go to Home Assistant → **Supervisor → Add-on Store**
2. Add the repository (Settings → Repositories → `https://github.com/martemme/HomeAssistantAddons`)
3. Install the **SonarQube** add-on
4. Configure the required options and start the add-on

## 🌐 Access

Once installed, access the SonarQube web interface at:

`http://<your-home-assistant-ip>:9000`

## 🧾 Requirements

- Home Assistant OS or Supervised installation
- Supported architectures: `amd64`, `aarch64`
- Persistent storage for `/share/sonarqube/data` and `/share/sonarqube/extensions`
- A running PostgreSQL database for SonarQube connectivity

## 📂 Repository Structure

```bash
sonarqube/
├── CHANGELOG.md       # Changelog for the add-on
├── config.json        # Add-on configuration definition
├── Dockerfile         # Dockerfile for the SonarQube container
├── icon.png           # Icon for the add-on
├── logo.png           # Logo for the add-on
├── README.md          # This file
└── run.sh             # Startup script for SonarQube
```

## 🧠 Notes

- The add-on requires a PostgreSQL database. Ensure that `jdbc_url`, `jdbc_username`, and `jdbc_password` are correctly configured.
- Timezone configuration can be customized via the `TZ` option.
- The Home Assistant add-on system creates the options file (`/data/options.json`) automatically based on your configuration.

## 🛡 Security

> ⚠️ Always use strong passwords and ensure secure network settings, especially for database connections.

---

[semver]: http://semver.org/spec/v2.0.0.html
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
[repository-badge]: https://img.shields.io/badge/Add%20repository%20to%20my-Home%20Assistant-41BDF5?logo=home-assistant&style=for-the-badge
[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmartemme%2FHomeAssistantAddons
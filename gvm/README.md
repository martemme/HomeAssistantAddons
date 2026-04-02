# Home Assistant Add-on: GVM (OpenVAS) 

![Supports amd64 Architecture](https://img.shields.io/badge/amd64-yes-green.svg)
![Supports aarch64 Architecture](https://img.shields.io/badge/aarch64-yes-green.svg)

This Home Assistant add-on deploys the GVM (OpenVAS) vulnerability scanner inside a Docker container.

## 🚀 Features

- Full GVM Scanner in a managed container
- Web UI available on port `9392`
- Username and password configurable from UI

## ⚙️ Configuration

Example `options` in `config.json`:

```json
{
    "username": "admin",
    "password": "changeme",
    "ui_port": 9392,
    "TZ": "Europe/Rome",
    "HTTPS": "false",
    "SSHD": "true",
    "DB_PASSWORD": "changeme"
}
```

## 🌐 Access

Once installed, access the GVM web interface at:

`http://<your-home-assistant-ip>:9392`

## 📂 Repository Structure

```bash
gvm/
├── CHANGELOG.md       # Changelog for the add-on
├── config.json        # Add-on configuration definition
├── Dockerfile         # Dockerfile for the GVM container
├── icon.png           # Icon for the add-on
├── logo.png           # Logo for the add-on
├── README.md          # This file
└── run.sh             # Startup script for GVM
```

## 🛡 Security

> ⚠️ Always use strong passwords and ensure secure network settings.

---

[semver]: http://semver.org/spec/v2.0.0.html
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
[repository-badge]: https://img.shields.io/badge/Add%20repository%20to%20my-Home%20Assistant-41BDF5?logo=home-assistant&style=for-the-badge
[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmartemme%2FHomeAssistantAddons
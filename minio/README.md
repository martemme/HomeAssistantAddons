# Home Assistant Add-on: MinIO

![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]

This add-on provides an **S3-compatible** server based on MinIO, perfect for:

- File/media storage
- Logging or custom integrations

It is designed to be **production-ready**, secure, lightweight, and accessible directly via the Home Assistant sidebar.

## ⚙️ Configuration

```yaml
access_key: admin
secret_key: CHANGEME-strong-password
drive: storage
```

### Parameters

| Variable        | Default     | Description                                           |
|-----------------|-------------|-------------------------------------------------------|
| `access_key`    | `admin`     | MinIO user credential                                 |
| `secret_key`    | `admin`     | MinIO password credential                             |
| `drive`         | `storage`   | Folder where MinIO data will be saved inside `/data`  |

## 🚀 Installation

1. Go to Home Assistant → **Supervisor → Add-on Store**
2. Add this repository (Settings → Repositories → `https://github.com/martemme/HomeAssistantAddons`)
3. Install the add-on, configure the credentials and start it

## 🌐 Access

Once installed, access MinIO via the sidebar or at:

`http://<ip_hass>:9000` (if Ingress is not available)

## 🧾 Requirements

- Home Assistant OS or Supervised
- Supported architecture: `amd64`, `aarch64`
- Access to a persistent folder for `/data`

## 📂 Repository Structure

```bash
minio/
├── config.json         # Add-on definition
├── Dockerfile          # MinIO container
├── run.sh              # Startup script
├── README.md
└── ...
```

## 🧠 Notes
The credentials are passed as environment variables during bootstrap.
The container is based on `alpine:3.18` image

## 🛡 Security
> ⚠️ Always use strong passwords.

Consider enabling automatic TLS by placing certificates in `/ssl/`.

## Changelog & Releases

Releases are based on [Semantic Versioning][semver], and use the format
of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented
based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

---
Made with ❤️ for automation and resilience.

[semver]: http://semver.org/spec/v2.0.0.html
[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
[repository-badge]: https://img.shields.io/badge/Add%20repository%20to%20my-Home%20Assistant-41BDF5?logo=home-assistant&style=for-the-badge
[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmartemme%2FHomeAssistantAddons
# Home Assistant Add-on: MinIO

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]

This add-on provides an **S3-compatible** server based on MinIO, perfect for:

- File/media storage
- Logging or custom integrations

It is designed to be **production-ready**, secure, lightweight, and accessible directly via the Home Assistant sidebar.

## ⚙️ Configuration

```yaml
access_key: admin
secret_key: CHANGEME-strong-password
region: us-east-1
bucket: backup
```

## 🌐 Access

Once installed, access MinIO via the sidebar or at:

`http://<ip_hass>:9000` (if Ingress is not available)

## 🚀 Installation

1. Go to Home Assistant → **Supervisor → Add-on Store**
2. Add your custom Git repository (Settings → Repositories → `https://github.com/<your-username>/minio-addon`)
3. Install the add-on, start it, and access MinIO via Ingress

## 🧾 Requirements

- Home Assistant OS or Supervised
- Supported architecture: `amd64`, `aarch64`
- Access to a persistent folder for `/data`

## 📂 Repository Structure

```bash
minio-addon/
├── config.json         # Add-on definition
├── Dockerfile          # MinIO container
├── run.sh              # Entry point with TLS support and auto-creation of buckets
├── README.md
└── ...
```

## 🧠 Notes
The bucket specified in `bucket:` is automatically created if it does not exist.

If you use Longhorn, you can point backups to:

```bash
http://<IP_HASS>:9000/longhorn-backup
```

The credentials are passed as environment variables during bootstrap.

## 🛡 Security
> ⚠️ Always use strong passwords.

Consider enabling automatic TLS by placing certificates in `/ssl/`.

## ✅ Future TODOs
- Support for bucket versioning
- Healthcheck and Prometheus metrics
- Interface for managing users/buckets via options

---
Made with ❤️ for automation and resilience.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
[repository-badge]: https://img.shields.io/badge/Add%20repository%20to%20my-Home%20Assistant-41BDF5?logo=home-assistant&style=for-the-badge
[repository-url]: https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmartemme%2FHomeAssistantAddons
# Home Assistant Add-on: NFS Server

![Supports amd64 Architecture][amd64-shield]
![Supports aarch64 Architecture][aarch64-shield]
![Supports armv7 Architecture][armv7-shield]

This add-on provides a **user-space NFS server** based on unfs3, perfect for:

- Mounting Home Assistant folders on other machines on your network
- Sharing media, config, or backup folders over NFS

It is designed to be **lightweight and kernel-independent**, running entirely in user-space without requiring NFS kernel modules.

## Configuration

```yaml
shares:
  - folder: media
    allowed_network: 192.168.1.0/24
    read_only: false
```

### Parameters

| Variable                    | Default             | Description                                                        |
|-----------------------------|---------------------|--------------------------------------------------------------------|
| `shares[].folder`           | `media`             | HA folder to export (`media`, `share`, `config`, `backup`)        |
| `shares[].allowed_network`  | `192.168.1.0/24`    | Network(s) allowed to access the share. Comma-separated for multiple (e.g. `192.168.1.0/24, 10.0.0.0/8`) |
| `shares[].read_only`        | `false`             | Whether the share is read-only                                     |

You can define multiple shares:

```yaml
shares:
  - folder: media
    allowed_network: 192.168.1.0/24
    read_only: false
  - folder: share
    allowed_network: 192.168.1.0/24
    read_only: false
  - folder: config
    allowed_network: 192.168.1.10/32
    read_only: true
```

## Installation

1. Go to Home Assistant → **Supervisor → Add-on Store**
2. Add this repository (Settings → Repositories → `https://github.com/martemme/HomeAssistantAddons`)
3. Install the add-on, configure your shares and start it

## Usage

Once started, mount a share from a client machine.

Example on Linux:
```bash
mkdir /mnt/hass-media
mount -t nfs <home-assistant-ip>:/media /mnt/hass-media
```

Example on macOS:
```bash
mkdir /mnt/hass-media
mount -t nfs -o resvport <home-assistant-ip>:/media /mnt/hass-media
```

## Requirements

- Home Assistant OS or Supervised
- Supported architecture: `amd64`, `aarch64`, `armv7`
- NFS kernel modules are **not** required (uses unfs3 user-space server)

## Notes

> ⚠️ Always restrict `allowed_network` to your local subnet. Avoid using `0.0.0.0/0` in production.

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

# Changelog

## 1.0.5 - 2026-03-31

- fix: switch to unfs3 user-space NFS server (kernel nfsd not available on HA OS)
- fix: remove unneeded SYS_ADMIN/SYS_MODULE/kernel_modules (not required with unfs3)

## 1.0.3 - 2026-03-31

- feat: support multiple configurable NFS shares (folder, allowed_network, read_only)
- fix: add hassio_api access so bashio can read addon config
- fix: mount nfsd filesystem before starting rpc.nfsd
- fix: use correct HA base images in build_from

## 1.0.0 - 2026-03-29

- Initial release

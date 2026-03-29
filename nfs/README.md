# Home Assistant Add-on: NFS Server

This add-on exposes the Home Assistant media folder via NFS.

## Configuration

The following configuration options are available:

- `allowed_network`: The network allowed to access the NFS share (e.g., `192.168.1.0/24`). Defaults to `0.0.0.0/0` (everyone). It is highly recommended to restrict this to your local network.

## How to use

1.  Start the add-on.
2.  On your client machine, mount the NFS share. The NFS share will be the IP of your Home Assistant instance, and the exported path is `/media`.

    Example on a Linux client:
    ```bash
    mkdir /mnt/hass-media
    mount -t nfs <home-assistant-ip>:/media /mnt/hass-media
    ```

## Notes

This addon requires `host_network` and `SYS_ADMIN` privileges to run.

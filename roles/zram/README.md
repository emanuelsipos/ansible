# zram

Configure compressed RAM swap on Debian/Proxmox VE hosts using
[`systemd-zram-generator`](https://github.com/systemd/zram-generator). Writes a
templated `/etc/systemd/zram-generator.conf`, optionally manages `vm.swappiness`
via a dedicated `sysctl` drop-in, and safely activates previously inactive
devices.

## Requirements

- `community.general` collection for loading the `zram` kernel module.
- `ansible.posix` collection for `vm.swappiness` management when
  `zram_manage_swappiness` is `true`.
- A real kernel. `systemd-zram-generator` is a no-op inside containers (it checks `systemd-detect-virt --container`), so this role configures, but does not activate, zram in LXC/Docker. It is intended for the Proxmox VE **host** nodes.

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `zram_package` | `systemd-zram-generator` | Package providing the generator |
| `zram_config_file` | `/etc/systemd/zram-generator.conf` | Generator config path |
| `zram_devices` | one `zram0` device (see below) | Dict of devices, keyed by `zramN`; each becomes a `[zramN]` section |
| `zram_manage_swappiness` | `true` | Write `vm.swappiness` to a drop-in; set `false` to manage it elsewhere |
| `zram_swappiness` | `10` | Value for `vm.swappiness` when managed here |
| `zram_sysctl_drop_in_file` | `/etc/sysctl.d/99-zram.conf` | Drop-in file for the swappiness setting |

### `zram_devices` keys

Per device, only `zram_size` is required; every other key is emitted only when set.

| Key | Maps to | Notes |
|-----|---------|-------|
| `zram_size` | `zram-size` | Expression over `ram` (MemTotal in MiB), e.g. `ram * 0.25` or `min(ram / 2, 8192)` |
| `compression_algorithm` | `compression-algorithm` | e.g. `zstd`, `lz4` |
| `swap_priority` | `swap-priority` | Omit for a filesystem device |
| `writeback_device` | `writeback-device` | Block device for incompressible pages |
| `host_memory_limit` | `host-memory-limit` | MiB; skip the device above this much RAM |
| `fs_type` / `mount_point` | `fs-type` / `mount-point` | Format/mount instead of using as swap |
| `options` | `options` | swapon/mount options |

Default:

```yaml
zram_devices:
  zram0:
    zram_size: "ram * 0.25"
    compression_algorithm: zstd
    swap_priority: 100
```

## Usage

```yaml
- hosts: pve
  become: true
  roles:
    - role: zram
```

Override the size (e.g. cap a large-RAM host at 8 GiB) and keep swappiness elsewhere:

```yaml
- hosts: pve
  become: true
  roles:
    - role: zram
      vars:
        zram_devices:
          zram0:
            zram_size: "min(ram / 4, 8192)"
            compression_algorithm: zstd
            swap_priority: 100
        zram_manage_swappiness: false
```

## How it works

1. Installs `systemd-zram-generator`.
2. Detects whether it is running in a container (where the generator is inert).
3. Loads the `zram` kernel module on real hosts.
4. Renders `zram_devices` into `/etc/systemd/zram-generator.conf`.
5. Regenerates systemd units when the package or configuration changes.
6. Starts inactive `dev-zramN.swap` units and leaves active swap untouched.
7. Optionally writes `vm.swappiness` to its own `sysctl` drop-in.

Changes to the size or compression algorithm of an active device are written to
configuration but are not applied by restarting swap automatically. They take
effect on the next reboot. This avoids forcing `swapoff` on a host that might
not have enough free memory to absorb the compressed pages.

## License

MIT

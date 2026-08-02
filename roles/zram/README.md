# zram

Configure compressed RAM swap on Debian/Proxmox VE hosts using
[`systemd-zram-generator`](https://github.com/systemd/zram-generator). Writes a
templated `/etc/systemd/zram-generator.conf`, optionally manages `vm.swappiness`
via a dedicated `sysctl` drop-in, and applies changes at runtime without a reboot.

## Requirements

- `ansible.posix` collection (`ansible-galaxy collection install ansible.posix`) — only needed when `zram_manage_swappiness` is `true`.
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
3. Renders `zram_devices` into `/etc/systemd/zram-generator.conf`.
4. On change, reloads systemd (regenerating the `dev-zramN.swap` units) and restarts each device's swap unit — skipped in containers, where a reboot on a real host would be required instead.
5. Optionally writes `vm.swappiness` to its own `sysctl` drop-in.

## License

MIT

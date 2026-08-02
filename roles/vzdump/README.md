# vzdump

Manages `exclude-path` entries and global configuration settings in `/etc/vzdump.conf` on Proxmox VE hosts.

Prevents vzdump from backing up large ephemeral directories (Docker overlay2, containerd layer stores, OS caches) inside LXC containers, keeping backup sizes sane and avoiding snapshot errors. It also applies host-level performance tuning (I/O limits, CPU threads).

## Requirements

Must run on Proxmox VE hosts (the `pve` group). `/etc/vzdump.conf` is a Proxmox-native file — applying this role to non-PVE hosts is harmless but purposeless.

## Role Variables

| Variable                     | Default | Description                                                           |
| ---------------------------- | ------- | --------------------------------------------------------------------- |
| `vzdump_extra_exclude_paths` | `[]`    | List of additional paths to append to the default exclude list.       |
| `vzdump_extra_config`        | `{}`    | Dictionary of additional key/value pairs to merge into `vzdump.conf`. |

### Defaults

The role ships with a comprehensive set of defaults optimized for Docker-heavy LXC workloads:

```yaml
# defaults/main.yml
vzdump_default_config:
  bwlimit: 102400
  ionice: 7
  zstd: 4
  lockwait: 10

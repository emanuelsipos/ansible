# sysctl

A generic role to apply arbitrary `sysctl` settings via drop-in files under `/etc/sysctl.d/`. Optionally loads and persists kernel modules required for those settings.

## Requirements

- `ansible.posix` collection (`ansible-galaxy collection install ansible.posix`)
- `community.general` collection (`ansible-galaxy collection install community.general`)

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `sysctl_settings` | `{}` | Dict of `sysctl` key/value pairs to apply |
| `sysctl_drop_in_file` | `/etc/sysctl.d/99-custom.conf` | Path to the drop-in file to write settings into |
| `sysctl_modules` | `[]` | List of kernel modules to load (and persist across reboots) before applying settings |

## Usage

### Basic — apply arbitrary sysctl settings

```yaml
- hosts: servers
  become: true
  roles:
    - role: sysctl
      vars:
        sysctl_settings:
          net.ipv4.ip_forward: "1"
          vm.swappiness: "10"
        sysctl_drop_in_file: /etc/sysctl.d/99-custom.conf
```

### With kernel module loading (e.g. BBR)

```yaml
- hosts: machines
  become: true
  roles:
    - role: sysctl
      vars:
        sysctl_settings:
          net.core.default_qdisc: fq
          net.ipv4.tcp_congestion_control: bbr
        sysctl_drop_in_file: /etc/sysctl.d/99-networking.conf
        sysctl_modules:
          - tcp_bbr
```

### Multiple invocations in the same play (using `include_role`)

The role supports being called multiple times with different drop-in files, for example
to keep networking and PVE-specific settings in separate files:

```yaml
- hosts: pve
  become: true
  tasks:
    - ansible.builtin.include_role:
        name: sysctl
      vars:
        sysctl_settings: "{{ pve_sysctl_settings }}"
        sysctl_drop_in_file: /etc/sysctl.d/99-pve.conf

    - ansible.builtin.include_role:
        name: sysctl
      vars:
        sysctl_settings:
          net.ipv4.tcp_congestion_control: bbr
        sysctl_drop_in_file: /etc/sysctl.d/99-networking.conf
        sysctl_modules:
          - tcp_bbr
```

## How it works

1. Loads each module listed in `sysctl_modules` with `modprobe` and writes a file to `/etc/modules-load.d/` so it persists across reboots.
2. Applies each setting in `sysctl_settings` to `sysctl_drop_in_file` using `ansible.posix.sysctl`.
3. Notifies a handler that runs `sysctl --system` to reload all drop-in files.

## License

MIT

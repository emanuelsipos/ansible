# apt_archive_policy

Disables retention of downloaded APT package archives on Debian-family hosts and
optionally removes archives already present in the APT cache.

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `apt_archive_policy_clean_existing` | `false` | Run a guarded one-time `apt-get clean` after writing the policy |

## Usage

```yaml
- hosts: all
  become: true
  roles:
    - role: apt_archive_policy
```

The role manages `/etc/apt/apt.conf.d/99-apt-archive-policy` with both APT
settings required for command-line and library-based APT package downloads. It
fails on non-Debian-family hosts. Existing archives are cleaned only when no
APT, dpkg, unattended-upgrade, or APT systemd transaction is active. Cleanup is
an explicit maintenance opt-in and is skipped in Ansible check mode. Tasks use
the `base` and `apt` tags.

To remove existing archives during a controlled maintenance run:

```yaml
apt_archive_policy_clean_existing: true
```

## License

MIT

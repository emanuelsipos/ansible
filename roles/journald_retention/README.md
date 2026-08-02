# journald_retention

Configures `systemd-journald` retention settings via a drop-in file, and vacuums old logs immediately.

## Requirements

None. Uses only the `ansible.builtin` module namespace.

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `journald_retention_days` | `7` | Maximum age of log entries (days) |
| `journald_retention_system_max_use` | `250M` | Maximum disk space used by the journal |
| `journald_retention_storage` | `persistent` | Journal storage mode (`volatile`, `persistent`, `auto`, `none`) |

## Usage

```yaml
- hosts: all
  become: true
  roles:
    - journald_retention
```

With custom values:

```yaml
- hosts: all
  become: true
  roles:
    - role: journald_retention
      vars:
        journald_retention_days: 90
        journald_retention_system_max_use: 5G
```

## What it does

1. Creates `/etc/systemd/journald.conf.d/` if it doesn't exist.
2. Writes `/etc/systemd/journald.conf.d/retention.conf` with `MaxRetentionSec`, `SystemMaxUse`, and `Storage`.
3. Notifies a handler to restart `systemd-journald`.
4. Runs `journalctl --vacuum-time` immediately to enforce the retention on existing logs.

## License

MIT

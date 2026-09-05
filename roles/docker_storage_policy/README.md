# Docker storage policy

This role installs two independent policies on Komodo-managed Docker hosts:

- A daily report of Docker's estimated image, container, volume, and build-cache
  totals and their change since the previous report.
- A weekly `docker builder prune --force --filter until=168h` job.

Container writable layers larger than 1 GiB fail the report service by default,
which leaves a warning in journald while preserving the report state. Dangling
volumes are listed with their labels and mountpoints but are never deleted.

## Prune ownership

- Ansible owns aged build-cache pruning only.
- Docker image pruning is intentionally disabled. Komodo 2.3.3 implements its
  `PruneImages` action as `docker image prune -a -f` without an age filter or
  rollback-image protection.
- Docker volume pruning remains a manual, ownership-aware operation.

The report and build-cache jobs share a lock so their Docker storage operations
cannot run concurrently.

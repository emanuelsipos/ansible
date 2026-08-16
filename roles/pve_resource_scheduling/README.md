# pve_resource_scheduling

Automatically cycle ZFS pool scrubs on selected PVE hosts. Scrubs are a
pool-level ZFS operation, not a dataset-level operation. The role installs one
service, timer, and launcher per configured host; the launcher discovers
healthy pools at runtime and starts at most one overdue pool per timer run.

```yaml
pve_resource_scheduling_scrub_policies:
  io:
    calendar: "*-*-* 05:00:00"
    cycle_days: 28
```

The daily 05:00 timer uses `Persistent=false`, so it does not replay a missed
check at boot. `cycle_days` must be between 21 and 42 days; the configured
28-day target is measured start-to-start for each pool. The launcher derives
the minimum global spacing by dividing that cycle by the number of currently
`ONLINE` pools. For example, four healthy pools are spaced by roughly seven
days; daily evaluation supplies at most one day of additional granularity.
In steady state, that is equivalent to `pool A -> 7 days -> pool B -> 7 days ->
pool C -> 7 days -> pool D -> 7 days -> repeat`, with the oldest due pool taking
the next boundary. One scheduler is used instead of generated per-pool cron
entries, so adding or removing a pool adjusts the spacing automatically.

The pool with no previous completed scrub, or the oldest completed scrub, is
selected after its own cycle is due. It starts only when the most recent scan
start among healthy pools is at least the derived spacing old. A completed
resilver or other scan therefore delays the next start without making its pool
look scrubbed. The launcher reads ZFS scan history directly and keeps no custom
scheduling state.

The launcher skips without stopping anything when another scrub or resilver is
active or paused. The 28-day cycle is a target, not a deadline: a long scrub can
make another pool late rather than causing two automatic scrubs to compete for
host or controller I/O. Resilvers always take precedence. Only pools currently
reporting `ONLINE` are eligible. If the launcher cannot read or validate an
eligible pool's scan status, it skips that run rather than launching from
incomplete scheduling information.

The replacement timer is enabled before the role sets
`org.debian:periodic-scrub=disable` on every currently discovered pool.
Migration of former fixed-pool units is an explicit operational step. Removing
a host from policy is intentionally not automated because the local Debian
scrub property must be restored as part of decommissioning.

The role uses only `ansible.builtin` modules and expects `zfs`, `zpool`, Python
3, systemd, `date`, and `flock` on configured hosts.

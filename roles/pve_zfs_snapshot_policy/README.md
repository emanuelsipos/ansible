# pve_zfs_snapshot_policy

Apply explicit, inventory-driven `zfs-auto-snapshot` policy to PVE datasets.
The role contains no host, pool, dataset, profile, schedule, or retention
choices. Reusable profiles and common/host-specific dataset mappings are
defined in `group_vars` or `host_vars`.

```yaml
pve_zfs_snapshot_policy_tiers:
  hourly:
    schedule: "17 * * * *"
    keep: 24

pve_zfs_snapshot_policy_profiles:
  guest:
    hourly: true

pve_zfs_snapshot_policy_common_datasets:
  rpool/data: guest

pve_zfs_snapshot_policy_host_datasets:
  storage-node:
    tank/content: bulk
```

Host-specific mappings override common mappings. Dataset properties inherit to
descendants, so a policy root such as `rpool/data` covers newly created guest
disks. The prune helper uses the longest matching policy root, allowing a child
dataset to override its parent profile.

Every configured dataset must exist locally. The role fails on unknown profiles,
unsafe names, incomplete profile tiers, a hostname mismatch, or a missing
`zfs-auto-snapshot` executable. It does not install packages because PVE package
changes are restricted to controlled maintenance.

The role clears local `com.sun:auto-snapshot` overrides and sets every configured
tier property explicitly. Tier properties are authoritative because the single
cron file uses `--default-exclude`; unclassified datasets therefore receive no
automatic snapshots. All five package cron files are preserved under local
`dpkg-divert` paths ending in `.distrib`, preventing package upgrades from
restoring duplicate jobs. Remove those diversions explicitly when
decommissioning the role.

Creation jobs pass `--skip-scrub`, so a pool with an active scrub is excluded
without pausing snapshot creation on other pools.

`pve_zfs_snapshot_policy_host_activation` is empty by default, so every host is
inactive and deployment only reports bounded prune candidates. Each configured
inventory hostname must contain exactly the boolean `creation_enabled` and
`prune_enabled` values. Creation can be staged before retention; pruning always
requires creation. For example, the PVE group enables creation and retention on
reviewed host `io`, leaving `europa` and unlisted future hosts inactive:

```yaml
pve_zfs_snapshot_policy_host_activation:
  io:
    creation_enabled: true
    prune_enabled: true
```

Do not add another host until its report and short creation-only stage have been
reviewed. The prune calendar is used only where local pruning is enabled. It is
implemented as a non-persistent systemd timer so a reboot does not launch a
catch-up cleanup alongside guest startup, backups, or scrubs.

An immediate cleanup additionally requires local pruning to be enabled and:

```yaml
pve_zfs_snapshot_policy_prune_now: true
```

The locked helper is the only component that performs retention deletion. It
recognizes only snapshots named
`zfs-auto-snap_<configured-tier>-...`. Proxmox `__base__` and `__replicate_*`
snapshots, plus manually named snapshots, are outside that namespace and remain
untouched. It never uses recursive or forced destruction. Held, cloned, or
otherwise undeletable snapshots are reported as per-snapshot skips. Before any
deletion, it identifies candidate pools with an active or paused scrub/resilver
and skips their candidates. Scheduled execution deletes at most
`pve_zfs_snapshot_policy_prune_max_candidates` candidates per run and continues
past expected busy, held, cloned, or already-missing snapshots. Unexpected
destruction errors remain visible through a nonzero service result. The helper
holds the automatic scrub launcher's lock from scan inspection through deletion,
preventing a new managed scrub from starting during the operation.

`--preflight` performs bounded dry-run checks without deletion, and
`--expect-manifest-sha256` can bind a manual operation to the candidate-name
digest printed by the helper. Use `--max-candidates` explicitly for a larger
supervised catch-up. The scheduled service writes concise counters to the
systemd journal instead of generating cron mail. A false tier keeps zero
automatic snapshots for that tier once pruning is explicitly enabled.

Direct `zpool scrub` commands do not participate in this advisory lock. Do not
start one during the prune window; use
`flock --exclusive /run/lock/pve-zfs-scrub.lock zpool scrub <pool>` for a manual
start so it coordinates with managed pruning.

Deploy a node through Semaphore or locally with:

```bash
ansible-playbook -i <inventory> playbooks/all-hosts/playbook.yml \
  --limit <node> --tags snapshots
```

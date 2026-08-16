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

Pruning is disabled by default. With
`pve_zfs_snapshot_policy_report_prune_candidates: true`, deployment reports a
bounded list without deleting anything. Enable scheduled retention only after
reviewing that report:

```yaml
pve_zfs_snapshot_policy_prune_enabled: true
pve_zfs_snapshot_policy_prune_schedule: "10 4 * * *"
```

An immediate cleanup additionally requires:

```yaml
pve_zfs_snapshot_policy_prune_now: true
```

The locked helper is the only component that performs retention deletion. It
recognizes only snapshots named
`zfs-auto-snap_<configured-tier>-...`. Proxmox `__base__` and `__replicate_*`
snapshots, plus manually named snapshots, are outside that namespace and remain
untouched. It never uses recursive or forced destruction. Held, cloned, or
otherwise undeletable snapshots are reported as failures. A false tier keeps
zero automatic snapshots for that tier once pruning is explicitly enabled.

Deploy a node through Semaphore or locally with:

```bash
ansible-playbook -i <inventory> playbooks/all-hosts/playbook.yml \
  --limit <node> --tags snapshots
```

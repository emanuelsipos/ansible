# pve_maintenance

`playbooks/pve-maintenance/playbook.yml` deliberately accepts exactly one PVE
host. It always refreshes indexes and runs a no-removal simulation; it runs no
package upgrade unless the extra variable is a typed boolean:

```bash
ansible-playbook -i hosts playbooks/pve-maintenance/playbook.yml \
  --limit io -e '{"pve_maintenance_execute": true, "pve_maintenance_planned_singleton_fencing_ack": true}'
```

Use this playbook rather than invoking an upgrade command directly. Maintenance
passes `--no-remove` and rejects any simulated package removal, including kernel
removal. It also refuses to run unless the controlled PVE timer, index-refresh,
package-download, and autoclean policy is effective. The real package mutation
runs synchronously so a controller deadline cannot terminate dpkg mid-upgrade.

The role makes its fail-closed lock with `mkdir /etc/pve/priv/.pve-maintenance.lock`.
Molecule can only exercise ordinary filesystem semantics, not pmxcfs. The
following test was observed on 2026-08-14 on the current idle, quorate jupiter
cluster; it creates this exact directory once, confirms a second `mkdir` fails,
and removes only that empty directory:

```bash
pvecm status && mkdir --mode=0700 /etc/pve/priv/.pve-maintenance.lock && ! mkdir /etc/pve/priv/.pve-maintenance.lock && rmdir /etc/pve/priv/.pve-maintenance.lock && pvecm status
```

The canonical PVE group variable records that validation. The assertion remains
in the role, so an override to false still blocks execute mode. An existing lock
always blocks; inspect it and remove it manually only after confirming that no
maintenance run owns it.

Execute mode retains that lock if the upgrade or postflight fails. This prevents
the peer-reboot timer or another maintenance run from acting on a partially
configured host. Inspect package state and remove the lock manually only after
the failure is resolved.

## Planned singleton maintenance

The current `group_vars/pve.yml` temporarily sets
`pve_maintenance_cluster_safety_mode: planned_singleton`,
`pve_maintenance_planned_singleton_node: io`, and
`pve_maintenance_planned_singleton_peer: europa`. This narrowly permits a
report while static membership still contains both nodes, only `io` is online,
`two_node=1` remains configured, and `pvecm status` reports one node and one
expected and total vote. A report run needs no extra variables: inventory
selects this mode.

If the offline peer has been physically powered off and cannot rejoin, an
operator may temporarily run `pvecm expected 1` on `io` to establish the
required live quorum. That is a manual, transient cluster operation; this role
never runs it or changes cluster membership. Execute mode additionally requires
both `pve_maintenance_pmxcfs_atomic_lock_validated` and
`pve_maintenance_planned_singleton_pmxcfs_atomic_lock_validated` to be true,
plus the typed, per-run
`pve_maintenance_planned_singleton_fencing_ack: true`. The acknowledgement
must never be saved as enabled in inventory.

The singleton pmxcfs check was observed on `io` on 2026-08-17 with exact
`io`-only quorum and static `europa,io` membership. It repeated the first
`mkdir`, second-`mkdir` failure, and empty `rmdir` sequence above and verified
that the singleton quorum state remained unchanged before and after.

In this mode, a simulated install or configuration of `corosync`, `pve-cluster`,
or another quorum-stack package is rejected before execution. The exception is
only for `pve_maintenance`; peer reboot remains disabled and subject to the
normal strict two-node safety expectations. Change inventory back to
`strict_two_node` before `europa` is powered on or otherwise allowed to rejoin.
Only then remove the physical fence under the manual cluster recovery procedure.
Verify `/cluster/status` reports both nodes online and run a strict report that
proves `Nodes: 2`, `Expected votes: 2`, `Total votes: 2`, and `Quorate: Yes`
before scheduling or executing normal two-node maintenance.

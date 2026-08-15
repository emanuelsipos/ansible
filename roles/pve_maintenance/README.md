# pve_maintenance

`playbooks/pve-maintenance/playbook.yml` deliberately accepts exactly one PVE
host. It always refreshes indexes and runs a no-removal simulation; it runs no
package upgrade unless the extra variable is a typed boolean:

```bash
ansible-playbook -i hosts playbooks/pve-maintenance/playbook.yml \
  --limit europa -e '{"pve_maintenance_execute": true}'
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

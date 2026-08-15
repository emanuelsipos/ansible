# pve_peer_reboot

This opt-in role installs a root-only, local systemd service and timer. It does
not install packages, migrate guests, or SSH to the peer. The timer is Saturday
06:30 plus up to ten minutes on europa, and Sunday 06:30 plus up to ten minutes
on io. Missed windows do not catch up after boot. The script fails closed unless both
nodes are healthy and online, quorum is present, no maintenance/tasks/package
activity/backup/replication is active, and every running local guest has
`onboot=1`.

Before rebooting, the node atomically claims the same pmxcfs directory used by
PVE maintenance and records the currently running local guests. That reservation
survives the reboot and blocks both nodes from entering maintenance or reboot at
the same time. A recovery timer releases it only after the owner node rejoins a
healthy cluster, required PVE services are active, and the recorded guests are
running again.

Enabling the role also requires the canonical pmxcfs atomic-lock validation
flag. It records the same live `mkdir`/second-`mkdir`/`rmdir` check required by
execute-mode PVE maintenance.

There is no QDevice; the two-node cluster relies on `two_node=1`. Rebooting io
temporarily takes down Semaphore, PBS, and data3. Keep the first real reboot
observed before setting `pve_peer_reboot_enabled: true`. To stop the emergency
timer on a node after it has been enabled, set `pve_peer_reboot_enabled: false`
and rerun the role. Role convergence disables the reboot-request timer while
installing and enabling the recovery path so any existing reservation can still
be released safely.

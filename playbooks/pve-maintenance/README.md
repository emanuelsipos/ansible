# PVE maintenance playbook

Create separate Semaphore templates for report and execute runs, each limited
to one node (`europa` or `io`). The execute templates remain **unscheduled**.
While `group_vars/pve.yml` selects the planned-singleton mode, use `io` only.
The report template supplies no extra variables: the inventory already enables
the planned mode. After physical fencing is confirmed and both recorded pmxcfs
atomic-lock validations are true, an execute template uses typed JSON extra
vars for both execution and its per-run fencing acknowledgement:

```json
{
  "pve_maintenance_execute": true,
  "pve_maintenance_planned_singleton_fencing_ack": true
}
```

Both templates fail closed unless the PVE controlled-update policy is already
applied. They use `apt-get dist-upgrade --no-remove`; any simulated package
removal blocks execution. In planned-singleton mode, simulated installs or
configuration of `corosync`, `pve-cluster`, or other quorum-stack packages also
block execution.

Before a planned-singleton report or execute run, operationally disable each
affected `io` to `europa` replication job. Do not clear replication history or
remove jobs. A historical failed or error status is permitted only when its
unique cluster replication configuration explicitly disables that exact `io` to
`europa` job; running status always blocks. Enabled jobs targeting `europa`
also block while healthy because they can retry. Every `io`-source replication
configuration must have one local status entry.

For this temporary state only, an operator—not this role—may run the transient
manual `pvecm expected 1` command on `io` after confirming `europa` is
physically powered off and cannot rejoin. The static cluster membership remains
unchanged. Keep `pve_peer_reboot_enabled: false`; peer reboot remains disabled
and strict two-node. Change `pve_maintenance_cluster_safety_mode` back to
`strict_two_node` in inventory before `europa` is powered on or can rejoin.
Then remove the physical fence only through the manual cluster recovery
procedure, verify both nodes are online in `/cluster/status`, and complete a
strict report showing `Nodes: 2`, `Expected votes: 2`, `Total votes: 2`, and
`Quorate: Yes` before treating the planned exception as ended. Then re-enable
replication using the configuration digest and validate a successful sync.

After strict two-node mode is restored, run the first controlled update on
europa, then io. After the first validated manual runs, the recommended execute
schedule is europa Saturday 05:00 and io Sunday 05:00. A daily Semaphore report
schedule is optional. Keep peer reboot disabled until the first observed
controlled reboot, then it can be enabled and deployed. The local reboot timers,
if enabled, occur later. This two-node cluster has no QDevice and relies on
`two_node=1`; an io reboot temporarily takes down Semaphore, PBS, and data3. To
stop future local reboot requests, set `pve_peer_reboot_enabled: false` and
rerun the all-hosts playbook for that node; reservation recovery remains enabled
until any interrupted reboot is safe.

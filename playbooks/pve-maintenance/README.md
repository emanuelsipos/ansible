# PVE maintenance playbook

Create separate Semaphore templates for report and execute runs, each limited
to one node (`europa` or `io`). The execute templates initially have **no
schedule**. A report template supplies no execute variable. An execute template
uses typed JSON extra vars:

```json
{"pve_maintenance_execute":true}
```

Both templates fail closed unless the PVE controlled-update policy is already
applied. They use `apt-get dist-upgrade --no-remove`; any simulated package
removal blocks execution.

Run the first controlled update on europa, then io. After the first validated
manual runs, the recommended execute schedule is europa Saturday 05:00 and io
Sunday 05:00. A daily Semaphore report schedule is optional. Keep peer reboot
disabled until the first observed controlled reboot, then it can be enabled and
deployed. The local reboot timers, if enabled, occur later. This two-node
cluster has no QDevice and relies on `two_node=1`; an io reboot temporarily
takes down Semaphore, PBS, and data3. To stop future local reboot requests, set
`pve_peer_reboot_enabled: false` and rerun the all-hosts playbook for that node;
reservation recovery remains enabled until any interrupted reboot is safe.

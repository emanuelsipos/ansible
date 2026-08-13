# PVE host backup

Creates encrypted, file-level PVE host recovery snapshots with
`proxmox-backup-client`. These snapshots support clean reinstall and selective
restoration; they are not bare-metal images.

The role is disabled by default. It does not create PBS users, tokens, ACLs,
prune jobs, verification jobs, garbage-collection schedules, or datastore sync
jobs because doing so would require an administrator credential on each PVE
node.

## Backup contents

One timestamp-consistent PBS snapshot contains:

- `pve.pxar`: mounted `/etc/pve` configuration.
- `etc.pxar`: local `/etc`, excluding the duplicate `pve` subtree and this
  role's credential directory.
- `local.pxar`: custom programs and scripts under `/usr/local`.
- `opt.pxar`: locally installed tools under `/opt`.
- `recovery.pxar`: generated hardware, package, network, cluster, guest, ZFS,
  block-device, boot, systemd, and storage inventories plus an online SQLite
  backup of `/var/lib/pve-cluster/config.db`. It also preserves the explicitly
  classified, non-secret `/root/.forward`, `/root/.ssh/config`, and root public
  key when present.

The two PXAR exclusions are rooted at each archive source. On the audited hosts
they remove the duplicate `/pve` and credential-bearing `/pve-host-backup`
trees from `etc.pxar`. A matching top-level tree under another archive root
would also be excluded, so review host layout before deployment.

Each configured archive has a maximum apparent-size limit. A run fails before
upload if a source unexpectedly grows past its limit. Archive roots are limited
to the reviewed `/etc`, `/etc/pve`, `/usr/local`, and `/opt` paths so a variable
override cannot capture PVE guest disks, dumps, or transient filesystems. PXAR
skips descendant mountpoints by default; the role never enables the client
options that cross them.

## Explicit exclusions

`/root` is intentionally not archived broadly. Current host inspection found shell
histories, SSH private keys, rclone and Talos credentials, build trees, package
artifacts, and a legacy `/root/.host-backup` implementation there. Durable
credentials belong in Vaultwarden plus an offline recovery location, and source
belongs in Git. Add a narrowly scoped archive only after classifying a specific
file as necessary for recovery. The small default allowlist never includes a
private key, shell history, credential file, or environment file.

The current hosts have no recovery snippets under `/var/lib/vz`. Their custom
systemd units, NUT/network/ZFS/sysctl configuration, and package sources are
covered by `etc.pxar`; custom monitoring, ZFS snapshot, Beszel, Periphery,
`iptag`, and `talosctl` files are covered by `local.pxar` or `opt.pxar`.

## PBS setup

Before enabling the role:

1. Create one PBS user and API token per PVE node.
2. Create a namespace such as `pve-hosts/io` or `pve-hosts/europa`.
3. Grant only `DatastoreBackup` on that node's namespace.
4. Keep prune, verification, garbage collection, and datastore synchronization
   as PBS-side jobs using separate administrative identities.
5. Generate one PBS client encryption key per node. Store a recovery copy and
   any passphrase in Vaultwarden and a separate offline location before
   deploying it to the node.

The token can create and restore its owned backups but cannot prune or delete
existing snapshots. A compromised node can still read its unattended key and
token and can stop or flood future backups.

For the current topology, target local datastore `data3` and retain the hourly
PBS sync from `data3` to the Hexabyte S3 datastore. Do not rely on S3 as the
only copy. Monitor sync freshness, verification failures, GC failures, missed
host snapshots, and capacity on both datastores.

## Variables

Supply production values through Semaphore. Never commit them.

The token, key, and optional passphrase are published atomically as one
root-only credential bundle. systemd copies the bundle into its protected
credential directory for each run; the backup script extracts short-lived
credential files under its private runtime directory and removes them on exit.

```yaml
pve_host_backup_enabled: true
pve_host_backup_repository: "host-io@pbs!host-backup@pbs.example:8007:data3"
pve_host_backup_fingerprint: "00:11:22:33:44:55:66:77:88:99:aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99:aa:bb:cc:dd:ee:ff"
pve_host_backup_namespace: "pve-hosts/io"
pve_host_backup_id: "io"
pve_host_backup_token_secret: "SEMAPHORE_SECRET"
pve_host_backup_encryption_key: "SEMAPHORE_SECRET_PBS_KEY_JSON"
pve_host_backup_encryption_passphrase: "SEMAPHORE_SECRET_IF_KEY_IS_PROTECTED"
pve_host_backup_timer_calendar: "*-*-* 03:15:00"
```

Use `03:45` for the second node. The timer adds up to ten minutes of randomized
delay. A run is terminated after six hours by default; adjust
`pve_host_backup_timeout_start_sec` only for a measured need. Set
`pve_host_backup_require_quorum: false` only for a deliberately documented
recovery or standalone test case.

## Deployment and testing

Deploy to one node first:

```bash
ansible-playbook playbooks/all-hosts/playbook.yml \
  --limit io --tags host_backup
systemctl start pve-host-backup.service
journalctl -u pve-host-backup.service
```

List the resulting snapshot, confirm client-side encryption, and restore every
archive into an empty temporary directory. Validate the restored SQLite file:

```bash
sqlite3 ./pmxcfs-config.db 'PRAGMA integrity_check;'
sha256sum --check SHA256SUMS
```

Confirm the snapshot reaches Hexabyte through the PBS sync job and passes a PBS
verification job. Only after that restore test should the legacy
`/root/.host-backup` script, token, and keys be retired.

## Recovery

When one cluster node survives, reinstall the replacement with a compatible PVE
version and join it as a fresh member. Let pmxcfs replicate from the survivor.
Do not restore old `/etc/pve`, Corosync identity, node certificates, or
`config.db` over the surviving cluster.

When rebuilding the whole cluster, fence the old nodes, restore archives into a
temporary path, inspect ZFS pools before creating or importing anything, and
reconstruct configuration selectively. `config.db` is an emergency inspection
artifact; restoring it is a deliberate whole-cluster recovery action, not a
normal file copy.

To remove a previous deployment, set `pve_host_backup_enabled: false` and
`pve_host_backup_purge: true`. This stops and disables the managed timer and
removes this role's script, units, and credential directory. Disabled without
`purge` is a no-op. Purging does not touch the separate legacy
`/root/.host-backup` directory.

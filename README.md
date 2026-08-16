# Ansible

Ansible playbooks and roles for managing Debian, Ubuntu, and Proxmox hosts.

Production inventory and credentials are managed in Semaphore and are not stored in this repository. [`hosts.example`](hosts.example) documents the inventory groups expected by the playbooks.

## Playbooks

- `all-hosts`: unattended upgrades on non-PVE hosts, log retention, zsh,
  Docker, host tuning, encrypted PVE host backups, PVE update policy, and
  staggered PVE ZFS scrubs, and explicit PVE ZFS snapshot retention
- `beszel`: Beszel agent installation and configuration
- `komodo`: Komodo periphery and server configuration
- `tailscale`: Tailscale installation and enrollment
- `pve-maintenance`: single-node, report-first PVE `apt-get dist-upgrade`
  maintenance; see its [runbook](playbooks/pve-maintenance/README.md)

Reusable roles live under [`roles/`](roles/), including journald retention, zsh,
sysctl configuration, zram, staggered PVE ZFS scrubs, explicit ZFS snapshot
policy, vzdump exclusions, and GitHub release downloads.

## Semaphore configuration

Attach one variable group to the templates that run these playbooks.

| Input | Variable group section | Used by |
| --- | --- | --- |
| `PUBLIC_DOMAIN` | Variables → Environment variables | `beszel`, `komodo` |
| `KOMODO_REGISTRY_USERNAME` | Variables → Environment variables | `komodo` |
| `KOMODO_CORE_API_KEY` | Secrets → Environment variables | `komodo` |
| `KOMODO_CORE_API_SECRET` | Secrets → Environment variables | `komodo` |
| `KOMODO_REGISTRY_TOKEN` | Secrets → Environment variables | `komodo` |
| `TAILSCALE_AUTHKEY` | Secrets → Environment variables | `tailscale` |
| `agent_public_key` | Variables → Extra variables | `beszel` |
| `komodo_core_public_key` | Variables → Extra variables | `komodo` |
| `pve_host_backup_*` public settings | Variables → Extra variables or inventory | `all-hosts` |
| `pve_host_backup_token_secret` | Secrets → Extra variables or inventory | `all-hosts` |
| `pve_host_backup_encryption_key` | Secrets → Extra variables or inventory | `all-hosts` |
| `pve_host_backup_encryption_passphrase` | Secrets → Extra variables or inventory | `all-hosts` |

Production inventory is stored in Semaphore. The inventory must provide the
groups shown in [`hosts.example`](hosts.example); templates may limit runs to a
smaller host or group. It must also define `ansible_user` as an inventory
variable, either for all hosts or on each host. SSH identity belongs to the
inventory rather than repository policy:

```ini
[all:vars]
ansible_user=ansible
```

Each nested playbook directory links `group_vars` to the canonical repository
root directory. Semaphore installs static inventories beside the selected
playbook, so these links keep the same group variables available in Semaphore
and in local runs without maintaining duplicate variable files.

The `pve_host_backup` role is opt-in and fails closed when enabled without its
per-node PBS token, encryption key, repository, namespace, and fingerprint.
See [`roles/pve_host_backup/README.md`](roles/pve_host_backup/README.md) before
deploying it.

`pve_resource_scheduling` replaces Debian's all-pools periodic scrub execution
with one daily systemd timer that dynamically spaces pool-level ZFS scrubs for
configured PVE hosts. See
[`roles/pve_resource_scheduling/README.md`](roles/pve_resource_scheduling/README.md)
and keep the host-keyed `group_vars/pve.yml` calendar and cycle policy current.

`pve_zfs_snapshot_policy` applies reusable retention profiles to common and
host-specific datasets entirely from inventory variables. It uses explicit
opt-in snapshot properties and reports bounded prune candidates. Activation is
host-scoped: creation and scheduled pruning are enabled on reviewed host `io`,
while `europa` and unlisted hosts remain inactive. `prune_now` additionally
permits an immediate cleanup during the play when local pruning is enabled. See
[`roles/pve_zfs_snapshot_policy/README.md`](roles/pve_zfs_snapshot_policy/README.md).

The unattended-upgrades role is explicitly excluded from PVE inventory hosts.
PVE index refresh remains enabled without automatic package downloads or APT
autoclean, and the base APT install-mode timer is disabled. Use only the
controlled maintenance playbook for routine PVE updates.
The market survey found no mature third-party role that replaces this PVE-
specific safety policy, so the custom roles use official Ansible and PVE
building blocks without additional dependencies. See the [Proxmox package
repository and update documentation](https://pve.proxmox.com/pve-docs/pve-admin-guide.html#sysadmin_package_repositories).

For local use, copy `hosts.example` to `hosts`, replace the example hosts, install the requirements for the playbook being run, and provide the same variables through your preferred secret store.

```bash
ansible-galaxy collection install -r playbooks/all-hosts/requirements.yml
ansible-galaxy role install -r playbooks/all-hosts/requirements.yml
ansible-playbook -i hosts playbooks/all-hosts/playbook.yml
```

Install the hash-locked tools from `requirements-dev.txt`, then run
`pre-commit install` to apply available ansible-lint fixes before commits. CI
also opens an autofix PR when a push to `main` introduces fixable lint issues.

Renovate's `pip-compile` manager automatically updates direct dependencies,
regenerates pinned transitive dependencies and hashes, and performs lock-file
maintenance. Python and uv are pinned in `renovate.json5`; uv is also included in the
hash lock. To reproduce the lock locally on Linux x86_64 after installing `requirements-dev.txt`:

```bash
uv pip compile \
  --generate-hashes \
  --output-file=requirements-dev.txt \
  requirements-dev.in
```

## Networking

For Komodo hosts, IPv6 forwarding configures the first available interface in
this order: `komodo_ipv6_interface`, Ansible's default IPv6 interface, then its
default IPv4 interface. Set `komodo_ipv6_interface` when automatic detection is
not appropriate; it must name an interface present in Ansible's discovered
interface facts and contain only letters, digits, dots, underscores, or hyphens.

## License

[MIT](LICENSE)

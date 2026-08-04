# Ansible

Ansible playbooks and roles for managing Debian, Ubuntu, and Proxmox hosts.

Production inventory and credentials are managed in Semaphore and are not stored in this repository. [`hosts.example`](hosts.example) documents the inventory groups expected by the playbooks.

## Playbooks

- `all-hosts`: unattended upgrades, log retention, zsh, Docker, host tuning, and backup tooling
- `beszel`: Beszel agent installation and configuration
- `komodo`: Komodo periphery and server configuration
- `tailscale`: Tailscale installation and enrollment

Reusable roles live under [`roles/`](roles/), including journald retention, zsh, sysctl configuration, zram, vzdump exclusions, and GitHub release downloads.

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

Production inventory is stored in Semaphore. The inventory must provide the
groups shown in [`hosts.example`](hosts.example); templates may limit runs to a
smaller host or group.

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
maintenance. Python and uv are pinned in `renovate.json`; uv is also included in the
hash lock. To reproduce the lock locally on Linux x86_64 after installing `requirements-dev.txt`:

```bash
uv pip compile \
  --generate-hashes \
  --output-file=requirements-dev.txt \
  requirements-dev.in
```

## License

[MIT](LICENSE)

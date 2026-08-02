# Ansible

Ansible playbooks and roles for managing Debian, Ubuntu, and Proxmox hosts.

Production inventory and credentials are managed in Semaphore and are not stored in this repository. [`hosts.example`](hosts.example) documents the inventory groups expected by the playbooks.

## Playbooks

- `all-hosts`: unattended upgrades, log retention, Docker, host tuning, and backup tooling
- `beszel`: Beszel agent installation and configuration
- `komodo`: Komodo periphery and server configuration
- `tailscale`: Tailscale installation and enrollment

Reusable roles live under [`roles/`](roles/), including journald retention, sysctl configuration, zram, vzdump exclusions, and GitHub release downloads.

## Configuration

Semaphore supplies these environment variables:

```text
PUBLIC_DOMAIN
KOMODO_CORE_API_KEY
KOMODO_CORE_API_SECRET
KOMODO_REGISTRY_USERNAME
KOMODO_REGISTRY_TOKEN
```

It also supplies `komodo_core_public_key` and `agent_public_key` as Ansible extra variables.

For local use, copy `hosts.example` to `hosts`, replace the example hosts, install the requirements for the playbook being run, and provide the same variables through your preferred secret store.

```bash
ansible-galaxy install -r playbooks/all-hosts/requirements.yml
ansible-playbook -i hosts playbooks/all-hosts/playbook.yml
```

## License

[MIT](LICENSE)

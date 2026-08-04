#!/usr/bin/env python3
"""Verify nested playbooks resolve the canonical group variables."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_GROUP_VARS = ROOT / "group_vars"
EXPECTED = {
    "all-hosts": (
        "pve-test",
        {
            "machines_sysctl_settings",
            "pve_sysctl_settings",
            "unattended_upgrades_origins_patterns",
        },
    ),
    "beszel": ("pve-test", {"public_domain"}),
    "komodo": ("app-test", {"komodo_server_enabled"}),
    "tailscale": ("edge-test", {"machines_sysctl_settings"}),
}
INVENTORY = """\
[all:vars]
ansible_user=inventory-test-user

[pve]
pve-test

[vps]
edge-test

[machines:children]
pve
vps

[lxc]
app-test

[komodo]
app-test

[backup]
edge-test
"""


def inventory_vars(playbook_dir: Path, inventory: Path, host: str) -> dict:
    env = os.environ.copy()
    env.update(
        {
            "KOMODO_CORE_API_KEY": "test-key",
            "KOMODO_CORE_API_SECRET": "test-secret",
            "KOMODO_REGISTRY_TOKEN": "test-token",
            "KOMODO_REGISTRY_USERNAME": "test-user",
            "PUBLIC_DOMAIN": "example.invalid",
            "TAILSCALE_AUTHKEY": "test-key",
        }
    )
    result = subprocess.run(
        [
            "ansible-inventory",
            "--inventory",
            str(inventory),
            "--playbook-dir",
            str(playbook_dir),
            "--host",
            host,
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def main() -> None:
    playbooks = sorted((ROOT / "playbooks").glob("*/playbook.yml"))
    found = {playbook.parent.name for playbook in playbooks}
    if found != EXPECTED.keys():
        raise SystemExit(
            f"Update this check for the current playbooks: expected "
            f"{sorted(EXPECTED)}, found {sorted(found)}"
        )

    with tempfile.TemporaryDirectory() as temporary_dir:
        inventory = Path(temporary_dir) / "inventory.ini"
        inventory.write_text(INVENTORY, encoding="utf-8")

        for playbook in playbooks:
            playbook_dir = playbook.parent
            link = playbook_dir / "group_vars"
            if not link.is_symlink():
                raise SystemExit(f"{link} must be a symlink")
            if os.readlink(link) != "../../group_vars":
                raise SystemExit(f"{link} must point to ../../group_vars")
            if link.resolve() != CANONICAL_GROUP_VARS.resolve():
                raise SystemExit(f"{link} does not resolve to {CANONICAL_GROUP_VARS}")

            host, expected_vars = EXPECTED[playbook_dir.name]
            variables = inventory_vars(playbook_dir, inventory, host)
            missing = expected_vars - variables.keys()
            if missing:
                raise SystemExit(
                    f"{playbook_dir}: missing group variables {sorted(missing)}"
                )
            if variables.get("ansible_user") != "inventory-test-user":
                raise SystemExit(
                    f"{playbook_dir}: inventory ansible_user was not preserved"
                )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verify that the Renovate JSON5 configuration remains parseable."""

from pathlib import Path

import json5


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "renovate.json5"


def main() -> None:
    config = json5.loads(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise SystemExit("renovate.json5 must contain a JSON5 object")
    if not isinstance(config.get("packageRules"), list):
        raise SystemExit("renovate.json5 must define packageRules as a list")


if __name__ == "__main__":
    main()

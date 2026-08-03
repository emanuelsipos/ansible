#!/usr/bin/env python3
"""Convert a PEP 751 pylock file to pip's hash-locked requirements format."""

from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path


INPUT_REQUIREMENT = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)(?P<extras>\[[^\]]+\])?==(?P<version>[^\s]+)$"
)


def normalized(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def direct_requirements(path: Path) -> dict[str, tuple[str, str]]:
    requirements: dict[str, tuple[str, str]] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = INPUT_REQUIREMENT.fullmatch(line)
        if match is None:
            raise ValueError(f"unsupported input requirement: {line}")
        requirements[normalized(match["name"])] = (
            match["version"],
            match["extras"] or "",
        )
    return requirements


def render(input_path: Path, lock_path: Path) -> str:
    direct = direct_requirements(input_path)
    lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    packages: list[str] = []
    locked_direct: set[str] = set()

    for package in sorted(lock["packages"], key=lambda item: normalized(item["name"])):
        name = normalized(package["name"])
        extras = direct.get(name, ("", ""))[1]
        if name in direct:
            locked_direct.add(name)
            if direct[name][0] != package["version"]:
                raise ValueError(
                    f"{package['name']} is {direct[name][0]} in the input "
                    f"but {package['version']} in the lock"
                )

        hashes = sorted(
            {
                wheel["hashes"]["sha256"]
                for wheel in package.get("wheels", [])
                if "sha256" in wheel.get("hashes", {})
            }
        )
        if not hashes:
            raise ValueError(f"{package['name']} has no locked wheel SHA-256")
        suffix = " \\\n" + " \\\n".join(f"    --hash=sha256:{digest}" for digest in hashes)
        packages.append(f"{package['name']}{extras}=={package['version']}{suffix}")

    missing = sorted(set(direct) - locked_direct)
    if missing:
        raise ValueError(f"direct requirements missing from lock: {', '.join(missing)}")

    header = (
        "# Generated from requirements-dev.in for Python 3.14 on Linux x86_64.\n"
        "# Regenerate with the commands documented in README.md.\n"
    )
    return header + "\n" + "\n".join(packages) + "\n"


def validate_output(input_path: Path, output_path: Path) -> None:
    direct = direct_requirements(input_path)
    content = output_path.read_text(encoding="utf-8")
    locked: dict[str, tuple[str, str]] = {}
    for line in content.splitlines():
        match = INPUT_REQUIREMENT.match(line.removesuffix(" \\"))
        if match:
            locked[normalized(match["name"])] = (
                match["version"],
                match["extras"] or "",
            )

    for name, requirement in direct.items():
        if locked.get(name) != requirement:
            raise ValueError(f"{name} is missing or stale in {output_path}")

    package_count = sum(
        1
        for line in content.splitlines()
        if INPUT_REQUIREMENT.match(line.removesuffix(" \\"))
    )
    hash_count = len(re.findall(r"(?m)^\s+--hash=sha256:[a-f0-9]{64}$", content))
    if package_count == 0 or hash_count < package_count:
        raise ValueError(f"{output_path} contains an unhashed package")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        validate_output(args.input, args.output)
        print(f"{args.output} matches {args.input} and requires hashes")
    elif args.lock is None:
        parser.error("--lock is required unless --check is used")
    else:
        args.output.write_text(render(args.input, args.lock), encoding="utf-8")


if __name__ == "__main__":
    main()

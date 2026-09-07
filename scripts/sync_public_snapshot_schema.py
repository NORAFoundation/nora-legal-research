"""Synchronize the generated ResearchSnapshot schema into public consumers."""

from __future__ import annotations

import argparse
from pathlib import Path


SOURCE = Path(__file__).parents[1] / "schemas" / "research-snapshot-v1.schema.json"


def sync(targets: list[Path], *, check: bool) -> int:
    source = SOURCE.read_bytes()
    for target in targets:
        if check:
            if not target.exists() or target.read_bytes() != source:
                print(f"canonical ResearchSnapshot schema is stale: {target}")
                return 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source)
        print(f"synced {target}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", action="append", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return sync(args.target, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())

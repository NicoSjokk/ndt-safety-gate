"""Command line entry point: `ndt-gate validate <action.json>`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ndt_gate.gate import Gate
from ndt_gate.models import ProposedAction
from ndt_gate.twin import ClusterState, StubTwin

DEFAULT_STATE = Path("examples/cluster-state.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ndt-gate", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="run a proposed action through the gate")
    v.add_argument("action", type=Path, help="JSON file with the proposed action")
    v.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_STATE,
        help="cluster state for the stub twin (default: %(default)s)",
    )

    args = parser.parse_args(argv)

    action = ProposedAction.from_dict(json.loads(args.action.read_text()))
    gate = Gate(twin=StubTwin(ClusterState.load(args.state)))
    verdict = gate.validate(action)

    print(json.dumps(verdict.to_dict(), indent=2, default=str))
    return 0 if verdict.approved else 1


if __name__ == "__main__":
    sys.exit(main())

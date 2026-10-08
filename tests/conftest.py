from pathlib import Path

import pytest

from ndt_gate.twin import ClusterState

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def examples() -> Path:
    return EXAMPLES


@pytest.fixture
def prod_state() -> ClusterState:
    return ClusterState.load(EXAMPLES / "cluster-state.json")

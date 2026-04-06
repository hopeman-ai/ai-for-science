import sys
from pathlib import Path

import pytest

# src를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def data_dir(project_root) -> Path:
    return project_root / "data"


@pytest.fixture
def configs_dir(project_root) -> Path:
    return project_root / "configs"

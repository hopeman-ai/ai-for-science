import json

import pytest

from ai_for_science.api.data_service import (
    get_all_comparisons,
    get_dimension_list,
    get_overview,
    get_references,
    get_references_by_country,
    get_strategies,
)


@pytest.fixture
def strategies_data(data_dir):
    """strategies.json이 존재하고 올바른 구조인지 확인"""
    path = data_dir / "processed" / "strategies.json"
    if not path.exists():
        pytest.skip("strategies.json not found")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def references_data(data_dir):
    """sources.json이 존재하고 올바른 구조인지 확인"""
    path = data_dir / "references" / "sources.json"
    if not path.exists():
        pytest.skip("sources.json not found")
    return json.loads(path.read_text(encoding="utf-8"))


def test_get_strategies(strategies_data):
    data = get_strategies()
    assert "overview" in data
    assert "countries" in data
    assert "comparisons" in data


def test_get_overview(strategies_data):
    overview = get_overview()
    assert "overview" in overview
    assert "countries" in overview


def test_get_all_comparisons(strategies_data):
    comparisons = get_all_comparisons()
    assert isinstance(comparisons, list)
    if comparisons:
        assert "dimension" in comparisons[0]


def test_get_dimension_list(strategies_data):
    dims = get_dimension_list()
    assert isinstance(dims, list)
    if dims:
        assert "code" in dims[0]
        assert "label" in dims[0]


def test_get_references(references_data):
    refs = get_references()
    assert isinstance(refs, list)
    assert len(refs) > 0


def test_get_references_by_country(references_data):
    refs = get_references_by_country("japan")
    assert isinstance(refs, list)

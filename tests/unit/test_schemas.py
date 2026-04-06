import pytest

from ai_for_science.schemas.models import (
    AgentMessage,
    AgentType,
    ComparisonDimension,
    ComparisonEntry,
    Country,
    Reference,
    ServiceResponse,
    UserQuery,
)


def test_country_enum():
    assert Country.JAPAN.value == "japan"
    assert Country.USA.value == "usa"
    assert len(Country) == 4


def test_comparison_dimension_enum():
    assert ComparisonDimension.STRATEGY_TYPE.value == "strategy_type"
    assert len(ComparisonDimension) == 8


def test_user_query_basic():
    q = UserQuery(question="일본의 AI 전략은?")
    assert q.question == "일본의 AI 전략은?"
    assert q.countries is None
    assert q.dimensions is None


def test_user_query_with_filters():
    q = UserQuery(
        question="비교 분석",
        countries=[Country.JAPAN, Country.USA],
        dimensions=[ComparisonDimension.INFRASTRUCTURE],
    )
    assert len(q.countries) == 2
    assert len(q.dimensions) == 1


def test_reference_model():
    ref = Reference(
        title="Test Report",
        source="Test Org",
        url="https://example.com",
        country=Country.JAPAN,
    )
    assert ref.title == "Test Report"
    assert ref.description == ""


def test_agent_message():
    msg = AgentMessage(
        sender=AgentType.RESEARCH,
        content="테스트 응답",
    )
    assert msg.sender == AgentType.RESEARCH
    assert msg.references == []
    assert msg.comparisons == []


def test_comparison_entry():
    entry = ComparisonEntry(
        dimension=ComparisonDimension.INFRASTRUCTURE,
        dimension_label="인프라 전략",
        country_data={"japan": "AI 연구플랫폼", "usa": "NAIRR"},
    )
    assert entry.dimension_label == "인프라 전략"
    assert "japan" in entry.country_data


def test_service_response():
    resp = ServiceResponse(answer="분석 결과입니다.")
    assert resp.answer == "분석 결과입니다."
    assert resp.insights == []

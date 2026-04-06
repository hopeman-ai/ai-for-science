"""Critic 에이전트 및 평가 규칙 엔진 테스트"""

import pytest

from ai_for_science.evaluation.evidence import EvidenceStore
from ai_for_science.evaluation.rules import RuleEngine
from ai_for_science.schemas.evaluation import (
    CriticVerdict,
    IssueType,
    Severity,
)


@pytest.fixture
def rule_engine():
    return RuleEngine()


@pytest.fixture
def evidence_store():
    return EvidenceStore()


# ── 근거 검증 테스트 ──────────────────────────────────

def test_evidence_store_loads_chunks(evidence_store):
    """근거 인덱스가 정상 로드되는지 확인"""
    chunks = evidence_store.get_all_chunks()
    assert len(chunks) > 0


def test_evidence_store_loads_links(evidence_store):
    """콘텐츠-근거 링크가 정상 로드되는지 확인"""
    links = evidence_store.get_all_links()
    assert len(links) > 0


def test_evidence_coverage_existing_section(evidence_store):
    """근거가 있는 섹션의 커버리지 확인"""
    coverage = evidence_store.check_evidence_coverage("countries.korea")
    assert coverage["covered"] is True
    assert coverage["evidence_count"] > 0


def test_evidence_coverage_missing_section(evidence_store):
    """근거가 없는 섹션의 커버리지 확인"""
    coverage = evidence_store.check_evidence_coverage("nonexistent.section")
    assert coverage["covered"] is False


def test_latest_year_for_country(evidence_store):
    """국가별 최신 근거 연도 조회"""
    year = evidence_store.get_latest_year_for_country("korea")
    assert year >= 2026


# ── 과도한 단정 표현 탐지 테스트 ──────────────────────

def test_overclaim_detection(rule_engine):
    """과도한 단정 표현 감지"""
    content = {"text": "한국은 전략이 없다. AI 정책이 완전히 부재하다."}
    ev = rule_engine.evaluate_section("test.overclaim", content)
    overclaim_issues = [i for i in ev.issues if i.type == IssueType.OVERCLAIM]
    assert len(overclaim_issues) > 0


def test_no_overclaim_for_neutral_text(rule_engine):
    """중립적 표현에는 단정 이슈가 없어야 함"""
    content = {"text": "한국은 AI 행동계획을 수립하여 추진 중이다."}
    ev = rule_engine.evaluate_section("test.neutral", content)
    overclaim_issues = [i for i in ev.issues if i.type == IssueType.OVERCLAIM]
    assert len(overclaim_issues) == 0


# ── 비교 균형성 테스트 ────────────────────────────────

def test_balance_check_missing_country(rule_engine):
    """국가 누락 시 불균형 이슈 발생"""
    content = {
        "data": {
            "korea": {"summary": "한국 전략", "detail": "상세 설명"},
            "japan": {"summary": "일본 전략", "detail": "상세 설명"},
            # usa, eu, china 누락
        }
    }
    ev = rule_engine.evaluate_section("comparisons.test", content)
    imbalance = [i for i in ev.issues if i.type == IssueType.IMBALANCE]
    assert len(imbalance) > 0


def test_balance_check_complete(rule_engine):
    """5개국 모두 있으면 누락 이슈 없음"""
    content = {
        "data": {
            "korea": {"summary": "한국", "detail": "x" * 50},
            "japan": {"summary": "일본", "detail": "x" * 50},
            "china": {"summary": "중국", "detail": "x" * 50},
            "usa": {"summary": "미국", "detail": "x" * 50},
            "eu": {"summary": "EU", "detail": "x" * 50},
        }
    }
    ev = rule_engine.evaluate_section("comparisons.test", content)
    missing_issues = [
        i for i in ev.issues
        if i.type == IssueType.IMBALANCE and "누락" in i.reason
    ]
    assert len(missing_issues) == 0


# ── 점수 산정 테스트 ──────────────────────────────────

def test_score_calculation_no_issues(rule_engine):
    """이슈 없으면 100점"""
    score = rule_engine._calculate_score([])
    assert score == 100


def test_score_high_severity_deduction(rule_engine):
    """고위험 이슈 감점 확인"""
    from ai_for_science.schemas.evaluation import CriticIssue
    issues = [CriticIssue(
        type=IssueType.EVIDENCE_GAP, severity=Severity.HIGH,
        target_section="test", problem_text="test",
        reason="test", suggestion="test",
    )]
    score = rule_engine._calculate_score(issues)
    assert score == 85  # 100 - 15


# ── verdict 결정 테스트 ───────────────────────────────

def test_verdict_pass_high_score(rule_engine):
    """90점 이상 → PASS"""
    verdict = rule_engine._determine_verdict(95, [])
    assert verdict == CriticVerdict.PASS


def test_verdict_revise_medium_score(rule_engine):
    """75~89점 → REVISE"""
    verdict = rule_engine._determine_verdict(80, [])
    assert verdict == CriticVerdict.REVISE


def test_verdict_hold_low_score(rule_engine):
    """60 미만 → HOLD"""
    verdict = rule_engine._determine_verdict(55, [])
    assert verdict == CriticVerdict.HOLD


# ── 전체 섹션 평가 통합 테스트 ────────────────────────

def test_evaluate_real_strategy_section(rule_engine):
    """실제 strategies.json의 한국 데이터로 평가 수행"""
    import json
    from ai_for_science.config import settings

    path = settings.DATA_DIR / "processed" / "strategies.json"
    if not path.exists():
        pytest.skip("strategies.json not found")

    data = json.loads(path.read_text(encoding="utf-8"))
    korea = data.get("countries", {}).get("korea", {})
    if not korea:
        pytest.skip("korea data not found")

    ev = rule_engine.evaluate_section("countries.korea", korea)
    assert ev.score > 0
    assert ev.evaluation_id.startswith("eval_")
    assert ev.verdict in list(CriticVerdict)

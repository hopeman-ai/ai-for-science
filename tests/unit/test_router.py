"""Router 에이전트 테스트"""

import pytest

from ai_for_science.agents.router.agent import RouterAgent
from ai_for_science.schemas.evaluation import (
    CriticEvaluation,
    CriticIssue,
    CriticVerdict,
    IssueType,
    RouterDecision,
    Severity,
)


@pytest.fixture
def router():
    return RouterAgent()


def _make_eval(score, issues=None):
    return CriticEvaluation(
        evaluation_id="eval_test",
        target="test",
        score=score,
        verdict=CriticVerdict.PASS if score >= 90 else CriticVerdict.REVISE,
        issues=issues or [],
    )


def _make_issue(issue_type, severity):
    return CriticIssue(
        type=issue_type, severity=severity,
        target_section="test", problem_text="test",
        reason="test", suggestion="test",
    )


# ── PASS ──────────────────────────────────────────────

def test_router_pass_high_score(router):
    """고득점 + 이슈 없음 → PASS"""
    result = router.route(_make_eval(95))
    assert result.decision == RouterDecision.PASS
    assert result.send_to == "publish"


def test_router_pass_with_low_issues(router):
    """고득점 + 저위험 이슈만 → PASS"""
    issues = [_make_issue(IssueType.SOURCE_UNCLEAR, Severity.LOW)]
    result = router.route(_make_eval(92, issues))
    assert result.decision == RouterDecision.PASS


# ── REVISE ────────────────────────────────────────────

def test_router_revise_medium_score(router):
    """75~89점 → REVISE"""
    issues = [_make_issue(IssueType.OVERCLAIM, Severity.MEDIUM)]
    result = router.route(_make_eval(82, issues))
    assert result.decision == RouterDecision.REVISE
    assert result.send_to == "reviser"


# ── REWRITE ───────────────────────────────────────────

def test_router_rewrite_low_score(router):
    """60 미만 → REWRITE"""
    issues = [
        _make_issue(IssueType.EVIDENCE_GAP, Severity.MEDIUM),
        _make_issue(IssueType.OVERCLAIM, Severity.MEDIUM),
        _make_issue(IssueType.IMBALANCE, Severity.MEDIUM),
    ]
    result = router.route(_make_eval(55, issues))
    assert result.decision == RouterDecision.REWRITE


def test_router_rewrite_missing_high(router):
    """핵심 누락 HIGH → REWRITE"""
    issues = [_make_issue(IssueType.MISSING, Severity.HIGH)]
    result = router.route(_make_eval(78, issues))
    assert result.decision == RouterDecision.REWRITE


# ── HOLD ──────────────────────────────────────────────

def test_router_hold_evidence_gap_high(router):
    """공식 출처 부족 HIGH → HOLD"""
    issues = [_make_issue(IssueType.EVIDENCE_GAP, Severity.HIGH)]
    result = router.route(_make_eval(70, issues))
    assert result.decision == RouterDecision.HOLD


# ── ESCALATE ──────────────────────────────────────────

def test_router_escalate_outdated_high(router):
    """최신 문서 충돌 HIGH → ESCALATE"""
    issues = [_make_issue(IssueType.OUTDATED, Severity.HIGH)]
    result = router.route(_make_eval(65, issues))
    assert result.decision == RouterDecision.ESCALATE
    assert result.send_to == "human_review"


def test_router_escalate_inconsistency_high(router):
    """내부 불일치 HIGH → ESCALATE"""
    issues = [_make_issue(IssueType.INCONSISTENCY, Severity.HIGH)]
    result = router.route(_make_eval(60, issues))
    assert result.decision == RouterDecision.ESCALATE


# ── 조치 항목 생성 ────────────────────────────────────

def test_router_generates_actions(router):
    """라우팅 결과에 구체적 조치 항목이 포함"""
    issues = [
        _make_issue(IssueType.OVERCLAIM, Severity.MEDIUM),
        _make_issue(IssueType.MISSING, Severity.MEDIUM),
    ]
    result = router.route(_make_eval(80, issues))
    assert len(result.required_actions) > 0


# ── 전체 파이프라인 통합 테스트 ───────────────────────

def test_pipeline_with_router():
    """파이프라인 실행 시 router_decision 포함 확인"""
    import json
    from ai_for_science.config import settings
    from ai_for_science.evaluation.pipeline import EvaluationPipeline

    path = settings.DATA_DIR / "processed" / "strategies.json"
    if not path.exists():
        pytest.skip("strategies.json not found")

    data = json.loads(path.read_text(encoding="utf-8"))
    korea = data.get("countries", {}).get("korea", {})
    if not korea:
        pytest.skip("korea data not found")

    pipeline = EvaluationPipeline(max_iterations=1)
    result = pipeline.run_section("countries.korea", korea)

    assert result.routing is not None
    assert result.routing.decision in list(RouterDecision)
    assert result.final_evaluation is not None
    rd = result.to_dict()
    assert "router_decision" in rd

"""Reviser 에이전트 테스트"""

import pytest

from ai_for_science.agents.reviser.agent import ReviserAgent
from ai_for_science.schemas.evaluation import (
    CriticEvaluation,
    CriticIssue,
    CriticVerdict,
    IssueType,
    Severity,
)


@pytest.fixture
def reviser():
    return ReviserAgent()


@pytest.fixture
def sample_evaluation():
    """overclaim 이슈가 포함된 평가 결과"""
    return CriticEvaluation(
        evaluation_id="eval_test_001",
        target="countries.korea",
        score=75,
        verdict=CriticVerdict.REVISE,
        summary="테스트 평가",
        issues=[
            CriticIssue(
                type=IssueType.OVERCLAIM,
                severity=Severity.MEDIUM,
                target_section="countries.korea",
                problem_text="전략이 없다",
                reason="과도한 단정 표현",
                suggestion="완화 표현 사용",
            ),
            CriticIssue(
                type=IssueType.SOURCE_UNCLEAR,
                severity=Severity.LOW,
                target_section="countries.korea",
                problem_text="알려져 있다",
                reason="출처 불명확",
                suggestion="출처 명시",
            ),
        ],
    )


def test_reviser_fixes_overclaim(reviser, sample_evaluation):
    """overclaim 이슈를 자동 수정"""
    content = {"text": "한국은 전략이 없다."}
    result = reviser.revise(sample_evaluation, content)

    overclaim_fixes = [i for i in result.items if i.issue_type == IssueType.OVERCLAIM]
    assert len(overclaim_fixes) > 0
    assert "전략이 없다" not in overclaim_fixes[0].revised_text


def test_reviser_flags_unclear_source(reviser, sample_evaluation):
    """출처 불명확 표현에 플래그 추가"""
    content = {"text": "알려져 있다."}
    result = reviser.revise(sample_evaluation, content)

    source_fixes = [i for i in result.items if i.issue_type == IssueType.SOURCE_UNCLEAR]
    assert len(source_fixes) > 0
    assert "출처 확인 필요" in source_fixes[0].revised_text


def test_reviser_does_not_fix_high_evidence_gap(reviser):
    """고위험 근거 부족은 자동 수정하지 않음"""
    evaluation = CriticEvaluation(
        evaluation_id="eval_test_002",
        target="test",
        score=50,
        verdict=CriticVerdict.HOLD,
        issues=[
            CriticIssue(
                type=IssueType.EVIDENCE_GAP,
                severity=Severity.HIGH,
                target_section="test",
                problem_text="근거 없는 주장",
                reason="공식 출처 없음",
                suggestion="출처 추가",
            ),
        ],
    )
    result = reviser.revise(evaluation, {"text": "근거 없는 주장"})
    assert len(result.items) == 0


def test_apply_revisions(reviser, sample_evaluation):
    """수정 결과를 콘텐츠에 적용"""
    content = {"text": "한국은 전략이 없다. 이는 알려져 있다."}
    result = reviser.revise(sample_evaluation, content)

    revised = reviser.apply_revisions(content, result)

    # 원본과 다르게 수정되었는지 확인
    if result.items:
        assert revised != content


def test_revision_summary(reviser, sample_evaluation):
    """수정 결과 요약 생성"""
    content = {"text": "한국은 전략이 없다."}
    result = reviser.revise(sample_evaluation, content)
    assert "자동 수정" in result.summary
    assert result.requires_re_evaluation is True

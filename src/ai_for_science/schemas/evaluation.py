"""Critic / Reviser 에이전트용 평가 데이터 모델"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ── 열거형 ──────────────────────────────────────────────

class IssueType(str, Enum):
    EVIDENCE_GAP = "evidence_gap"        # 근거 부족
    OUTDATED = "outdated"                # 최신성 문제
    OVERCLAIM = "overclaim"              # 과도한 단정/과장
    MISSING = "missing"                  # 핵심 누락
    INCONSISTENCY = "inconsistency"      # 내부 불일치
    IMBALANCE = "imbalance"              # 국가 간 비교 불균형
    SOURCE_UNCLEAR = "source_unclear"    # 출처 불명확


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewStatus(str, Enum):
    DRAFT = "draft"                      # 초안
    CRITIC_REVIEWED = "critic_reviewed"  # Critic 검토 완료
    REVISION_NEEDED = "revision_needed"  # 수정 필요
    HUMAN_REVIEW = "human_review"        # 사람 검토 필요
    PUBLISHABLE = "publishable"          # 게시 가능


class CriticVerdict(str, Enum):
    PASS = "pass"           # 게시 가능
    REVISE = "revise"       # 자동 수정 후 재평가
    ESCALATE = "escalate"   # 사람 검토 필요
    HOLD = "hold"           # 게시 보류


class RouterDecision(str, Enum):
    PASS = "pass"           # 게시
    REVISE = "revise"       # 경미한 수정 → Reviser
    REWRITE = "rewrite"     # 구조적 재작성 필요
    HOLD = "hold"           # 근거 부족, 보류
    ESCALATE = "escalate"   # 사람 검토 필요


class RouterActionType(str, Enum):
    EDIT = "edit"
    REWRITE = "rewrite"
    REMOVE = "remove"
    ADD_EVIDENCE = "add_evidence"
    ADD_MISSING = "add_missing_topic"


# ── 근거자료 ────────────────────────────────────────────

class EvidenceChunk(BaseModel):
    """원문 근거 단위"""
    evidence_id: str
    document_id: str                     # sources.json의 id
    document_title: str
    issuing_body: str
    year: int
    url: str
    excerpt: str                         # 근거 발췌문
    page_or_section: str = ""


class EvidenceLink(BaseModel):
    """서비스 문장 ↔ 근거 연결"""
    target_section: str                  # 예: "comparisons.infrastructure.korea"
    target_text: str                     # 검증 대상 문장
    evidence_ids: list[str] = []         # 연결된 근거 ID 목록
    has_sufficient_evidence: bool = False
    note: str = ""


# ── Critic 평가 ─────────────────────────────────────────

class CriticIssue(BaseModel):
    """Critic이 발견한 개별 문제"""
    type: IssueType
    severity: Severity
    target_section: str
    problem_text: str
    reason: str
    suggestion: str


class FreshnessCheck(BaseModel):
    """최신성 검증 결과"""
    section: str
    latest_source_year: int
    content_reflects_latest: bool
    note: str = ""


class EvidenceCheck(BaseModel):
    """근거 검증 결과"""
    section: str
    claim: str
    has_evidence: bool
    evidence_id: str = ""
    confidence: str = ""  # "strong" | "partial" | "none"


class CriticEvaluation(BaseModel):
    """Critic 에이전트 전체 평가 결과"""
    evaluation_id: str = ""
    target: str                          # 평가 대상 (예: "strategies.korea", "comparisons.infrastructure")
    evaluated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    score: int = 0                       # 0~100
    verdict: CriticVerdict = CriticVerdict.HOLD
    summary: str = ""
    issues: list[CriticIssue] = []
    evidence_checks: list[EvidenceCheck] = []
    freshness_checks: list[FreshnessCheck] = []
    recommendation: str = ""


# ── Router 판단 결과 ───────────────────────────────────

class RouterAction(BaseModel):
    """Router가 지시하는 개별 조치"""
    section: str
    action: RouterActionType
    reason: str = ""


class RoutingResult(BaseModel):
    """Router 에이전트 판단 결과"""
    routing_id: str = ""
    evaluation_id: str                   # 판단 기반 Critic 평가 ID
    decided_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    decision: RouterDecision = RouterDecision.HOLD
    reason: str = ""
    priority: Severity = Severity.MEDIUM
    required_actions: list[RouterAction] = []
    send_to: str = ""                    # "reviser" | "human_review" | "publish"


# ── Reviser 결과 ────────────────────────────────────────

class RevisionItem(BaseModel):
    """Reviser가 수행한 개별 수정"""
    target_section: str
    original_text: str
    revised_text: str
    revision_reason: str
    issue_type: IssueType


class RevisionResult(BaseModel):
    """Reviser 에이전트 수정 결과"""
    revision_id: str = ""
    evaluation_id: str                   # 기반 Critic 평가 ID
    revised_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    items: list[RevisionItem] = []
    summary: str = ""
    requires_re_evaluation: bool = True


# ── 컨텐츠 상태 관리 ───────────────────────────────────

class ContentStatus(BaseModel):
    """서비스 컨텐츠 단위의 상태"""
    section: str
    status: ReviewStatus = ReviewStatus.DRAFT
    last_critic_score: int = 0
    last_evaluated_at: str = ""
    last_revised_at: str = ""
    last_human_review_at: str = ""
    evaluation_history: list[str] = []   # evaluation_id 목록

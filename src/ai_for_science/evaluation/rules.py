"""Critic 평가 규칙 엔진 — 룰 기반 점수 산정 및 verdict 결정"""

import re
from datetime import datetime

from ai_for_science.schemas.evaluation import (
    CriticEvaluation,
    CriticIssue,
    CriticVerdict,
    EvidenceCheck,
    FreshnessCheck,
    IssueType,
    ReviewStatus,
    Severity,
)
from ai_for_science.evaluation.evidence import EvidenceStore

# 과도한 단정 표현 패턴
OVERCLAIM_PATTERNS = [
    r"반드시.*해야\s*한다",
    r"전혀.*없다",
    r"완전히.*부재",
    r"전략이\s*없다",
    r"전략\s*부재",
    r"절대적으로",
    r"가장\s+뛰어나",
    r"유일하게",
    r"압도적",
]

CURRENT_YEAR = datetime.now().year


class RuleEngine:
    """Critic 평가 규칙 엔진"""

    def __init__(self, evidence_store: EvidenceStore | None = None):
        self.evidence = evidence_store or EvidenceStore()

    def evaluate_section(self, section: str, content: dict) -> CriticEvaluation:
        """단일 섹션을 규칙 기반으로 평가"""
        issues: list[CriticIssue] = []
        evidence_checks: list[EvidenceCheck] = []
        freshness_checks: list[FreshnessCheck] = []

        text = self._extract_text(content)

        # 1) 근거 커버리지 점검
        ec_issues, ec_checks = self._check_evidence(section, text)
        issues.extend(ec_issues)
        evidence_checks.extend(ec_checks)

        # 2) 최신성 점검
        fr_issues, fr_checks = self._check_freshness(section, content)
        issues.extend(fr_issues)
        freshness_checks.extend(fr_checks)

        # 3) 과도한 단정 표현 점검
        issues.extend(self._check_overclaim(section, text))

        # 4) 국가 비교 균형성 점검
        if "comparisons" in section or "countries" in section:
            issues.extend(self._check_balance(section, content))

        # 5) 출처 명확성 점검
        issues.extend(self._check_source_clarity(section, text))

        # 6) 필수 주제 커버리지 점검
        if "countries" in section:
            issues.extend(self._check_coverage(section, text))

        # 점수 산정 및 verdict 결정
        score = self._calculate_score(issues)
        verdict = self._determine_verdict(score, issues)
        summary = self._build_summary(section, score, issues)

        return CriticEvaluation(
            evaluation_id=f"eval_{section}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            target=section,
            score=score,
            verdict=verdict,
            summary=summary,
            issues=issues,
            evidence_checks=evidence_checks,
            freshness_checks=freshness_checks,
            recommendation=self._build_recommendation(verdict, issues),
        )

    # ── 규칙 1: 근거 검증 ─────────────────────────────

    def _check_evidence(
        self, section: str, text: str
    ) -> tuple[list[CriticIssue], list[EvidenceCheck]]:
        issues = []
        checks = []

        coverage = self.evidence.check_evidence_coverage(section)

        if not coverage["covered"]:
            issues.append(CriticIssue(
                type=IssueType.EVIDENCE_GAP,
                severity=Severity.HIGH,
                target_section=section,
                problem_text=text[:100],
                reason="이 섹션에 연결된 근거자료가 없습니다.",
                suggestion="공식 출처 문서를 확인하고 근거 링크를 추가하세요.",
            ))
            checks.append(EvidenceCheck(
                section=section,
                claim=text[:100],
                has_evidence=False,
                confidence="none",
            ))
        else:
            if not coverage.get("all_sufficient", False):
                issues.append(CriticIssue(
                    type=IssueType.EVIDENCE_GAP,
                    severity=Severity.MEDIUM,
                    target_section=section,
                    problem_text=text[:100],
                    reason="일부 문장에 근거가 불충분합니다.",
                    suggestion="근거가 부족한 문장을 보완하거나 해당 주장을 완화하세요.",
                ))
            checks.append(EvidenceCheck(
                section=section,
                claim=text[:100],
                has_evidence=True,
                confidence="strong" if coverage.get("all_sufficient") else "partial",
            ))

        return issues, checks

    # ── 규칙 2: 최신성 검증 ────────────────────────────

    def _check_freshness(
        self, section: str, content: dict
    ) -> tuple[list[CriticIssue], list[FreshnessCheck]]:
        issues = []
        checks = []

        # 국가 코드 추출
        country = self._extract_country(section)
        if not country:
            return issues, checks

        latest_year = self.evidence.get_latest_year_for_country(country)
        if latest_year == 0:
            return issues, checks

        # 콘텐츠 내 연도 참조 확인
        text = self._extract_text(content)
        year_mentions = re.findall(r'20[12]\d', text)
        old_years = [int(y) for y in year_mentions if int(y) < latest_year - 1]

        is_fresh = len(old_years) == 0
        checks.append(FreshnessCheck(
            section=section,
            latest_source_year=latest_year,
            content_reflects_latest=is_fresh,
            note=f"과거 연도 참조: {old_years}" if old_years else "최신 자료 기준 작성됨",
        ))

        if not is_fresh:
            issues.append(CriticIssue(
                type=IssueType.OUTDATED,
                severity=Severity.MEDIUM,
                target_section=section,
                problem_text=f"과거 연도({old_years}) 참조 발견",
                reason=f"최신 대표 문서({latest_year}년)보다 오래된 자료를 참조하고 있습니다.",
                suggestion="최신 대표 문서 기준으로 내용을 갱신하세요.",
            ))

        return issues, checks

    # ── 규칙 6: 필수 주제 커버리지 ──────────────────────

    # 국가 전략 요약에 반드시 포함되어야 하는 키워드
    REQUIRED_TOPICS = {
        "korea": ["행동계획", "국가인공지능전략위원회", "K-문샷"],
        "japan": ["문부과학성", "연구 시스템", "후가쿠"],
        "china": ["국무원", "AI+", "슈퍼컴퓨팅"],
        "usa": ["NAIRR", "NSF", "연구 인프라"],
        "eu": ["Horizon", "EOSC", "AI Continent"],
    }

    def _check_coverage(self, section: str, text: str) -> list[CriticIssue]:
        """국가별 전략 요약에 필수 키워드가 포함되어 있는지 점검"""
        issues = []
        country = self._extract_country(section)
        if country not in self.REQUIRED_TOPICS:
            return issues

        required = self.REQUIRED_TOPICS[country]
        missing = [kw for kw in required if kw not in text]

        if missing:
            issues.append(CriticIssue(
                type=IssueType.MISSING,
                severity=Severity.MEDIUM if len(missing) <= 1 else Severity.HIGH,
                target_section=section,
                problem_text=f"누락 키워드: {', '.join(missing)}",
                reason=f"{country} 전략 요약에 필수 주제({', '.join(missing)})가 누락되었습니다.",
                suggestion=f"근거자료를 참조하여 {', '.join(missing)} 관련 내용을 추가하세요.",
            ))
        return issues

    # ── 규칙 3: 과도한 단정 표현 ───────────────────────

    def _check_overclaim(self, section: str, text: str) -> list[CriticIssue]:
        issues = []
        for pattern in OVERCLAIM_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                issues.append(CriticIssue(
                    type=IssueType.OVERCLAIM,
                    severity=Severity.MEDIUM,
                    target_section=section,
                    problem_text=match,
                    reason=f"과도한 단정 표현 '{match}'이 감지되었습니다.",
                    suggestion="근거가 뒷받침되지 않는 단정 표현을 완화하세요. 예: '~로 평가됨', '~로 분석됨'.",
                ))
        return issues

    # ── 규칙 4: 비교 균형성 ────────────────────────────

    def _check_balance(self, section: str, content: dict) -> list[CriticIssue]:
        issues = []
        if not isinstance(content, dict):
            return issues

        countries_expected = {"korea", "japan", "china", "usa", "eu"}
        data = content.get("data", content)

        if isinstance(data, dict):
            present = set(data.keys()) & countries_expected
            missing = countries_expected - present
            if missing:
                issues.append(CriticIssue(
                    type=IssueType.IMBALANCE,
                    severity=Severity.MEDIUM,
                    target_section=section,
                    problem_text=f"누락 국가: {', '.join(missing)}",
                    reason="일부 국가의 비교 데이터가 누락되어 불균형합니다.",
                    suggestion=f"{', '.join(missing)} 국가의 데이터를 추가하세요.",
                ))

            # 텍스트 길이 균형 확인
            lengths = {}
            for k, v in data.items():
                if k in countries_expected:
                    t = self._extract_text(v)
                    lengths[k] = len(t)

            if lengths:
                avg_len = sum(lengths.values()) / len(lengths)
                for k, l in lengths.items():
                    if l < avg_len * 0.3:
                        issues.append(CriticIssue(
                            type=IssueType.IMBALANCE,
                            severity=Severity.LOW,
                            target_section=section,
                            problem_text=f"{k}: {l}자 (평균 {avg_len:.0f}자)",
                            reason=f"{k} 국가의 설명이 다른 국가에 비해 현저히 짧습니다.",
                            suggestion="설명의 분량을 균형 있게 조정하세요.",
                        ))

        return issues

    # ── 규칙 5: 출처 명확성 ────────────────────────────

    def _check_source_clarity(self, section: str, text: str) -> list[CriticIssue]:
        issues = []
        vague_patterns = [
            r"일부에서는",
            r"알려져\s*있다",
            r"것으로\s*보인다",
            r"~라고\s*한다",
            r"전문가들은",
        ]
        for pattern in vague_patterns:
            if re.search(pattern, text):
                issues.append(CriticIssue(
                    type=IssueType.SOURCE_UNCLEAR,
                    severity=Severity.LOW,
                    target_section=section,
                    problem_text=re.search(pattern, text).group(),
                    reason="출처가 불명확한 간접 표현이 사용되었습니다.",
                    suggestion="구체적인 출처(기관명, 문서명)를 명시하세요.",
                ))
        return issues

    # ── 점수 산정 ──────────────────────────────────────

    def _calculate_score(self, issues: list[CriticIssue]) -> int:
        """100점 기준 감점 방식"""
        score = 100
        for issue in issues:
            if issue.severity == Severity.HIGH:
                score -= 15
            elif issue.severity == Severity.MEDIUM:
                score -= 8
            elif issue.severity == Severity.LOW:
                score -= 3
        return max(0, score)

    def _determine_verdict(self, score: int, issues: list[CriticIssue]) -> CriticVerdict:
        """점수 및 이슈에 따른 verdict 결정"""
        # 고위험 이슈가 있으면 즉시 escalate 또는 hold
        high_issues = [i for i in issues if i.severity == Severity.HIGH]
        if any(i.type == IssueType.OUTDATED for i in high_issues):
            return CriticVerdict.ESCALATE
        if any(i.type == IssueType.EVIDENCE_GAP for i in high_issues):
            return CriticVerdict.HOLD

        if score >= 90:
            return CriticVerdict.PASS
        elif score >= 75:
            return CriticVerdict.REVISE
        elif score >= 60:
            return CriticVerdict.REVISE
        else:
            return CriticVerdict.HOLD

    def score_to_status(self, score: int, verdict: CriticVerdict) -> ReviewStatus:
        """verdict를 ReviewStatus로 변환"""
        mapping = {
            CriticVerdict.PASS: ReviewStatus.PUBLISHABLE,
            CriticVerdict.REVISE: ReviewStatus.REVISION_NEEDED,
            CriticVerdict.ESCALATE: ReviewStatus.HUMAN_REVIEW,
            CriticVerdict.HOLD: ReviewStatus.DRAFT,
        }
        return mapping.get(verdict, ReviewStatus.DRAFT)

    # ── 유틸 ───────────────────────────────────────────

    def _extract_text(self, content) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, dict):
            parts = []
            for v in content.values():
                parts.append(self._extract_text(v))
            return " ".join(parts)
        if isinstance(content, list):
            return " ".join(self._extract_text(i) for i in content)
        return str(content)

    def _extract_country(self, section: str) -> str:
        for c in ["korea", "japan", "china", "usa", "eu"]:
            if c in section:
                return c
        return ""

    def _build_summary(self, section: str, score: int, issues: list[CriticIssue]) -> str:
        high = sum(1 for i in issues if i.severity == Severity.HIGH)
        med = sum(1 for i in issues if i.severity == Severity.MEDIUM)
        low = sum(1 for i in issues if i.severity == Severity.LOW)
        return (
            f"[{section}] 점수: {score}/100 | "
            f"이슈: 고위험 {high}건, 중위험 {med}건, 저위험 {low}건"
        )

    def _build_recommendation(self, verdict: CriticVerdict, issues: list[CriticIssue]) -> str:
        if verdict == CriticVerdict.PASS:
            return "게시 가능합니다. 이슈가 있다면 낮은 우선순위로 개선하세요."
        if verdict == CriticVerdict.REVISE:
            targets = list({i.target_section for i in issues if i.severity != Severity.LOW})
            return f"수정이 필요합니다. 우선 점검 영역: {', '.join(targets[:3])}"
        if verdict == CriticVerdict.ESCALATE:
            return "최신 자료와 충돌하는 내용이 있습니다. 사람 검토가 필요합니다."
        return "근거가 부족하여 게시를 보류합니다. 공식 출처를 확보한 후 재작성하세요."

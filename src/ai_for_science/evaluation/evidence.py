"""근거자료 저장소 — evidence_index.json 기반 근거 조회·검증"""

import json
from pathlib import Path

from ai_for_science.config import settings
from ai_for_science.schemas.evaluation import EvidenceChunk, EvidenceLink


class EvidenceStore:
    """근거자료 인덱스를 로드하고 조회하는 저장소"""

    def __init__(self):
        self._chunks: dict[str, EvidenceChunk] = {}
        self._links: list[EvidenceLink] = []
        self._load()

    def _load(self):
        path = settings.DATA_DIR / "processed" / "evidence_index.json"
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        for c in data.get("evidence_chunks", []):
            chunk = EvidenceChunk(**c)
            self._chunks[chunk.evidence_id] = chunk
        for lnk in data.get("content_links", []):
            self._links.append(EvidenceLink(**lnk))

    def get_chunk(self, evidence_id: str) -> EvidenceChunk | None:
        return self._chunks.get(evidence_id)

    def get_all_chunks(self) -> list[EvidenceChunk]:
        return list(self._chunks.values())

    def get_links_for_section(self, section_prefix: str) -> list[EvidenceLink]:
        """특정 섹션에 연결된 근거 링크 목록 반환"""
        return [lnk for lnk in self._links if lnk.target_section.startswith(section_prefix)]

    def get_all_links(self) -> list[EvidenceLink]:
        return list(self._links)

    def check_evidence_coverage(self, section: str) -> dict:
        """해당 섹션의 근거 커버리지 점검"""
        links = self.get_links_for_section(section)
        if not links:
            return {"covered": False, "link_count": 0, "evidence_count": 0}

        total_evidence = sum(len(lnk.evidence_ids) for lnk in links)
        all_sufficient = all(lnk.has_sufficient_evidence for lnk in links)
        return {
            "covered": True,
            "link_count": len(links),
            "evidence_count": total_evidence,
            "all_sufficient": all_sufficient,
        }

    def get_latest_year_for_country(self, country: str) -> int:
        """특정 국가의 최신 근거 문서 연도 반환"""
        years = [
            c.year for c in self._chunks.values()
            if country in c.document_id
        ]
        return max(years) if years else 0

    def get_evidence_for_claim(self, section: str, claim_text: str) -> list[EvidenceChunk]:
        """특정 문장에 연결된 근거 청크 목록 반환"""
        for lnk in self._links:
            if lnk.target_section == section or claim_text in lnk.target_text:
                return [self._chunks[eid] for eid in lnk.evidence_ids if eid in self._chunks]
        return []

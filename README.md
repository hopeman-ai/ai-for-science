# AI for Science — 국가별 전략 비교

공개자료를 기반으로 주요국의 AI for Science 국가전략을 비교 분석하는 정책 참고 서비스입니다.

> **참고용 분석 플랫폼입니다.** 공식 정부 입장이나 법적 해석을 대변하지 않습니다.
> 공개된 정책 문서를 기반으로 한 요약·비교이며, 최신성 및 정확성은 지속적으로 검토·개선 중입니다.
> 오류나 개선 사항은 [Issues](../../issues)를 통해 알려주시면 반영하겠습니다.

## 비교 대상

| 국가 | 전략 유형 |
|------|----------|
| 미국 | 연구 인프라 개방형 |
| EU | 연구 네트워크 통합형 |
| 일본 | 연구 시스템 혁신형 |
| 중국 | 산업 플랫폼 주도형 |
| 한국 | 산업·인프라 기반 Science 확장형 |

## 주요 기능

- 국가별 AI for Science 전략 요약 및 비교
- 8개 차원(전략 유형, 인프라, 데이터, 인재, 거버넌스 등) 비교 분석
- 국가 전략 포지셔닝 시각화 (산업/과학 × 정부/생태계 2축)
- 한국 PEST 진단 및 정책 제안
- 근거자료 기반 검증 워크플로우 (Critic → Router → Reviser)

## 공개 범위

이 저장소는 **문서 중심의 베타 공개**입니다.

| 구분 | 공개 여부 |
|------|----------|
| 전략 비교 데이터 (요약/메타데이터) | 공개 |
| 프론트엔드 코드 | 공개 |
| 백엔드 코드 | 공개 |
| 출처 목록 및 링크 | 공개 |
| API 키, 토큰, .env | **비공개** (.gitignore) |
| 원문 PDF/전문 저장본 | **비공개** (링크만 제공) |
| 실행 산출물 (outputs/) | **비공개** (.gitignore) |

## 디렉터리 구조

```
ai-for-science/
├── configs/              # 설정 (프롬프트, 파이프라인)
├── data/                 # 정책 데이터 (메타데이터, 요약)
│   ├── processed/        # 전략 비교 JSON
│   └── references/       # 출처 목록, 외부 리소스
├── docs/                 # 프로젝트 문서
├── src/ai_for_science/   # 소스 코드
│   ├── agents/           # 멀티 에이전트 (Critic, Router, Reviser 등)
│   ├── api/              # FastAPI 서버
│   ├── evaluation/       # 검증 파이프라인
│   └── frontend/         # 웹 UI
├── tests/                # 테스트
├── .env.example          # 환경변수 템플릿 (API 키 미포함)
├── DISCLAIMER.md         # 정책 신뢰성 고지
├── SECURITY.md           # 보안 정책
└── pyproject.toml        # 의존성 관리
```

## 설치 및 실행

```bash
# 환경 셋업
python scripts/setup_env.py

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# .env에 OpenAI API 키 설정
cp .env.example .env
# .env 파일 편집 → OPENAI_API_KEY 입력

# 서버 실행
python scripts/run_server.py
# http://localhost:8000 접속
```

## 테스트

```bash
python scripts/run_tests.py
```

## 데이터 출처

이 서비스의 모든 분석은 아래와 같은 공식 자료를 기반으로 합니다.

- 대한민국 AI 행동계획 (국가인공지능전략위원회, 2026)
- 독자 AI 파운데이션 모델 프로젝트 (과기정통부, 2025)
- AI 특화 파운데이션 모델 프로젝트 (과기정통부, 2025)
- AI for Science 推進について (문부과학성, 2023)
- NAIRR (NSF, 2024)
- AI Continent Action Plan (European Commission, 2025)
- 인공지능+ 행동계획 (중국 국무원, 2024)

전체 출처 목록: [data/references/sources.json](data/references/sources.json)

## 피드백

이 서비스는 외부 피드백을 반영하여 개선합니다.

- **사실 오류 제보**: [Issue 등록](../../issues/new?template=fact-error.yml)
- **최신 자료 제안**: [Issue 등록](../../issues/new?template=source-update.yml)
- **전략 해석 의견**: [Discussions](../../discussions)

자세한 안내: [CONTRIBUTING.md](CONTRIBUTING.md)

## 기술 스택

Python 3.11+ · FastAPI · Pydantic · OpenAI API · Vanilla JS · Canvas 2D

## 라이선스

MIT License — [LICENSE](LICENSE)

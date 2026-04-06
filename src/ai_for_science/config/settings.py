import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트 기준 .env 로드
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """프로젝트 전역 설정"""

    # LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

    # 경로 (프로젝트 루트 기준)
    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    CONFIGS_DIR: Path = PROJECT_ROOT / "configs"
    PROMPTS_DIR: Path = PROJECT_ROOT / "configs" / "prompts"
    OUTPUTS_DIR: Path = PROJECT_ROOT / "outputs"

    # 출력 하위 경로
    OUTPUTS_DRAFT: Path = OUTPUTS_DIR / "draft"
    OUTPUTS_FINAL: Path = OUTPUTS_DIR / "final"
    OUTPUTS_RETRIEVAL: Path = OUTPUTS_DIR / "retrieval"
    OUTPUTS_ARCHIVE: Path = OUTPUTS_DIR / "archive"
    OUTPUTS_RUNS: Path = OUTPUTS_DIR / "runs"


settings = Settings()

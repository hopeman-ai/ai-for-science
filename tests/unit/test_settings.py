from pathlib import Path

from ai_for_science.config.settings import Settings


def test_settings_paths_exist():
    """설정에 정의된 주요 경로가 유효한지 검증"""
    s = Settings()
    assert isinstance(s.PROJECT_ROOT, Path)
    assert s.DATA_DIR.name == "data"
    assert s.CONFIGS_DIR.name == "configs"
    assert s.PROMPTS_DIR.name == "prompts"


def test_settings_default_model():
    """기본 모델 설정 확인"""
    s = Settings()
    assert s.OPENAI_MODEL  # 비어있지 않음
    assert isinstance(s.OPENAI_TEMPERATURE, float)

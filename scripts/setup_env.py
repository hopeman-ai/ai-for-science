#!/usr/bin/env python3
"""프로젝트 개발환경 초기 셋업 스크립트

사용법:
    python scripts/setup_env.py

수행 작업:
    1. .venv 가상환경 생성
    2. pip 업그레이드
    3. 프로젝트 의존성 설치 (editable mode)
    4. .env 파일 생성 (없는 경우)
    5. outputs 디렉터리 구조 생성
"""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = PROJECT_ROOT / ".venv"


def run(cmd: list[str], **kwargs):
    print(f"  > {' '.join(cmd)}")
    subprocess.check_call(cmd, **kwargs)


def main():
    print("=== AI for Science 개발환경 셋업 ===\n")

    # 1. 가상환경 생성
    if not VENV_DIR.exists():
        print("[1/5] .venv 가상환경 생성...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        print("[1/5] .venv 이미 존재 (건너뜀)")

    # venv 내 python 경로
    if sys.platform == "win32":
        python = str(VENV_DIR / "Scripts" / "python.exe")
    else:
        python = str(VENV_DIR / "bin" / "python")

    # 2. pip 업그레이드
    print("[2/5] pip 업그레이드...")
    run([python, "-m", "pip", "install", "--upgrade", "pip"])

    # 3. 의존성 설치
    print("[3/5] 프로젝트 의존성 설치 (editable mode)...")
    run([python, "-m", "pip", "install", "-e", f"{PROJECT_ROOT}[dev]"])

    # 4. .env 파일
    env_file = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"
    if not env_file.exists() and env_example.exists():
        print("[4/5] .env 파일 생성 (.env.example 복사)...")
        shutil.copy(env_example, env_file)
        print("  !! .env 파일에 OPENAI_API_KEY를 설정하세요.")
    else:
        print("[4/5] .env 파일 확인 완료")

    # 5. outputs 디렉터리 구조
    print("[5/5] outputs 디렉터리 구조 생성...")
    for subdir in ["archive", "draft", "final", "retrieval", "runs"]:
        d = PROJECT_ROOT / "outputs" / subdir
        d.mkdir(parents=True, exist_ok=True)
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    print("\n=== 셋업 완료! ===")
    print(f"가상환경 활성화: {VENV_DIR / 'Scripts' / 'activate'}")
    print("서버 실행: uvicorn ai_for_science.api.main:app --reload")


if __name__ == "__main__":
    main()

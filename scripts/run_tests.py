#!/usr/bin/env python3
"""테스트 실행 스크립트

사용법:
    python scripts/run_tests.py              # 전체 테스트
    python scripts/run_tests.py --unit       # 단위 테스트만
    python scripts/run_tests.py --integration # 통합 테스트만
    python scripts/run_tests.py --cov        # 커버리지 포함
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="테스트 실행")
    parser.add_argument("--unit", action="store_true", help="단위 테스트만 실행")
    parser.add_argument("--integration", action="store_true", help="통합 테스트만 실행")
    parser.add_argument("--cov", action="store_true", help="커버리지 리포트 생성")
    args = parser.parse_args()

    cmd = [sys.executable, "-m", "pytest", "-v"]

    if args.unit:
        cmd.append("tests/unit/")
    elif args.integration:
        cmd.extend(["-m", "integration", "tests/integration/"])
    else:
        cmd.append("tests/")

    if args.cov:
        cmd.extend(["--cov=src/ai_for_science", "--cov-report=html"])

    subprocess.call(cmd, cwd=str(PROJECT_ROOT))


if __name__ == "__main__":
    main()

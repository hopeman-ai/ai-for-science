#!/usr/bin/env python3
"""실행 결과를 archive 디렉터리로 이동하는 스크립트

사용법:
    python scripts/archive_run.py                      # outputs/runs → outputs/archive
    python scripts/archive_run.py --source outputs/draft --tag v1
"""

import argparse
import shutil
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="실행 결과 아카이빙")
    parser.add_argument(
        "--source",
        default="outputs/runs",
        help="아카이빙할 소스 디렉터리 (기본: outputs/runs)",
    )
    parser.add_argument("--tag", default="", help="아카이브 태그 (예: v1, experiment-01)")
    args = parser.parse_args()

    source = PROJECT_ROOT / args.source
    if not source.exists() or not any(source.iterdir()):
        print(f"아카이빙할 파일이 없습니다: {source}")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{timestamp}_{args.tag}" if args.tag else timestamp
    dest = PROJECT_ROOT / "outputs" / "archive" / archive_name

    shutil.copytree(source, dest)
    print(f"아카이빙 완료: {dest}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""FastAPI 개발 서버 실행 스크립트

사용법:
    python scripts/run_server.py
    python scripts/run_server.py --port 8080
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="AI for Science 서버 실행")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-reload", action="store_true")
    args = parser.parse_args()

    cmd = [
        sys.executable, "-m", "uvicorn",
        "ai_for_science.api.main:app",
        "--host", args.host,
        "--port", str(args.port),
    ]
    if not args.no_reload:
        cmd.append("--reload")

    env_additions = {"PYTHONPATH": str(PROJECT_ROOT / "src")}

    import os
    env = {**os.environ, **env_additions}

    print(f"서버 시작: http://{args.host}:{args.port}")
    subprocess.call(cmd, cwd=str(PROJECT_ROOT), env=env)


if __name__ == "__main__":
    main()

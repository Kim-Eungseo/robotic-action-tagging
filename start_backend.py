#!/usr/bin/env python3
"""
로봇 행동 태깅 도구 - FastAPI 백엔드 시작 스크립트
"""

import os
import sys
import subprocess


def check_dependencies():
    """필요한 의존성 패키지들이 설치되어 있는지 확인"""
    required_packages = ["fastapi", "uvicorn", "datasets", "pillow", "numpy"]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ 다음 패키지들이 설치되어 있지 않습니다:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n다음 명령으로 설치하세요:")
        print(f"pip install {' '.join(missing_packages)}")
        print("\n또는:")
        print("pip install -r requirements.txt")
        return False

    return True


def start_server():
    """FastAPI 서버 시작"""
    print("🚀 로봇 행동 태깅 FastAPI 서버를 시작합니다...")
    print("📋 API 문서: http://localhost:8001/docs")
    print("🎯 프론트엔드: http://localhost:8000")
    print("\n종료하려면 Ctrl+C를 누르세요.\n")

    # 백엔드 디렉터리로 이동
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    if not os.path.exists(backend_dir):
        print("❌ backend 디렉터리를 찾을 수 없습니다.")
        return False

    try:
        # uvicorn으로 서버 시작
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8001",
                "--reload",
            ],
            cwd=backend_dir,
        )
    except KeyboardInterrupt:
        print("\n🛑 서버가 종료되었습니다.")
    except Exception as e:
        print(f"❌ 서버 시작 중 오류 발생: {e}")
        return False

    return True


if __name__ == "__main__":
    print("🤖 로봇 행동 태깅 도구 - FastAPI 백엔드")
    print("=" * 50)

    if not check_dependencies():
        sys.exit(1)

    start_server()

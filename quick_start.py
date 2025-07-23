#!/usr/bin/env python3
"""
Libero 데이터셋 빠른 시작 스크립트
"""

import os
import sys
import time
import subprocess
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def check_libero_access():
    """Libero 데이터셋 접근 가능 여부 확인"""
    try:
        from datasets import load_dataset

        logger.info("🔍 Libero 데이터셋 접근 권한을 확인하는 중...")
        # 샘플 데이터만 로드해서 테스트
        dataset = load_dataset("physical-intelligence/libero", split="train[:1]")
        return True
    except Exception as e:
        logger.error(f"❌ Libero 데이터셋 접근 실패: {str(e)}")
        return False


def start_simple_server():
    """간단한 HTTP 서버 시작"""
    try:
        logger.info("🌐 HTTP 서버를 시작하는 중...")
        subprocess.Popen([sys.executable, "-m", "http.server", "8000"])
        return True
    except Exception as e:
        logger.error(f"❌ HTTP 서버 시작 실패: {str(e)}")
        return False


def show_instructions():
    """사용 방법 안내"""
    logger.info("\n=== 🚀 서버가 시작되었습니다! ===")
    logger.info("📱 브라우저에서 다음 주소로 접속하세요:")
    logger.info("   http://localhost:8000")
    logger.info("\n🔧 문제 해결:")
    logger.info("1. 포트 8000이 사용 중인 경우:")
    logger.info("   다른 프로세스를 종료하거나 포트를 변경하세요")
    logger.info("2. 페이지가 로드되지 않는 경우:")
    logger.info("   브라우저를 새로고침하거나 캐시를 삭제해보세요")


def main():
    try:
        logger.info("🤖 Libero 로봇 행동 태깅 도구 시작")
        logger.info("=" * 40)

        # 1. 의존성 확인
        logger.info("\n📦 의존성 확인 중...")

        # datasets 체크
        try:
            __import__("datasets")
            logger.info("✅ datasets 설치됨")
        except ImportError as e:
            logger.error("❌ datasets - 설치 필요")
            logger.error("💾 다음 명령으로 설치하세요:")
            logger.error("pip install datasets")
            logger.error("또는:")
            logger.error("pip install -r requirements.txt")
            return

        # PIL(pillow) 체크
        try:
            import PIL

            logger.info(f"✅ pillow (PIL) v{PIL.__version__} 설치됨")
        except ImportError as e:
            logger.error("❌ pillow - 설치 필요")
            logger.error("💾 다음 명령으로 설치하세요:")
            logger.error("pip install pillow")
            logger.error("또는:")
            logger.error("pip install -r requirements.txt")
            return

        # 2. Libero 데이터셋 접근성 확인
        if not check_libero_access():
            logger.warning("\n⚠️ Libero 데이터셋에 접근할 수 없습니다.")
            logger.info("로컬 이미지 업로드 기능은 계속 사용 가능합니다.")

        # 3. 웹 서버 시작
        if start_simple_server():
            show_instructions()

            logger.info("\n🛑 서버를 중지하려면 Ctrl+C를 누르세요.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\n👋 서버가 종료되었습니다.")
        else:
            logger.error("❌ 웹 서버 시작에 실패했습니다.")
    except Exception as e:
        logger.error(f"❌ 예상치 못한 오류 발생: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()

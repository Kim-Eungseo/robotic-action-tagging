#!/usr/bin/env python3
"""
로봇 행동 태깅 도구 - 통합 서버 시작 스크립트
Frontend (HTTP) + Backend (FastAPI) 동시 실행
"""

import os
import sys
import time
import signal
import subprocess
import threading
import requests
from datetime import datetime


class ServerManager:
    def __init__(self):
        self.frontend_process = None
        self.backend_process = None
        self.running = False
        
    def check_dependencies(self):
        """필요한 의존성 패키지들이 설치되어 있는지 확인"""
        required_packages = {
            "fastapi": "fastapi",
            "uvicorn": "uvicorn", 
            "datasets": "datasets",
            "PIL": "pillow",
            "numpy": "numpy",
            "requests": "requests"
        }
        missing_packages = []
        
        for import_name, package_name in required_packages.items():
            try:
                __import__(import_name)
            except ImportError:
                missing_packages.append(package_name)
        
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
    
    def check_ports(self):
        """포트 8000, 8001이 사용 가능한지 확인"""
        import socket
        
        ports = [8000, 8001]
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    print(f"⚠️  포트 {port}이 이미 사용 중입니다.")
                    print(f"   다음 명령으로 기존 프로세스를 종료하세요:")
                    print(f"   sudo lsof -ti:{port} | xargs kill")
                    sock.close()
                    return False
            except:
                pass
            finally:
                sock.close()
        
        return True
    
    def start_backend(self):
        """백엔드 FastAPI 서버 시작"""
        print("🚀 백엔드 서버 시작 중...")
        
        backend_dir = os.path.join(os.path.dirname(__file__), "backend")
        if not os.path.exists(backend_dir):
            print("❌ backend 디렉터리를 찾을 수 없습니다.")
            return False
        
        try:
            self.backend_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "main:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8001",
                    "--reload"
                ],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"❌ 백엔드 서버 시작 실패: {e}")
            return False
    
    def start_frontend(self):
        """프론트엔드 HTTP 서버 시작"""
        print("🌐 프론트엔드 서버 시작 중...")
        
        try:
            self.frontend_process = subprocess.Popen(
                [sys.executable, "-m", "http.server", "8000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"❌ 프론트엔드 서버 시작 실패: {e}")
            return False
    
    def wait_for_servers(self):
        """서버들이 준비될 때까지 대기"""
        print("\n⏳ 서버 시작 대기 중...")
        
        max_retries = 30
        
        # 백엔드 서버 확인
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:8001", timeout=1)
                if response.status_code == 200:
                    print("✅ 백엔드 서버 준비 완료")
                    break
            except:
                pass
            time.sleep(1)
        else:
            print("❌ 백엔드 서버 시작 타임아웃")
            return False
        
        # 프론트엔드 서버 확인
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:8000", timeout=1)
                if response.status_code == 200:
                    print("✅ 프론트엔드 서버 준비 완료")
                    break
            except:
                pass
            time.sleep(1)
        else:
            print("❌ 프론트엔드 서버 시작 타임아웃")
            return False
        
        return True
    
    def show_info(self):
        """서버 정보 및 접속 안내"""
        print("\n" + "="*60)
        print("🎉 모든 서버가 성공적으로 시작되었습니다!")
        print("="*60)
        
        print(f"\n📱 브라우저에서 다음 주소들로 접속하세요:")
        print(f"   🎯 메인 애플리케이션: http://localhost:8000")
        print(f"   🤖 Libero 전용 뷰어: http://localhost:8000/libero_frontend.html")
        print(f"   📋 API 문서: http://localhost:8001/docs")
        print(f"   🔧 API 테스트: http://localhost:8001")
        
        print(f"\n🔧 서버 상태:")
        print(f"   Frontend: 🟢 실행 중 (PID: {self.frontend_process.pid})")
        print(f"   Backend:  🟢 실행 중 (PID: {self.backend_process.pid})")
        
        print(f"\n💡 주요 기능:")
        print(f"   • HuggingFace 데이터셋 연동")
        print(f"   • Libero 로봇 데이터 분석 (273,465개 프레임)")
        print(f"   • 듀얼 카메라 뷰 (메인/손목 카메라)")
        print(f"   • 실시간 로봇 상태 모니터링")
        print(f"   • 서버 기반 태깅 데이터 저장")
        
        print(f"\n⚠️  종료하려면 Ctrl+C를 누르세요")
        print("="*60)
    
    def stop_servers(self):
        """모든 서버 종료"""
        print("\n🛑 서버들을 종료하는 중...")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("✅ 프론트엔드 서버 종료됨")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                print("⚡ 프론트엔드 서버 강제 종료됨")
            except Exception as e:
                print(f"❌ 프론트엔드 서버 종료 오류: {e}")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✅ 백엔드 서버 종료됨")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                print("⚡ 백엔드 서버 강제 종료됨")
            except Exception as e:
                print(f"❌ 백엔드 서버 종료 오류: {e}")
        
        self.running = False
        print("👋 모든 서버가 종료되었습니다.")
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러 (Ctrl+C 처리)"""
        self.stop_servers()
        sys.exit(0)
    
    def monitor_processes(self):
        """프로세스 상태 모니터링"""
        while self.running:
            time.sleep(5)
            
            # 프로세스가 종료되었는지 확인
            if self.frontend_process and self.frontend_process.poll() is not None:
                print("❌ 프론트엔드 서버가 예상치 못하게 종료되었습니다.")
                self.running = False
                break
                
            if self.backend_process and self.backend_process.poll() is not None:
                print("❌ 백엔드 서버가 예상치 못하게 종료되었습니다.")
                self.running = False
                break
    
    def run(self):
        """메인 실행 함수"""
        print("🤖 로봇 행동 태깅 도구 - 통합 서버 시작")
        print("="*50)
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 1. 의존성 확인
        print("\n📦 의존성 확인 중...")
        if not self.check_dependencies():
            return False
        print("✅ 모든 의존성이 설치되어 있습니다.")
        
        # 2. 포트 확인
        print("\n🔍 포트 사용 가능성 확인 중...")
        if not self.check_ports():
            return False
        print("✅ 포트 8000, 8001 사용 가능합니다.")
        
        # 3. 서버 시작
        if not self.start_backend():
            return False
            
        if not self.start_frontend():
            self.stop_servers()
            return False
        
        # 4. 서버 준비 대기
        if not self.wait_for_servers():
            self.stop_servers()
            return False
        
        # 5. 정보 출력
        self.show_info()
        
        # 6. 모니터링 시작
        self.running = True
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # 7. 메인 루프 (사용자 입력 대기)
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_servers()
        
        return True


def main():
    """메인 함수"""
    manager = ServerManager()
    
    try:
        success = manager.run()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        manager.stop_servers()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
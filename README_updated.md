# 🤖 로봇 행동 태깅 도구 - HuggingFace 연동

로봇 팔의 연속적인 행동 사진들을 분석하고 각 구간별로 행동을 태깅할 수 있는 웹 애플리케이션입니다. **HuggingFace datasets와 완전 연동**되어 클라우드의 로봇 데이터셋을 직접 로드하고 태깅할 수 있습니다.

## 🆕 새로운 기능

- **🤗 HuggingFace 데이터셋 연동**: 클라우드에서 로봇 행동 데이터를 직접 로드
- **🔄 실시간 동기화**: FastAPI 백엔드를 통한 빠른 데이터 처리
- **📡 API 기반 아키텍처**: 확장 가능한 마이크로서비스 구조
- **💾 서버 저장**: 태깅 데이터를 서버에 저장하고 세션 관리

## ✨ 주요 기능

### 로컬 기능
- **이미지 시퀀스 재생**: 로봇의 연속적인 행동 사진들을 동영상처럼 재생
- **타임라인 인터페이스**: 아이폰 영상 편집 스타일의 직관적인 타임라인
- **구간별 태깅**: 각 행동 구간에 이름과 설명 추가

### HuggingFace 연동 기능 
- **데이터셋 브라우징**: HuggingFace Hub의 로봇 데이터셋 탐색
- **실시간 로딩**: 클라우드에서 이미지 시퀀스 스트리밍
- **메타데이터 활용**: 데이터셋의 추가 정보 표시
- **다양한 형식 지원**: PIL Image, NumPy 배열, 다양한 데이터 형식

### 고급 기능
- **재생 제어**: 재생/일시정지, 프레임별 이동, 속도 조절
- **데이터 관리**: 로컬/서버 저장, JSON 내보내기/가져오기
- **키보드 단축키**: 빠른 조작을 위한 키보드 지원
- **세션 관리**: 작업 세션별 태깅 데이터 관리

## 🚀 시작하기

### 1. 의존성 설치

```bash
# Python 패키지 설치
pip install -r requirements.txt

# 또는 수동 설치
pip install fastapi uvicorn datasets pillow numpy python-multipart
```

### 2. 서버 실행

**방법 1: 자동 스크립트 사용**
```bash
python start_backend.py
```

**방법 2: 수동 실행**
```bash
# 백엔드 서버 시작 (새 터미널)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# 프론트엔드 서버 시작 (다른 터미널)
python -m http.server 8000
```

### 3. 접속

- **메인 애플리케이션**: http://localhost:8000/frontend_updated.html
- **API 문서**: http://localhost:8001/docs
- **기본 버전**: http://localhost:8000 (로컬 업로드만)

## 🎯 사용 방법

### HuggingFace 데이터셋 모드

1. **모드 전환**: 상단에서 "HuggingFace 데이터셋" 탭 클릭
2. **데이터셋 로드**: 
   ```
   데이터셋 이름: your-username/robot-manipulation-dataset
   Split: train, validation, test 중 선택
   ```
3. **시퀀스 선택**: 썸네일 브라우저에서 원하는 시퀀스 클릭
4. **태깅 작업**: 로컬 모드와 동일한 방식으로 행동 태깅

### 로컬 업로드 모드

1. **모드 전환**: 상단에서 "로컬 업로드" 탭 클릭
2. **이미지 업로드**: "이미지 시퀀스 업로드" 버튼으로 파일 선택
3. **태깅 작업**: 타임라인에서 구간별 행동 태깅

### 기본 태깅 워크플로우

1. **재생 및 분석**: 스페이스바로 재생하며 로봇 행동 관찰
2. **태깅**: 
   - 의미있는 행동 구간에서 "새 태그 추가"
   - 행동 이름 입력 (예: "물건 집기", "이동하기", "놓기")
   - 시작/끝 프레임 조정
3. **저장**: 
   - 로컬 저장: JSON 파일로 내보내기
   - 서버 저장: 세션 ID로 서버에 저장

## 📁 프로젝트 구조

```
robotic-action-tagging/
├── backend/
│   └── main.py              # FastAPI 백엔드 서버
├── frontend_updated.html    # HuggingFace 연동 프론트엔드
├── script_updated.js        # 업데이트된 JavaScript
├── index.html              # 기본 프론트엔드 (로컬 전용)
├── script.js               # 기본 JavaScript
├── style.css               # 공통 스타일시트
├── start_backend.py        # 백엔드 시작 스크립트
├── requirements.txt        # Python 의존성
└── README_updated.md       # 이 파일
```

## 🔧 API 엔드포인트

### 데이터셋 관련
- `GET /api/datasets` - 인기 데이터셋 목록
- `GET /api/datasets/{name}/info` - 데이터셋 정보
- `GET /api/datasets/{name}/{split}/sequence/{index}` - 이미지 시퀀스 조회

### 태깅 관련
- `POST /api/tagging/{session_id}` - 태깅 데이터 저장
- `GET /api/tagging/{session_id}` - 태깅 데이터 로드
- `GET /api/tagging/sessions` - 세션 목록

### 파일 업로드
- `POST /api/upload-images` - 로컬 이미지 업로드

## 🎯 HuggingFace 데이터셋 예시

### 지원하는 데이터 형식

```python
# 1. 이미지 리스트 형식
{
    "images": [PIL.Image, PIL.Image, ...],
    "actions": ["pick", "move", "place"],
    "metadata": {...}
}

# 2. 단일 이미지 형식  
{
    "image": PIL.Image,
    "action": "pick",
    "step": 0
}

# 3. 프레임 시퀀스 형식
{
    "frames": [numpy.array, numpy.array, ...],
    "episode_id": "ep_001"
}
```

### 데이터셋 업로드 예시

```python
from datasets import Dataset, DatasetDict
from PIL import Image
import numpy as np

# 로봇 행동 데이터셋 생성
def create_robot_dataset():
    # 예시 데이터
    episodes = []
    for ep in range(100):
        frames = []
        actions = []
        
        # 각 에피소드당 50프레임
        for frame in range(50):
            # 가상의 이미지 생성 (실제로는 로봇 카메라 이미지)
            img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            frames.append(Image.fromarray(img))
            
            # 행동 라벨
            if frame < 15:
                actions.append("approach")
            elif frame < 30:
                actions.append("grasp")
            elif frame < 45:
                actions.append("lift")
            else:
                actions.append("place")
        
        episodes.append({
            "images": frames,
            "actions": actions,
            "episode_id": f"ep_{ep:03d}",
            "success": np.random.choice([True, False])
        })
    
    # 데이터셋 생성
    dataset = Dataset.from_list(episodes)
    
    # train/test 분할
    dataset_dict = DatasetDict({
        "train": dataset.select(range(80)),
        "test": dataset.select(range(80, 100))
    })
    
    # HuggingFace Hub에 업로드
    dataset_dict.push_to_hub("your-username/robot-manipulation-dataset")

# 사용 예시
create_robot_dataset()
```

## 🎮 키보드 단축키

| 키 | 기능 |
|---|---|
| `스페이스바` | 재생/일시정지 토글 |
| `←` | 이전 프레임 |
| `→` | 다음 프레임 |
| `ESC` | 태그 편집 취소 |

## 📊 데이터 형식

### 태깅 데이터 (JSON)

```json
{
  "tags": [
    {
      "id": "1640995200000",
      "name": "물건 집기",
      "startFrame": 0,
      "endFrame": 25,
      "description": "로봇 팔이 테이블 위의 물건에 접근하여 집는 동작"
    }
  ],
  "totalFrames": 100,
  "fps": 10,
  "exportTime": "2024-01-01T00:00:00.000Z",
  "version": "1.0",
  "datasetName": "your-username/robot-dataset",
  "splitName": "train"
}
```

## 🔬 고급 활용

### 1. 커스텀 데이터셋 연동

```python
# datasets 라이브러리로 로봇 데이터 로드
from datasets import load_dataset

# 공개 데이터셋 로드
dataset = load_dataset("your-username/robot-manipulation")

# 로컬 데이터셋 로드  
dataset = load_dataset("imagefolder", data_dir="./robot_images")
```

### 2. 배치 태깅 워크플로우

1. HuggingFace에서 대량의 로봇 에피소드 로드
2. 각 에피소드별로 행동 구간 태깅
3. 서버에 저장하여 팀원들과 공유
4. JSON으로 내보내어 ML 파이프라인에 활용

### 3. 태깅 데이터 활용

```python
import json

# 태깅 데이터 로드
with open('robot_action_tags.json') as f:
    tags_data = json.load(f)

# 행동별 프레임 구간 추출
for tag in tags_data['tags']:
    action = tag['name']
    start_frame = tag['startFrame'] 
    end_frame = tag['endFrame']
    
    print(f"행동: {action}, 구간: {start_frame}-{end_frame}")
```

## 🐛 문제 해결

### 백엔드 연결 오류
```bash
# 백엔드 서버가 실행 중인지 확인
curl http://localhost:8001/

# 포트 충돌 시 다른 포트 사용
uvicorn main:app --port 8002
```

### HuggingFace 인증 오류
```bash
# HuggingFace CLI로 로그인
huggingface-cli login

# 또는 환경변수 설정
export HUGGINGFACE_HUB_TOKEN="your_token_here"
```

### 메모리 부족 오류
- 큰 데이터셋의 경우 배치 크기 조정
- 이미지 해상도 다운샘플링 고려
- 서버 메모리 증설

## 📝 로드맵

### 단기 (1-2개월)
- [ ] 실시간 협업 태깅 기능
- [ ] 태그 템플릿 및 자동 제안
- [ ] 비디오 파일 직접 지원

### 중기 (3-6개월)  
- [ ] AI 보조 자동 태깅
- [ ] 3D 시각화 지원
- [ ] 대규모 데이터셋 최적화

### 장기 (6개월+)
- [ ] 로봇 시뮬레이터 연동
- [ ] 실시간 로봇 제어 인터페이스
- [ ] 분산 태깅 시스템

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 새 기능 브랜치를 만듭니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`)
4. 브랜치를 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🙏 감사의 말

- HuggingFace datasets 팀
- FastAPI 개발팀  
- 로봇 연구 커뮤니티 
# 🤖 Libero 로봇 행동 태깅 도구

[Physical Intelligence Libero 데이터셋](https://huggingface.co/datasets/physical-intelligence/libero)에 특화된 로봇 행동 태깅 도구입니다. **Panda 로봇의 조작 태스크 데이터**를 직접 로드하여 듀얼 카메라 뷰와 로봇 상태/액션 정보를 실시간으로 분석하고 태깅할 수 있습니다.

## 🎯 Libero 데이터셋 특징

### **데이터 구성**
- **총 프레임**: 273,465개
- **총 에피소드**: 1,693개  
- **총 태스크**: 40개
- **로봇**: Panda 7-DOF 매니퓰레이터
- **프레임레이트**: 10 FPS

### **데이터 형식**
```python
{
    "image": PIL.Image (256x256x3),          # 메인 카메라
    "wrist_image": PIL.Image (256x256x3),    # 손목 카메라  
    "state": [8개 float],                    # 로봇 상태
    "actions": [7개 float],                  # 로봇 액션
    "timestamp": float,                      # 타임스탬프
    "frame_index": int,                      # 프레임 번호
    "episode_index": int,                    # 에피소드 번호
    "task_index": int                        # 태스크 번호
}
```

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. Libero 백엔드 시작
```bash
cd backend
python libero_main.py
```

### 3. 웹 애플리케이션 접속
```
브라우저 → http://localhost:8000/libero_frontend.html
API 문서 → http://localhost:8002/docs
```

## ✨ 핵심 기능

### 🎥 **듀얼 카메라 뷰어**
- **메인 카메라**: 로봇 전체 작업 공간 시점
- **손목 카메라**: 로봇 그리퍼 근접 시점
- **동기화된 재생**: 두 카메라 뷰 동시 재생

### 🎮 **로봇 데이터 시각화**
- **로봇 상태 (8차원)**:
  ```
  [x, y, z, qx, qy, qz, qw, gripper_width]
  ```
- **로봇 액션 (7차원)**:
  ```
  [dx, dy, dz, drx, dry, drz, gripper_action]
  ```
- **실시간 업데이트**: 프레임별 상태/액션 표시

### 📊 **에피소드 브라우징**
- **태스크별 필터링**: 40개 태스크별 에피소드 분류
- **썸네일 미리보기**: 각 에피소드의 첫 프레임
- **통계 정보**: 프레임 수, 지속 시간 등

### 🏷️ **고급 태깅 시스템**
- **타임라인 태깅**: 아이폰 스타일 구간 태깅
- **행동 분류**: 로봇 manipulation 행동별 라벨링
- **메타데이터 보존**: 에피소드, 태스크 정보 유지

## 🎯 사용 방법

### **1. 에피소드 선택**
1. 태스크 필터 선택 (옵션)
2. "에피소드 로드" 클릭
3. 썸네일에서 원하는 에피소드 클릭

### **2. 행동 분석**
- **재생 제어**: 스페이스바로 재생/일시정지
- **프레임 이동**: 화살표 키 또는 타임라인 클릭
- **로봇 데이터**: 실시간 상태/액션 모니터링

### **3. 행동 태깅**
```
"새 태그 추가" → 시작/끝 프레임 설정 → 행동 이름 입력
```

**추천 태깅 카테고리**:
- `approach_object` - 물체에 접근
- `grasp_object` - 물체 잡기
- `lift_object` - 물체 들어올리기
- `move_to_target` - 목표 위치로 이동
- `place_object` - 물체 놓기
- `release_gripper` - 그리퍼 열기
- `retract` - 초기 위치로 복귀

### **4. 데이터 저장**
- **로컬 저장**: JSON 파일로 내보내기
- **서버 저장**: 세션 ID로 서버에 저장

## 🔧 API 엔드포인트

### **Libero 전용 API (포트 8002)**

```http
GET  /api/libero/info                           # 데이터셋 정보
GET  /api/libero/tasks                          # 태스크 목록
GET  /api/libero/episodes?task_index=0&limit=50 # 에피소드 목록
GET  /api/libero/episode/{episode_index}        # 에피소드 프레임들
GET  /api/libero/episode/{episode_index}/thumbnail # 에피소드 썸네일
POST /api/libero/tagging/{session_id}           # 태깅 데이터 저장
GET  /api/libero/tagging/{session_id}           # 태깅 데이터 로드
```

### **예시 요청**
```bash
# 에피소드 0의 첫 100프레임 로드
curl "http://localhost:8002/api/libero/episode/0?frame_count=100"

# 태스크 5의 에피소드들 조회
curl "http://localhost:8002/api/libero/episodes?task_index=5"
```

## 💡 고급 활용

### **1. 태스크별 행동 패턴 분석**
```python
# 태스크 0: 서랍 열기
episodes = get_episodes(task_index=0)
for episode in episodes:
    # pull_handle, open_drawer 행동 태깅
```

### **2. 그리퍼 상태 기반 분석**
```python
# 로봇 상태의 마지막 요소가 gripper_width
gripper_width = robot_state[7]
if gripper_width < 0.02:
    action_type = "grasping"
else:
    action_type = "releasing"
```

### **3. 배치 태깅 워크플로우**
1. 특정 태스크의 모든 에피소드 로드
2. 공통 행동 패턴 식별
3. 템플릿 기반 일괄 태깅
4. 개별 미세 조정

## 📊 데이터 분석 예시

### **태깅 데이터 구조**
```json
{
  "tags": [
    {
      "id": "1640995200000",
      "name": "approach_object",
      "startFrame": 0,
      "endFrame": 25,
      "description": "로봇이 목표 물체에 접근하는 구간"
    }
  ],
  "totalFrames": 150,
  "fps": 10,
  "episodeIndex": 42,
  "taskIndex": 5,
  "datasetName": "physical-intelligence/libero"
}
```

### **분석 코드 예시**
```python
import json
import numpy as np

# 태깅 데이터 로드
with open('libero_episode_42_tags.json') as f:
    data = json.load(f)

# 행동별 지속 시간 분석
for tag in data['tags']:
    duration = (tag['endFrame'] - tag['startFrame']) / data['fps']
    print(f"{tag['name']}: {duration:.1f}초")

# 행동 시퀀스 추출
sequence = []
for tag in sorted(data['tags'], key=lambda x: x['startFrame']):
    sequence.append(tag['name'])
print("행동 시퀀스:", " → ".join(sequence))
```

## 🎮 키보드 단축키

| 키 | 기능 |
|---|---|
| `스페이스바` | 재생/일시정지 |
| `←` | 이전 프레임 |
| `→` | 다음 프레임 |
| `ESC` | 태그 편집 취소 |

## 🔬 연구 활용 사례

### **1. Imitation Learning**
```python
# 태깅된 행동별 demonstration 추출
for tag in tags:
    if tag['name'] == 'grasp_object':
        demonstration = episode_data[tag['startFrame']:tag['endFrame']]
        # 모방 학습 데이터로 활용
```

### **2. Behavior Cloning**
```python
# 행동-상태 매핑으로 정책 학습
state_action_pairs = []
for frame in episode:
    state = frame['state']
    action = frame['actions'] 
    behavior_label = get_behavior_at_frame(frame_idx)
    state_action_pairs.append((state, action, behavior_label))
```

### **3. Hierarchical Planning**
```python
# 상위 레벨 행동 계획
high_level_plan = ['approach_object', 'grasp_object', 'move_to_target', 'place_object']
for behavior in high_level_plan:
    execute_behavior(behavior, robot_state)
```

## 📈 성능 최적화

### **대용량 에피소드 처리**
- **청크 로딩**: 100프레임씩 나누어 로드
- **백그라운드 캐싱**: 다음 에피소드 미리 로드
- **이미지 압축**: 표시용 해상도 최적화

### **메모리 관리**
```python
# 메모리 효율적 로딩
episode = load_episode(episode_index, frame_count=100)
# 필요시 추가 프레임 로드
if need_more_frames:
    additional_frames = load_episode(episode_index, start_frame=100, frame_count=50)
```

## 🐛 문제 해결

### **데이터셋 로딩 오류**
```bash
# HuggingFace 인증
huggingface-cli login

# 또는 토큰 설정
export HUGGINGFACE_HUB_TOKEN="your_token"
```

### **메모리 부족**
- 에피소드당 로드 프레임 수 감소 (기본 100 → 50)
- 이미지 해상도 다운샘플링
- 백그라운드 프로세스 종료

### **네트워크 연결 오류**
```bash
# 백엔드 서버 상태 확인
curl http://localhost:8002/api/libero/info

# 포트 변경 (충돌 시)
python libero_main.py --port 8003
```

## 📝 개발 로드맵

### **단기 (1-2개월)**
- [ ] 자동 행동 감지 (gripper 상태 기반)
- [ ] 태그 템플릿 시스템
- [ ] 3D 로봇 시각화

### **중기 (3-6개월)**
- [ ] 다중 에피소드 동시 분석
- [ ] 행동 유사도 분석
- [ ] Vision Transformer 기반 자동 태깅

### **장기 (6개월+)**
- [ ] 실시간 로봇 제어 연동
- [ ] VR/AR 인터페이스
- [ ] 다중 로봇 시스템 지원

## 🤝 기여하기

Libero 데이터셋 분석에 특화된 기능 제안이나 버그 리포트를 환영합니다!

1. 이슈 등록: 태깅 카테고리, 분석 기능 제안
2. 풀 리퀘스트: 새로운 시각화, 분석 도구
3. 데이터 공유: 태깅된 에피소드 데이터 기여

## 📚 참고 자료

- [Libero 데이터셋 논문](https://libero-ai.github.io/)
- [Physical Intelligence](https://www.physicalintelligence.company/)
- [HuggingFace Datasets](https://huggingface.co/datasets/physical-intelligence/libero)
- [Panda 로봇 문서](https://frankaemika.github.io/docs/)

## 📄 라이선스

MIT 라이선스 하에 배포됩니다. Libero 데이터셋은 별도의 라이선스를 따릅니다. 
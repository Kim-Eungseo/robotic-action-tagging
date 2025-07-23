from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import base64
import io
from PIL import Image
import numpy as np

app = FastAPI(title="Simple Libero Test API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_dummy_image(text="Test", size=(256, 256)):
    """테스트용 더미 이미지 생성"""
    img = Image.new("RGB", size, color=(64, 64, 64))
    # 간단한 텍스트나 패턴 추가 (선택사항)
    return img


def image_to_base64(img):
    """PIL 이미지를 base64로 변환"""
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


@app.get("/")
async def read_root():
    return {"message": "Simple Libero Test API 실행 중"}


@app.get("/api/libero/info")
async def get_libero_info():
    """테스트용 Libero 정보"""
    return {
        "name": "physical-intelligence/libero",
        "description": "Libero 로봇 조작 벤치마크 데이터셋 (테스트 모드)",
        "total_frames": 273465,
        "total_episodes": 1693,
        "total_tasks": 40,
        "fps": 10,
        "robot_type": "panda",
        "status": "test_mode",
    }


@app.get("/api/libero/tasks")
async def get_tasks():
    """테스트용 태스크 목록"""
    return [
        {"task_index": i, "episode_count": 50, "frame_count": 1000} for i in range(10)
    ]


@app.get("/api/libero/episodes")
async def get_episodes():
    """테스트용 에피소드 목록"""
    return [
        {
            "episode_index": i,
            "task_index": i % 5,
            "frame_count": 100 + i * 10,
            "start_timestamp": 0.0,
            "end_timestamp": 10.0 + i,
        }
        for i in range(20)
    ]


@app.get("/api/libero/episode/{episode_index}")
async def get_episode(episode_index: int, start_frame: int = 0, frame_count: int = 100):
    """테스트용 에피소드 프레임 데이터"""

    # 더미 프레임 데이터 생성
    frames = []
    total_frames = min(frame_count, 50)  # 최대 50프레임

    for i in range(total_frames):
        # 메인 카메라 이미지 (로봇 작업 시뮬레이션)
        main_img = create_dummy_image(f"Main {i}", (256, 256))

        # 손목 카메라 이미지 (그리퍼 시뮬레이션)
        wrist_img = create_dummy_image(f"Wrist {i}", (256, 256))

        # 로봇 상태 (8차원: x,y,z,qx,qy,qz,qw,gripper)
        state = [
            0.5 + 0.1 * np.sin(i * 0.1),  # x
            0.0 + 0.05 * np.cos(i * 0.1),  # y
            0.3 + 0.02 * i / total_frames,  # z
            0.0,
            0.0,
            0.0,
            1.0,  # quaternion
            0.05 - 0.04 * (i / total_frames),  # gripper_width
        ]

        # 로봇 액션 (7차원: dx,dy,dz,drx,dry,drz,gripper_cmd)
        actions = [
            0.01 * np.sin(i * 0.2),  # dx
            0.01 * np.cos(i * 0.2),  # dy
            0.005,  # dz
            0.0,
            0.0,
            0.0,  # rotations
            -1 if i > total_frames / 2 else 1,  # gripper command
        ]

        frame_data = {
            "image": image_to_base64(main_img),
            "wrist_image": image_to_base64(wrist_img),
            "state": state,
            "actions": actions,
            "timestamp": i * 0.1,
            "frame_index": start_frame + i,
            "episode_index": episode_index,
            "task_index": episode_index % 5,
        }
        frames.append(frame_data)

    return {
        "frames": frames,
        "episode_index": episode_index,
        "task_index": episode_index % 5,
        "total_frames": total_frames,
        "metadata": {
            "episode_index": episode_index,
            "task_index": episode_index % 5,
            "total_frames_in_episode": total_frames,
            "returned_frames": len(frames),
            "start_frame": start_frame,
            "duration": total_frames * 0.1,
        },
    }


@app.get("/api/libero/episode/{episode_index}/thumbnail")
async def get_episode_thumbnail(episode_index: int):
    """테스트용 에피소드 썸네일"""

    # 썸네일 이미지 생성
    thumb_img = create_dummy_image(f"Episode {episode_index}", (256, 256))

    return {
        "episode_index": episode_index,
        "task_index": episode_index % 5,
        "thumbnail": image_to_base64(thumb_img),
    }


@app.post("/api/libero/tagging/{session_id}")
async def save_tagging_data(session_id: str, data: dict):
    """테스트용 태깅 데이터 저장"""
    return {"message": f"태깅 데이터 저장됨 (테스트 모드)", "session_id": session_id}


if __name__ == "__main__":
    import uvicorn

    print("🧪 Enhanced Libero Test Server 시작 중...")
    uvicorn.run(app, host="0.0.0.0", port=8002)

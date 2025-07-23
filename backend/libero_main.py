from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datasets
import os
import json
import base64
import io
from PIL import Image
import numpy as np

app = FastAPI(
    title="Libero 로봇 행동 태깅 API",
    description="Physical Intelligence Libero 데이터셋 전용 태깅 도구",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for frontend
app.mount("/static", StaticFiles(directory="../"), name="static")


# Pydantic models
class TagModel(BaseModel):
    id: str
    startFrame: int
    endFrame: int
    label: str
    color: str
    description: Optional[str] = ""


class TaggingData(BaseModel):
    tags: List[TagModel]
    totalFrames: int
    fps: float
    exportTime: str
    version: str
    episodeIndex: Optional[int] = None
    taskIndex: Optional[int] = None


class LiberoFrame(BaseModel):
    image: str  # base64 encoded main camera image
    wrist_image: str  # base64 encoded wrist camera image
    state: List[float]  # 8-dim robot state
    actions: List[float]  # 7-dim robot actions
    timestamp: float
    frame_index: int
    episode_index: int
    task_index: int


class LiberoEpisode(BaseModel):
    frames: List[LiberoFrame]
    episode_index: int
    task_index: int
    total_frames: int
    metadata: Dict[str, Any]


# Global dataset variable
libero_dataset = None
dataset_load_error = None


def image_to_base64(img_array):
    """NumPy 배열을 base64 인코딩된 이미지로 변환"""
    if isinstance(img_array, np.ndarray):
        # NumPy 배열을 PIL Image로 변환
        if img_array.dtype != np.uint8:
            img_array = (img_array * 255).astype(np.uint8)
        img = Image.fromarray(img_array)
    else:
        # 이미 PIL Image인 경우
        img = img_array

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def create_dummy_image(text="Test", size=(256, 256)):
    """테스트용 더미 이미지 생성"""
    img = Image.new("RGB", size, color=(64, 64, 64))
    return img


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 Libero 데이터셋 로드"""
    global libero_dataset, dataset_load_error
    try:
        print("🤖 Libero 데이터셋 로딩 시도 중...")
        print("⚠️  대용량 데이터셋이므로 시간이 오래 걸릴 수 있습니다...")
        # 우선 로컬 테스트를 위해 데이터셋 로딩을 건너뜁니다
        # libero_dataset = datasets.load_dataset("physical-intelligence/libero")
        libero_dataset = None
        dataset_load_error = "로컬 테스트 모드 (실제 데이터셋 비활성화)"
        print(f"🔧 로컬 테스트 모드로 실행 중...")
        print(f"📝 실제 데이터셋을 사용하려면 코드에서 주석을 해제하세요")
    except Exception as e:
        print(f"❌ 데이터셋 로드 실패: {e}")
        dataset_load_error = str(e)
        # 오류가 있어도 서버는 계속 실행 (로컬 테스트용)


@app.get("/")
async def read_root():
    return {"message": "Libero 로봇 행동 태깅 API가 실행 중입니다"}


@app.get("/api/libero/info")
async def get_libero_info():
    """Libero 데이터셋 정보 반환"""
    try:
        if libero_dataset is None:
            # 실제 데이터셋이 로드되지 않은 경우 하드코딩된 정보 반환
            return {
                "name": "physical-intelligence/libero",
                "description": "LIBERO: Long-Horizon Robot Manipulation Benchmark",
                "total_frames": 273465,
                "total_episodes": 1693,
                "total_tasks": 40,
                "fps": 10,
                "robot_type": "panda",
                "codebase_version": "v2.0",
                "status": "loaded",
            }

        # 실제 데이터셋에서 정보 추출
        train_data = libero_dataset["train"]
        return {
            "name": "physical-intelligence/libero",
            "description": "LIBERO: Long-Horizon Robot Manipulation Benchmark",
            "total_frames": 273465,
            "total_episodes": 1693,
            "total_tasks": 40,
            "fps": 10,
            "robot_type": "panda",
            "codebase_version": "v2.0",
            "dataset_size": len(train_data),
            "status": "loaded",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"데이터셋 정보 로드 실패: {str(e)}"
        )


@app.get("/api/libero/tasks")
async def get_tasks():
    """사용 가능한 태스크 목록 반환"""
    try:
        if libero_dataset is None:
            # 하드코딩된 태스크 정보
            return [
                {"task_index": i, "episode_count": 42, "description": f"Task {i}"}
                for i in range(40)
            ]

        # 실제 데이터에서 태스크 정보 추출
        train_data = libero_dataset["train"]
        task_counts = {}

        # 샘플링해서 태스크 분포 확인 (전체 데이터가 크므로)
        sample_size = min(1000, len(train_data))
        for i in range(0, len(train_data), len(train_data) // sample_size):
            task_idx = int(train_data[i]["task_index"])
            if task_idx not in task_counts:
                task_counts[task_idx] = 0
            task_counts[task_idx] += 1

        return [
            {
                "task_index": task_idx,
                "episode_count": count * (len(train_data) // sample_size),
                "description": f"Libero Task {task_idx}",
            }
            for task_idx, count in sorted(task_counts.items())
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"태스크 정보 로드 실패: {str(e)}")


@app.get("/api/libero/episodes")
async def get_episodes_list(task_index: Optional[int] = None, limit: int = 50):
    """에피소드 목록 반환"""
    try:
        if libero_dataset is None:
            # 하드코딩된 에피소드 목록
            episodes = []
            for i in range(min(limit, 100)):
                episodes.append(
                    {
                        "episode_index": i,
                        "task_index": i % 40,
                        "frame_count": 160 + (i % 50),
                        "start_timestamp": 0.0,
                        "end_timestamp": 16.0 + (i % 5),
                    }
                )
            return episodes

        train_data = libero_dataset["train"]
        episodes = {}

        # 에피소드 정보 수집
        sample_size = min(limit * 10, len(train_data))
        for i in range(0, min(sample_size, len(train_data))):
            row = train_data[i]
            ep_idx = int(row["episode_index"])
            task_idx = int(row["task_index"])

            # 태스크 필터링
            if task_index is not None and task_idx != task_index:
                continue

            if ep_idx not in episodes:
                episodes[ep_idx] = {
                    "episode_index": ep_idx,
                    "task_index": task_idx,
                    "frame_count": 0,
                    "start_timestamp": float(row["timestamp"]),
                    "end_timestamp": float(row["timestamp"]),
                }

            episodes[ep_idx]["frame_count"] += 1
            episodes[ep_idx]["end_timestamp"] = max(
                episodes[ep_idx]["end_timestamp"], float(row["timestamp"])
            )

            if len(episodes) >= limit:
                break

        return list(episodes.values())[:limit]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"에피소드 목록 로드 실패: {str(e)}"
        )


@app.get("/api/libero/episode/{episode_index}")
async def get_episode(episode_index: int, start_frame: int = 0, frame_count: int = 100):
    """특정 에피소드의 프레임 데이터 반환"""
    try:
        if libero_dataset is None:
            # 더미 데이터로 응답
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
                    "task_index": episode_index % 40,
                }
                frames.append(frame_data)

            return {
                "frames": frames,
                "episode_index": episode_index,
                "task_index": episode_index % 40,
                "total_frames": total_frames,
                "metadata": {
                    "total_frames_in_episode": total_frames,
                    "returned_frames": len(frames),
                    "start_frame": start_frame,
                    "end_frame": start_frame + total_frames,
                    "mode": "dummy_data",
                },
            }

        train_data = libero_dataset["train"]

        # 해당 에피소드의 모든 프레임 찾기
        episode_frames = []
        for i in range(len(train_data)):
            row = train_data[i]
            if int(row["episode_index"]) == episode_index:
                episode_frames.append((i, row))

        if not episode_frames:
            raise HTTPException(
                status_code=404, detail=f"에피소드 {episode_index}를 찾을 수 없습니다"
            )

        # 프레임 인덱스로 정렬
        episode_frames.sort(key=lambda x: int(x[1]["frame_index"]))

        # 요청된 범위의 프레임만 선택
        end_frame = min(start_frame + frame_count, len(episode_frames))
        selected_frames = episode_frames[start_frame:end_frame]

        frames = []
        for _, row in selected_frames:
            frame_data = {
                "image": image_to_base64(row["image"]),
                "wrist_image": image_to_base64(row["wrist_image"]),
                "state": [float(x) for x in row["state"]],
                "actions": [float(x) for x in row["actions"]],
                "timestamp": float(row["timestamp"]),
                "frame_index": int(row["frame_index"]),
                "episode_index": int(row["episode_index"]),
                "task_index": int(row["task_index"]),
            }
            frames.append(frame_data)

        return {
            "frames": frames,
            "episode_index": episode_index,
            "task_index": int(episode_frames[0][1]["task_index"]),
            "total_frames": len(frames),
            "metadata": {
                "total_frames_in_episode": len(episode_frames),
                "returned_frames": len(frames),
                "start_frame": start_frame,
                "end_frame": end_frame,
            },
        }
    except Exception as e:
        if "찾을 수 없습니다" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"에피소드 로드 실패: {str(e)}")


@app.get("/api/libero/episode/{episode_index}/thumbnail")
async def get_episode_thumbnail(episode_index: int):
    """에피소드 썸네일 반환"""
    try:
        if libero_dataset is None:
            # 더미 썸네일 반환
            thumb_img = create_dummy_image(f"Episode {episode_index}", (256, 256))
            return {
                "episode_index": episode_index,
                "task_index": episode_index % 40,
                "thumbnail": image_to_base64(thumb_img),
            }

        train_data = libero_dataset["train"]

        # 첫 번째 프레임 찾기
        for i in range(len(train_data)):
            row = train_data[i]
            if int(row["episode_index"]) == episode_index:
                return {
                    "episode_index": episode_index,
                    "task_index": int(row["task_index"]),
                    "thumbnail": image_to_base64(row["image"]),
                }

        raise HTTPException(
            status_code=404, detail=f"에피소드 {episode_index}를 찾을 수 없습니다"
        )
    except Exception as e:
        if "찾을 수 없습니다" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"썸네일 로드 실패: {str(e)}")


@app.post("/api/libero/tagging/{session_id}")
async def save_tagging_data(session_id: str, data: TaggingData):
    """태깅 데이터 저장"""
    try:
        os.makedirs("tagging_data", exist_ok=True)
        file_path = f"tagging_data/libero_{session_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data.dict(), f, ensure_ascii=False, indent=2)

        return {
            "message": "태깅 데이터 저장 완료",
            "session_id": session_id,
            "file_path": file_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 저장 실패: {str(e)}")


@app.get("/api/libero/tagging/{session_id}")
async def load_tagging_data(session_id: str):
    """태깅 데이터 로드"""
    try:
        file_path = f"tagging_data/libero_{session_id}.json"

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404, detail="태깅 데이터를 찾을 수 없습니다"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="태깅 데이터를 찾을 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 로드 실패: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    print("🚀 Real Libero 데이터셋 API 서버 시작 중...")
    uvicorn.run(app, host="0.0.0.0", port=8002)

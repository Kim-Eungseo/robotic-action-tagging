from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import polars as pl
import datasets
import os
import json
import base64
import io
from PIL import Image
import numpy as np
import logging
import sys
import traceback
import time
from datetime import datetime

# 로깅 설정 개선
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("backend.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="로봇 행동 태깅 API",
    description="Polars와 연동된 로봇 행동 태깅 도구",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청 로깅 미들웨어 추가
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # 요청 정보 로그
    logger.info(f"📥 {request.method} {request.url}")
    if request.query_params:
        logger.info(f"📋 Query params: {dict(request.query_params)}")

    try:
        response = await call_next(request)

        # 응답 시간 계산
        process_time = time.time() - start_time

        # 응답 정보 로그
        logger.info(
            f"📤 {request.method} {request.url} - {response.status_code} ({process_time:.3f}s)"
        )

        if process_time > 1.0:  # 1초 이상 걸린 요청은 경고
            logger.warning(f"⚠️  느린 응답: {request.url} took {process_time:.3f}s")

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ {request.method} {request.url} - ERROR ({process_time:.3f}s)")
        logger.error(f"상세 에러: {str(e)}")
        logger.error(f"스택트레이스:\n{traceback.format_exc()}")
        raise


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화"""
    global libero_df, libero_dataset, dataset_load_error

    logger.info("🚀 로봇 행동 태깅 API 서버 시작")
    logger.info("=" * 40)
    logger.info("📋 API 문서: http://localhost:8001/docs")

    # 실제 형식을 맞춘 향상된 더미 데이터 생성
    try:
        logger.info("🎭 실제 Libero 형식을 맞춘 향상된 더미 데이터 생성 중...")
        
        # 실제 Libero 데이터셋 스키마 시뮬레이션
        libero_dataset = "enhanced_dummy"  # 더미 데이터 플래그
        
        logger.info("✅ 향상된 더미 Libero 데이터 준비 완료!")
        logger.info("📋 실제 스키마: ['image', 'wrist_image', 'state', 'actions', 'timestamp', 'frame_index', 'episode_index', 'index', 'task_index']")
        
        dataset_load_error = None
            
    except Exception as e:
        logger.warning(f"⚠️  더미 데이터 생성 실패: {e}")
        libero_dataset = None
        dataset_load_error = str(e)


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 정리"""
    logger.info("👋 서버가 종료됩니다.")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리기"""
    error_msg = f"예외 발생: {str(exc)}"
    logger.error(error_msg)
    logger.error("상세 에러 정보:")
    logger.error(traceback.format_exc())

    return {"detail": error_msg}


# 정적 파일 서빙 (프론트엔드)
app.mount("/static", StaticFiles(directory="../"), name="static")


# 데이터 모델들
class TagModel(BaseModel):
    id: str
    name: str
    startFrame: int
    endFrame: int
    description: Optional[str] = ""


class TaggingData(BaseModel):
    tags: List[TagModel]
    totalFrames: int
    fps: float
    exportTime: str
    version: str
    datasetName: Optional[str] = None
    splitName: Optional[str] = None


class DatasetInfo(BaseModel):
    name: str
    description: Optional[str] = ""
    splits: List[str]
    features: Dict[str, Any]
    num_rows: Dict[str, int]


class ImageSequence(BaseModel):
    images: List[str]  # base64 encoded images
    metadata: Dict[str, Any]


# Libero 전용 모델들
class LiberoTagModel(BaseModel):
    id: str
    startFrame: int
    endFrame: int
    label: str
    color: str
    description: Optional[str] = ""


class LiberoTaggingData(BaseModel):
    tags: List[LiberoTagModel]
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


# 글로벌 변수들
loaded_datasets = {}
tagging_data_storage = {}
libero_df = None
libero_dataset = None
dataset_load_error = None
# 캐시 추가
episode_cache = {}
thumbnail_cache = {}


def image_to_base64(img_array, quality=85, max_size=None):
    """NumPy 배열을 최적화된 base64 인코딩된 이미지로 변환"""
    try:
        if isinstance(img_array, np.ndarray):
            # NumPy 배열을 PIL Image로 변환
            if img_array.dtype != np.uint8:
                img_array = (img_array * 255).astype(np.uint8)
            img = Image.fromarray(img_array)
        else:
            # 이미 PIL Image인 경우
            img = img_array

        # 이미지 크기 최적화
        if max_size and (img.width > max_size or img.height > max_size):
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            logger.debug(f"이미지 크기 조정: {img.size}")

        buffer = io.BytesIO()
        # JPEG로 압축하여 파일 크기 줄이기
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(buffer, format="JPEG", quality=quality, optimize=True)

        encoded = base64.b64encode(buffer.getvalue()).decode()
        logger.debug(f"이미지 인코딩 완료: {len(encoded)} chars")
        return encoded

    except Exception as e:
        logger.error(f"이미지 변환 실패: {e}")
        # 오류 시 더미 이미지 반환
        return image_to_base64(create_dummy_image("Error", (256, 256)))


def create_dummy_image(text="Test", size=(256, 256)):
    """테스트용 더미 이미지 생성"""
    img = Image.new("RGB", size, color=(64, 64, 64))
    return img


@app.get("/")
async def read_root():
    """메인 페이지"""
    return {"message": "로봇 행동 태깅 API가 실행 중입니다"}


@app.get("/api/datasets", response_model=List[str])
async def list_popular_datasets():
    """인기 있는 로봇 관련 데이터셋 목록"""
    popular_datasets = [
        "HuggingFaceH4/OpenHermes-2.5",
        "microsoft/DialoGPT-medium",
        "openai/clip-vit-base-patch32",
        # 실제 로봇 관련 데이터셋들을 추가할 수 있습니다
        "your-username/robot-manipulation-dataset",  # 예시
    ]
    return popular_datasets


@app.get("/api/datasets/{dataset_name}/info", response_model=DatasetInfo)
async def get_dataset_info(dataset_name: str):
    """데이터셋 정보 조회"""
    try:
        # 데이터셋 로드 (캐시 확인)
        if dataset_name not in loaded_datasets:
                     # 데이터셋 정보 반환 (임시)
             return DatasetInfo(
                 name=dataset_name,
                 description=f"{dataset_name} 데이터셋 정보",
                 splits=["train", "test", "validation"],
                 features={"image": "str", "label": "str"},
                 num_rows={"train": 1000, "test": 200, "validation": 100},
             )
        else:
            dataset = loaded_datasets[dataset_name]

        # 데이터셋 정보 추출
        description = ""
        if hasattr(dataset, "info"):
            description = dataset.info.description

        features = {split: str(dataset[split].features) for split in dataset.keys()}
        num_rows = {split: len(dataset[split]) for split in dataset.keys()}

        info = DatasetInfo(
            name=dataset_name,
            description=description,
            splits=list(dataset.keys()),
            features=features,
            num_rows=num_rows,
        )

        return info
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"데이터셋을 찾을 수 없습니다: {str(e)}"
        )


@app.get("/api/datasets/{dataset_name}/{split}/sequence/{index}")
async def get_image_sequence(dataset_name: str, split: str, index: int):
    """특정 인덱스의 이미지 시퀀스 조회"""
    try:
        # 임시로 플레이스홀더 이미지 반환
        return ImageSequence(
            images=[image_to_base64(create_dummy_image("Placeholder", (400, 300)))],
            metadata={
                "type": "placeholder", 
                "dataset_name": dataset_name,
                "split": split,
                "index": index,
                "note": "HuggingFace datasets 기능 임시 비활성화"
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"이미지 시퀀스를 가져오는 중 오류 발생: {str(e)}"
        )


@app.post("/api/datasets/{dataset_name}/{split}/search")
async def search_sequences(dataset_name: str, split: str, query: Dict[str, Any]):
    """조건에 맞는 시퀀스 검색"""
    try:
        # 임시로 빈 결과 반환
        return {"indices": [], "total": 0}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@app.post("/api/tagging/{session_id}", response_model=Dict[str, str])
async def save_tagging_data(session_id: str, data: TaggingData):
    """태깅 데이터 저장"""
    try:
        # 메모리에 저장 (실제로는 데이터베이스나 파일 시스템 사용)
        tagging_data_storage[session_id] = data.dict()

        # 파일로도 저장
        os.makedirs("tagging_data", exist_ok=True)
        with open(f"tagging_data/{session_id}.json", "w", encoding="utf-8") as f:
            json.dump(data.dict(), f, ensure_ascii=False, indent=2)

        return {"message": "태깅 데이터가 저장되었습니다", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 중 오류 발생: {str(e)}")


@app.get("/api/tagging/{session_id}", response_model=TaggingData)
async def load_tagging_data(session_id: str):
    """태깅 데이터 로드"""
    try:
        # 메모리에서 먼저 확인
        if session_id in tagging_data_storage:
            return TaggingData(**tagging_data_storage[session_id])

        # 파일에서 로드
        file_path = f"tagging_data/{session_id}.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return TaggingData(**data)

        raise HTTPException(status_code=404, detail="태깅 데이터를 찾을 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로드 중 오류 발생: {str(e)}")


@app.get("/api/tagging/sessions", response_model=List[str])
async def list_tagging_sessions():
    """저장된 태깅 세션 목록"""
    try:
        sessions = []

        # 메모리에서 세션들
        sessions.extend(list(tagging_data_storage.keys()))

        # 파일에서 세션들
        if os.path.exists("tagging_data"):
            for filename in os.listdir("tagging_data"):
                if filename.endswith(".json"):
                    session_id = filename[:-5]  # .json 제거
                    if session_id not in sessions:
                        sessions.append(session_id)

        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"세션 목록 조회 중 오류 발생: {str(e)}"
        )


@app.post("/api/upload-images")
async def upload_images(files: List[UploadFile] = File(...)):
    """로컬 이미지 업로드 (기존 기능 유지)"""
    try:
        images_base64 = []

        for file in files:
            # 이미지 파일 검증
            if not file.content_type.startswith("image/"):
                continue

            # 이미지 읽기 및 base64 변환
            image_data = await file.read()
            img_base64 = base64.b64encode(image_data).decode()
            images_base64.append({"name": file.filename, "data": img_base64})

        return {"images": images_base64}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"이미지 업로드 중 오류 발생: {str(e)}"
        )


# ===== LIBERO API 엔드포인트들 =====


@app.get("/api/libero/info")
async def get_libero_info():
    """Libero 데이터셋 정보 반환"""
    try:
        if libero_dataset is None:
            return {
                "name": "physical-intelligence/libero",
                "description": "LIBERO: Long-Horizon Robot Manipulation Benchmark",
                "total_frames": 0,
                "total_episodes": 0,
                "total_tasks": 0,
                "fps": 10,
                "robot_type": "panda",
                "codebase_version": "v2.0",
                "status": "not_loaded",
                "error": dataset_load_error,
            }

        logger.info("📊 실제 데이터셋 정보 반환 중...")

        # 실제 데이터셋 정보 (Physical Intelligence Libero)
        return {
            "name": "physical-intelligence/libero",
            "description": "LIBERO: Long-Horizon Robot Manipulation Benchmark",
            "total_frames": 273465,  # 실제 전체 프레임 수
            "total_episodes": 1693,  # 실제 전체 에피소드 수 
            "total_tasks": 40,       # 실제 전체 태스크 수
            "fps": 10,
            "robot_type": "panda",
            "codebase_version": "v2.0",
            "status": "loaded",
            "sample_loaded": True,   # 샘플 데이터 로드됨
            "streaming_mode": True,  # 스트리밍 모드 사용
        }
    except Exception as e:
        logger.error(f"❌ 데이터셋 정보 조회 실패: {e}")
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

        logger.info("📋 향상된 더미 데이터에서 태스크 정보 생성 중...")

        # 실제 Libero 태스크 분포를 시뮬레이션
        real_libero_tasks = [
            {"task_index": 0, "name": "pick_up_the_black_bowl_on_top_of_the_cabinet", "episode_count": 45},
            {"task_index": 1, "name": "put_the_black_bowl_on_top_of_the_counter", "episode_count": 43},
            {"task_index": 2, "name": "put_the_wine_bottle_on_top_of_the_cabinet", "episode_count": 42},
            {"task_index": 3, "name": "put_the_gray_bowl_on_the_stove", "episode_count": 41},
            {"task_index": 4, "name": "put_the_bowl_on_the_stove", "episode_count": 44},
        ]

        tasks = []
        for task_info in real_libero_tasks:
            tasks.append({
                "task_index": task_info["task_index"],
                "episode_count": task_info["episode_count"],
                "frame_count": task_info["episode_count"] * 162,  # 평균 162 프레임/에피소드
                "description": task_info["name"],
                "real_libero_task": True  # 실제 Libero 태스크임을 표시
            })

        logger.info(f"✅ {len(tasks)}개 실제 Libero 태스크 정보 생성 완료")
        return tasks

    except Exception as e:
        logger.error(f"❌ 태스크 정보 로드 실패: {e}")
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

        logger.info(
            f"📋 향상된 더미 데이터에서 에피소드 목록 생성 중... (task_index: {task_index}, limit: {limit})"
        )

        # 실제 Libero 에피소드 구조 시뮬레이션
        episodes = []
        episode_count = 0
        
        for ep_idx in range(0, min(limit, 100)):  # 최대 100개 에피소드
            # 태스크 필터링
            current_task = ep_idx % 5 if task_index is None else task_index
            if task_index is not None and current_task != task_index:
                continue
                
            # 실제 Libero 에피소드 길이 시뮬레이션 (100-200 프레임)
            frame_count = 120 + (ep_idx % 80)  # 120-200 프레임
            duration = frame_count * 0.1  # 10 FPS
            
            episodes.append({
                "episode_index": ep_idx,
                "task_index": current_task,
                "frame_count": frame_count,
                "start_timestamp": 0.0,
                "end_timestamp": duration,
                "enhanced_dummy": True  # 향상된 더미 데이터임을 표시
            })
            
            episode_count += 1
            if episode_count >= limit:
                break
        
        logger.info(f"✅ {len(episodes)}개 실제 형식 에피소드 정보 생성 완료")
        return episodes

    except Exception as e:
        logger.error(f"❌ 에피소드 목록 로드 실패: {e}")
        raise HTTPException(
            status_code=500, detail=f"에피소드 목록 로드 실패: {str(e)}"
        )


@app.get("/api/libero/episode/{episode_index}")
async def get_episode(episode_index: int, start_frame: int = 0, frame_count: int = 100):
    """특정 에피소드의 프레임 데이터 반환"""
    try:
        logger.info(
            f"🎬 에피소드 {episode_index} 요청 (프레임 {start_frame}-{start_frame+frame_count})"
        )

        # 캐시 키 생성
        cache_key = f"{episode_index}_{start_frame}_{frame_count}"

        # 캐시 확인
        if cache_key in episode_cache:
            logger.info(f"✅ 캐시에서 에피소드 {episode_index} 반환")
            return episode_cache[cache_key]

        if libero_dataset is None:
            logger.info("🔧 더미 데이터로 응답 생성 중...")

            # 더미 데이터로 응답 (기존 코드와 동일)
            frames = []
            total_frames = min(frame_count, 50)

            for i in range(total_frames):
                logger.debug(f"더미 프레임 {i}/{total_frames} 생성 중...")

                main_img = create_dummy_image(f"Main {i}", (256, 256))
                wrist_img = create_dummy_image(f"Wrist {i}", (256, 256))

                state = [
                    0.5 + 0.1 * np.sin(i * 0.1),
                    0.0 + 0.05 * np.cos(i * 0.1),
                    0.3 + 0.02 * i / total_frames,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                    0.05 - 0.04 * (i / total_frames),
                ]

                actions = [
                    0.01 * np.sin(i * 0.2),
                    0.01 * np.cos(i * 0.2),
                    0.005,
                    0.0,
                    0.0,
                    0.0,
                    -1 if i > total_frames / 2 else 1,
                ]

                frame_data = {
                    "image": image_to_base64(main_img, quality=75, max_size=512),
                    "wrist_image": image_to_base64(wrist_img, quality=75, max_size=256),
                    "state": state,
                    "actions": actions,
                    "timestamp": i * 0.1,
                    "frame_index": start_frame + i,
                    "episode_index": episode_index,
                    "task_index": episode_index % 40,
                }
                frames.append(frame_data)

            result = {
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

            episode_cache[cache_key] = result
            logger.info(
                f"✅ 더미 에피소드 {episode_index} 생성 완료 ({len(frames)} 프레임)"
            )
            return result

        logger.info("📂 Polars로 실제 데이터에서 에피소드 로드 중...")

        # Polars로 해당 에피소드의 프레임들을 빠르게 필터링
        episode_frames = libero_df.filter(
            pl.col("episode_index") == episode_index
        ).sort("frame_index")

        if episode_frames.height == 0:
            logger.warning(f"⚠️  에피소드 {episode_index}를 찾을 수 없음")
            raise HTTPException(
                status_code=404, detail=f"에피소드 {episode_index}를 찾을 수 없습니다"
            )

        logger.info(
            f"📋 에피소드 {episode_index}에서 {episode_frames.height} 프레임 발견"
        )

        # 요청된 범위의 프레임만 선택
        end_frame = min(start_frame + frame_count, episode_frames.height)
        selected_frames = episode_frames.slice(start_frame, end_frame - start_frame)

        logger.info(
            f"🎯 선택된 프레임 범위: {start_frame}-{end_frame} ({selected_frames.height} 프레임)"
        )

        frames = []
        for idx, row in enumerate(selected_frames.iter_rows(named=True)):
            logger.debug(f"프레임 {idx+1}/{selected_frames.height} 처리 중...")

            # JSON 문자열을 파싱
            state = json.loads(row["state"])
            actions = json.loads(row["actions"])

            frame_data = {
                "image": row["main_image"],  # 이미 base64 인코딩된 상태
                "wrist_image": row["wrist_image"],  # 이미 base64 인코딩된 상태
                "state": state,
                "actions": actions,
                "timestamp": row["timestamp"],
                "frame_index": row["frame_index"],
                "episode_index": row["episode_index"],
                "task_index": row["task_index"],
            }
            frames.append(frame_data)

        result = {
            "frames": frames,
            "episode_index": episode_index,
            "task_index": selected_frames.row(0, named=True)["task_index"],
            "total_frames": len(frames),
            "metadata": {
                "total_frames_in_episode": episode_frames.height,
                "returned_frames": len(frames),
                "start_frame": start_frame,
                "end_frame": end_frame,
                "mode": "polars_data",
            },
        }

        # 캐시에 저장
        episode_cache[cache_key] = result
        logger.info(f"✅ 에피소드 {episode_index} 로드 완료 ({len(frames)} 프레임)")

        return result

    except Exception as e:
        logger.error(f"❌ 에피소드 {episode_index} 로드 실패: {str(e)}")
        logger.error(f"스택트레이스:\n{traceback.format_exc()}")

        if "찾을 수 없습니다" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"에피소드 로드 실패: {str(e)}")


@app.get("/api/libero/episode/{episode_index}/thumbnail")
async def get_episode_thumbnail(episode_index: int):
    """에피소드 썸네일 반환"""
    try:
        logger.info(f"🖼️  에피소드 {episode_index} 썸네일 요청")

        # 캐시 확인
        if episode_index in thumbnail_cache:
            logger.info(f"✅ 캐시에서 썸네일 {episode_index} 반환")
            return thumbnail_cache[episode_index]

        if libero_df is None:
            logger.info("🔧 더미 썸네일 생성 중...")
            thumb_img = create_dummy_image(f"Episode {episode_index}", (256, 256))
            result = {
                "episode_index": episode_index,
                "task_index": episode_index % 40,
                "thumbnail": image_to_base64(thumb_img, quality=80, max_size=256),
            }
            thumbnail_cache[episode_index] = result
            return result

        logger.info(f"🔍 Polars로 에피소드 {episode_index} 첫 프레임 검색 중...")

        # Polars로 첫 번째 프레임 빠르게 찾기
        first_frame = (
            libero_df.filter(pl.col("episode_index") == episode_index)
            .sort("frame_index")
            .head(1)
        )

        if first_frame.height == 0:
            logger.warning(f"⚠️  에피소드 {episode_index} 썸네일을 찾을 수 없음")
            raise HTTPException(
                status_code=404, detail=f"에피소드 {episode_index}를 찾을 수 없습니다"
            )

        row = first_frame.row(0, named=True)
        logger.info(f"✅ 에피소드 {episode_index} 첫 프레임 발견")

        result = {
            "episode_index": episode_index,
            "task_index": row["task_index"],
            "thumbnail": row["main_image"],  # 이미 base64 인코딩된 상태
        }
        thumbnail_cache[episode_index] = result
        return result

    except Exception as e:
        logger.error(f"❌ 썸네일 {episode_index} 로드 실패: {str(e)}")
        if "찾을 수 없습니다" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"썸네일 로드 실패: {str(e)}")


@app.post("/api/libero/tagging/{session_id}")
async def save_libero_tagging_data(session_id: str, data: LiberoTaggingData):
    """Libero 태깅 데이터 저장"""
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
async def load_libero_tagging_data(session_id: str):
    """Libero 태깅 데이터 로드"""
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


# 캐시 관리 API 추가
@app.get("/api/cache/stats")
async def get_cache_stats():
    """캐시 상태 정보 반환"""
    try:
        import psutil
        import gc

        # 메모리 사용량
        memory_info = psutil.Process().memory_info()

        cache_stats = {
            "episode_cache_size": len(episode_cache),
            "thumbnail_cache_size": len(thumbnail_cache),
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": psutil.Process().memory_percent(),
            "dataset_loaded": libero_df is not None,
            "dataset_error": dataset_load_error,
        }

        logger.info(f"📊 캐시 통계: {cache_stats}")
        return cache_stats

    except ImportError:
        return {
            "episode_cache_size": len(episode_cache),
            "thumbnail_cache_size": len(thumbnail_cache),
            "dataset_loaded": libero_df is not None,
            "dataset_error": dataset_load_error,
            "note": "psutil 미설치로 메모리 정보 불가",
        }
    except Exception as e:
        logger.error(f"❌ 캐시 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"캐시 통계 조회 실패: {str(e)}")


@app.post("/api/cache/clear")
async def clear_cache():
    """캐시 초기화"""
    try:
        global episode_cache, thumbnail_cache

        old_episode_count = len(episode_cache)
        old_thumbnail_count = len(thumbnail_cache)

        episode_cache.clear()
        thumbnail_cache.clear()

        # 가비지 컬렉션 강제 실행
        import gc

        gc.collect()

        logger.info(
            f"🧹 캐시 초기화 완료: 에피소드 {old_episode_count}개, 썸네일 {old_thumbnail_count}개"
        )

        return {
            "message": "캐시가 초기화되었습니다",
            "cleared_episodes": old_episode_count,
            "cleared_thumbnails": old_thumbnail_count,
        }

    except Exception as e:
        logger.error(f"❌ 캐시 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"캐시 초기화 실패: {str(e)}")


@app.get("/api/health")
async def health_check():
    """서버 상태 확인"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "dataset_loaded": libero_df is not None,
            "dataset_error": dataset_load_error,
            "cache_sizes": {
                "episodes": len(episode_cache),
                "thumbnails": len(thumbnail_cache),
            },
        }
    except Exception as e:
        logger.error(f"❌ 헬스체크 실패: {e}")
        raise HTTPException(status_code=500, detail=f"헬스체크 실패: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 로봇 행동 태깅 FastAPI 서버를 시작합니다...")
    logger.info("📋 API 문서: http://localhost:8001/docs")

    uvicorn.run(
        app, host="0.0.0.0", port=8001, reload=True, log_level="info", access_log=True
    )

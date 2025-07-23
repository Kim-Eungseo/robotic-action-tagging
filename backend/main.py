from fastapi import FastAPI, HTTPException, UploadFile, File
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
import logging
import sys
import traceback

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("backend.log")],
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="로봇 행동 태깅 API",
    description="Hugging Face datasets와 연동된 로봇 행동 태깅 도구",
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


@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화"""
    logger.info("🚀 로봇 행동 태깅 API 서버 시작")
    logger.info("=" * 40)
    logger.info("📋 API 문서: http://localhost:8001/docs")


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


# 글로벌 변수들
loaded_datasets = {}
tagging_data_storage = {}


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
            dataset = datasets.load_dataset(dataset_name)
            loaded_datasets[dataset_name] = dataset
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
        # 데이터셋 로드
        if dataset_name not in loaded_datasets:
            dataset = datasets.load_dataset(dataset_name)
            loaded_datasets[dataset_name] = dataset
        else:
            dataset = loaded_datasets[dataset_name]

        if split not in dataset:
            raise HTTPException(
                status_code=404, detail=f"Split '{split}'을 찾을 수 없습니다"
            )

        if index >= len(dataset[split]):
            raise HTTPException(
                status_code=404, detail=f"인덱스 {index}가 범위를 벗어났습니다"
            )

        # 데이터 아이템 가져오기
        item = dataset[split][index]

        # 이미지 데이터 처리
        images_base64 = []

        # 다양한 데이터 형식 지원
        if "images" in item:
            images = item["images"]
        elif "image" in item:
            images = [item["image"]]
        elif "frames" in item:
            images = item["frames"]
        else:
            # 텍스트나 다른 형식의 경우 플레이스홀더 이미지 생성
            placeholder_img = Image.new("RGB", (400, 300), color="gray")
            buffer = io.BytesIO()
            placeholder_img.save(buffer, format="PNG")
            images_base64.append(base64.b64encode(buffer.getvalue()).decode())

            return ImageSequence(
                images=images_base64,
                metadata={"type": "placeholder", "original_data": str(item)[:200]},
            )

        # 이미지들을 base64로 변환
        for img in images:
            if isinstance(img, Image.Image):
                # PIL Image 객체
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                images_base64.append(img_base64)
            elif isinstance(img, np.ndarray):
                # NumPy 배열
                pil_img = Image.fromarray(img.astype("uint8"))
                buffer = io.BytesIO()
                pil_img.save(buffer, format="PNG")
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                images_base64.append(img_base64)
            else:
                # 기타 형식은 스킵하거나 플레이스홀더 생성
                placeholder_img = Image.new("RGB", (400, 300), color="lightgray")
                buffer = io.BytesIO()
                placeholder_img.save(buffer, format="PNG")
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                images_base64.append(img_base64)

        # 메타데이터 추출
        metadata = {
            k: v for k, v in item.items() if k not in ["images", "image", "frames"]
        }
        metadata["dataset_name"] = dataset_name
        metadata["split"] = split
        metadata["index"] = index

        return ImageSequence(images=images_base64, metadata=metadata)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"이미지 시퀀스를 가져오는 중 오류 발생: {str(e)}"
        )


@app.post("/api/datasets/{dataset_name}/{split}/search")
async def search_sequences(dataset_name: str, split: str, query: Dict[str, Any]):
    """조건에 맞는 시퀀스 검색"""
    try:
        if dataset_name not in loaded_datasets:
            dataset = datasets.load_dataset(dataset_name)
            loaded_datasets[dataset_name] = dataset
        else:
            dataset = loaded_datasets[dataset_name]

        if split not in dataset:
            raise HTTPException(
                status_code=404, detail=f"Split '{split}'을 찾을 수 없습니다"
            )

        # 간단한 필터링 (실제로는 더 복잡한 검색 로직 구현 가능)
        filtered_indices = []
        for i, item in enumerate(dataset[split]):
            match = True
            for key, value in query.items():
                if key in item and item[key] != value:
                    match = False
                    break
            if match:
                filtered_indices.append(i)
                if len(filtered_indices) >= 50:  # 최대 50개 결과
                    break

        return {"indices": filtered_indices, "total": len(filtered_indices)}

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


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 로봇 행동 태깅 FastAPI 서버를 시작합니다...")
    logger.info("📋 API 문서: http://localhost:8001/docs")

    uvicorn.run(
        app, host="0.0.0.0", port=8001, reload=True, log_level="info", access_log=True
    )

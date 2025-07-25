"""
Hugging Face Libero 데이터셋을 Polars DataFrame으로 변환하는 스크립트
"""

import os
import sys
import logging
import polars as pl
import numpy as np
import base64
import io
from PIL import Image
import datasets
from tqdm import tqdm
import json
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def image_to_base64_optimized(img_array, quality=75, max_size=512):
    """이미지를 최적화된 base64로 변환"""
    try:
        if isinstance(img_array, np.ndarray):
            if img_array.dtype != np.uint8:
                img_array = (img_array * 255).astype(np.uint8)
            img = Image.fromarray(img_array)
        else:
            img = img_array

        # 크기 최적화
        if max_size and (img.width > max_size or img.height > max_size):
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(buffer, format="JPEG", quality=quality, optimize=True)

        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        logger.error(f"이미지 변환 실패: {e}")
        return None


def convert_libero_to_parquet(output_dir="data", sample_size=None):
    """Libero 데이터셋을 Parquet으로 변환"""
    logger.info("🤖 Libero 데이터셋 로딩 시작...")

    try:
        # 데이터셋 로드
        dataset = datasets.load_dataset("physical-intelligence/libero")
        train_data = dataset["train"]

        logger.info(f"📊 총 데이터 크기: {len(train_data)}")

        # 샘플링 (테스트용)
        if sample_size:
            indices = list(range(0, len(train_data), len(train_data) // sample_size))
            train_data = train_data.select(indices)
            logger.info(f"🎯 샘플링된 데이터 크기: {len(train_data)}")

        # 데이터 변환
        logger.info("🔄 데이터 변환 시작...")

        converted_data = []

        for i, row in enumerate(tqdm(train_data, desc="변환 중")):
            try:
                # 이미지 변환 (메인 카메라)
                main_image_b64 = image_to_base64_optimized(
                    row["image"], quality=75, max_size=512
                )

                # 이미지 변환 (손목 카메라)
                wrist_image_b64 = image_to_base64_optimized(
                    row["wrist_image"], quality=70, max_size=256
                )

                if main_image_b64 is None or wrist_image_b64 is None:
                    logger.warning(f"⚠️  인덱스 {i} 이미지 변환 실패, 스킵")
                    continue

                converted_row = {
                    "episode_index": int(row["episode_index"]),
                    "frame_index": int(row["frame_index"]),
                    "task_index": int(row["task_index"]),
                    "timestamp": float(row["timestamp"]),
                    "main_image": main_image_b64,
                    "wrist_image": wrist_image_b64,
                    "state": json.dumps(
                        [float(x) for x in row["state"]]
                    ),  # JSON 문자열로 저장
                    "actions": json.dumps(
                        [float(x) for x in row["actions"]]
                    ),  # JSON 문자열로 저장
                }

                converted_data.append(converted_row)

                # 메모리 관리를 위해 중간에 저장
                if len(converted_data) >= 1000:
                    logger.info(f"💾 중간 저장 ({len(converted_data)} 항목)")
                    save_batch(converted_data, output_dir, i // 1000)
                    converted_data = []

            except Exception as e:
                logger.error(f"❌ 인덱스 {i} 처리 실패: {e}")
                continue

        # 남은 데이터 저장
        if converted_data:
            save_batch(converted_data, output_dir, "final")

        logger.info("✅ 데이터 변환 완료!")

        # 메타데이터 저장
        metadata = {
            "total_frames": len(train_data),
            "total_episodes": len(set(row["episode_index"] for row in train_data)),
            "total_tasks": len(set(row["task_index"] for row in train_data)),
            "conversion_time": datetime.now().isoformat(),
            "sample_size": sample_size,
        }

        with open(os.path.join(output_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info("📋 메타데이터 저장 완료")

    except Exception as e:
        logger.error(f"❌ 변환 실패: {e}")
        raise


def save_batch(data, output_dir, batch_num):
    """데이터 배치를 Parquet으로 저장"""
    try:
        os.makedirs(output_dir, exist_ok=True)

        # Polars DataFrame 생성
        df = pl.DataFrame(data)

        # Parquet으로 저장
        output_path = os.path.join(output_dir, f"libero_batch_{batch_num}.parquet")
        df.write_parquet(output_path, compression="snappy")

        logger.info(f"✅ 배치 {batch_num} 저장 완료: {output_path}")

    except Exception as e:
        logger.error(f"❌ 배치 {batch_num} 저장 실패: {e}")
        raise


def merge_parquet_files(input_dir="data", output_file="data/libero_complete.parquet"):
    """여러 Parquet 파일을 하나로 합치기"""
    try:
        logger.info("🔗 Parquet 파일들 합치는 중...")

        parquet_files = [
            f for f in os.listdir(input_dir) if f.endswith(".parquet") and "batch" in f
        ]

        if not parquet_files:
            logger.error("❌ Parquet 파일을 찾을 수 없습니다")
            return

        # 첫 번째 파일로 시작
        df = pl.read_parquet(os.path.join(input_dir, parquet_files[0]))

        # 나머지 파일들 합치기
        for file in tqdm(parquet_files[1:], desc="파일 합치는 중"):
            batch_df = pl.read_parquet(os.path.join(input_dir, file))
            df = pl.concat([df, batch_df])

        # 정렬 (episode_index, frame_index 순)
        df = df.sort(["episode_index", "frame_index"])

        # 최종 파일 저장
        df.write_parquet(output_file, compression="snappy")

        logger.info(f"✅ 최종 파일 저장 완료: {output_file}")
        logger.info(f"📊 총 행 수: {len(df)}")

        return df

    except Exception as e:
        logger.error(f"❌ 파일 합치기 실패: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Libero 데이터셋을 Polars Parquet으로 변환"
    )
    parser.add_argument("--output-dir", default="data", help="출력 디렉토리")
    parser.add_argument(
        "--sample-size", type=int, help="샘플링할 데이터 크기 (테스트용)"
    )
    parser.add_argument(
        "--merge-only", action="store_true", help="기존 배치 파일들만 합치기"
    )

    args = parser.parse_args()

    if args.merge_only:
        merge_parquet_files(args.output_dir)
    else:
        # 변환 실행
        convert_libero_to_parquet(args.output_dir, args.sample_size)

        # 자동으로 합치기
        merge_parquet_files(args.output_dir)

    logger.info("🎉 모든 작업 완료!")

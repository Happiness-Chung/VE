import os
import cv2
import numpy as np

# 🔹 폴더 경로 설정
mask_folder = "/root/VE/MotionEditor/data/case-77/images"  # 원본 흑백 마스크 폴더
output_folder = "/root/VE/MotionEditor/data/case-77/images"  # 변환된 컬러 마스크 저장 폴더

# 출력 폴더 생성
os.makedirs(output_folder, exist_ok=True)

# 🔹 마스크 변환 및 저장
for filename in os.listdir(mask_folder):
    if filename.endswith((".png", ".jpg", ".jpeg", ".tif")):
        # 파일 경로 설정
        mask_path = os.path.join(mask_folder, filename)
        output_path = os.path.join(output_folder, filename)

        # 흑백 마스크 불러오기 (Grayscale)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

        if mask is None:
            print(f"⚠️ {filename} 로드 실패")
            continue

        # 🔹 흑백 이미지를 3채널 컬러 이미지로 변환 (흑백 느낌 유지)
        color_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)  # (H, W) → (H, W, 3)

        # 변환된 이미지 저장
        cv2.imwrite(output_path, color_mask)

        print(f"✅ {filename} 변환 완료, 저장됨 -> {output_path}")

print("🎉 모든 마스크 변환이 완료되었습니다!")

import os
import cv2
import numpy as np
from scipy.ndimage import label

# 🔹 파일 경로 설정
image_path = "/root/VE/MotionEditor/data/case-76/images/0004.png"  # 인물 원본 이미지
source_mask_path = "/root/VE/MotionEditor/data/case-76/man.mask/0004.png"  # 원본 인물의 마스크
target_mask_path = "/root/VE/MotionEditor/data/case-79/images/0003.png"  # 타겟 포즈의 마스크
output_dir = "/root/VE/MotionEditor/data/case-79/materials"  # 결과 저장 폴더

# 🔹 결과 폴더 생성
os.makedirs(output_dir, exist_ok=True)

# 🔹 이미지 및 마스크 로드
image = cv2.imread(image_path)
source_mask = cv2.imread(source_mask_path, cv2.IMREAD_GRAYSCALE)
target_mask = cv2.imread(target_mask_path, cv2.IMREAD_GRAYSCALE)

# ✅ 1️⃣ 타겟 마스크와 겹치는 부분만 남기기
overlap_mask = cv2.bitwise_and(source_mask, target_mask)  # 겹치는 영역
aligned_person = cv2.bitwise_and(image, image, mask=overlap_mask)  # 인물 중 겹치는 부분만 남김
cv2.imwrite(os.path.join(output_dir, "aligned_person.png"), aligned_person)

# ✅ 2️⃣ 원본 마스크에서 겹치지 않는 부분 찾기
remaining_source_mask = cv2.bitwise_xor(source_mask, overlap_mask)  # 원본 마스크에서 겹치는 부분 제외
remaining_source_mask_binary = (remaining_source_mask > 128).astype(np.uint8)  # 이진화

# ✅ 3️⃣ 타겟 마스크에서 겹치지 않는 부분 찾기
remaining_target_mask = cv2.bitwise_xor(target_mask, overlap_mask)  # 타겟 마스크에서 겹치는 부분 제외
remaining_target_mask_binary = (remaining_target_mask > 128).astype(np.uint8)  # 이진화

# ✅ 4️⃣ 원본 마스크에서 팔다리 등 "덩어리" 별로 분리
source_labels, num_source_labels = label(remaining_source_mask_binary)

if num_source_labels == 0:
    print("⚠️ 원본 마스크에서 겹치지 않는 부분이 없음.")
else:
    for i in range(1, num_source_labels + 1):  # 1부터 시작 (배경 제외)
        part_mask = (source_labels == i).astype(np.uint8) * 255  # 해당 덩어리만 남기기
        part_image = cv2.bitwise_and(image, image, mask=part_mask)  # 인물 중 해당 덩어리만 추출

        # 🔹 결과 저장
        # cv2.imwrite(os.path.join(output_dir, f"part_{i}.png"), part_image)
        # cv2.imwrite(os.path.join(output_dir, f"part_{i}_mask.png"), part_mask)

    print(f"✅ {num_source_labels}개의 원본 마스크에서 독립적인 팔다리(덩어리) 저장 완료!")

# ✅ 5️⃣ 타겟 마스크에서 "덩어리" 별로 분리
target_labels, num_target_labels = label(remaining_target_mask_binary)
num_target_labels = int(num_target_labels)  # 정수 변환

if num_target_labels == 0:
    print("⚠️ 타겟 마스크에서 겹치지 않는 부분이 없음.")
else:
    for i in range(1, num_target_labels + 1):  # 1부터 시작 (배경 제외)
        target_part_mask = (target_labels == i).astype(np.uint8) * 255  # 해당 덩어리만 남기기

        # 🔹 결과 저장 (타겟 마스크는 이미지 정보가 없으므로 마스크만 저장)
        cv2.imwrite(os.path.join(output_dir, f"target_part_{i}_mask.png"), target_part_mask)

    print(f"✅ {num_target_labels}개의 타겟 마스크에서 독립적인 팔다리(덩어리) 저장 완료!")

print(f"🎉 전처리 완료! 결과 저장 위치: {output_dir}")

import os
import cv2
import numpy as np
from scipy.interpolate import Rbf
from scipy.spatial import Delaunay

# 🔹 폴더 경로 설정
image_folder = "/root/VE/MotionEditor/data/case-68/images"  # 원본 이미지 폴더
mask_folder = "/root/VE/MotionEditor/data/case-68/man.mask"  # 원본 마스크 폴더
target_mask_folder = "/root/VE/MotionEditor/data/case-78/man.mask"  # 타겟 포즈 마스크 폴더
output_image_folder = "/root/VE/MotionEditor/data/case-78/images"  # 결과 저장 폴더

def warp_with_delaunay(img_file):
    img_path = os.path.join(image_folder, img_file)
    mask_path = os.path.join(mask_folder, img_file)
    target_mask_path = os.path.join(target_mask_folder, img_file)
    output_img_path = os.path.join(output_image_folder, img_file)

    image = cv2.imread(img_path)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    target_mask = cv2.imread(target_mask_path, cv2.IMREAD_GRAYSCALE)

    if image is None or mask is None or target_mask is None:
        print(f"⚠️ {img_file} 관련 파일 로드 실패")
        return

    # 🔹 1️⃣ 마스크에서 인물 키포인트 추출
    src_points = np.column_stack(np.where(mask > 128))  # 원본 마스크 좌표 (y, x)
    dst_points = np.column_stack(np.where(target_mask > 128))  # 타겟 마스크 좌표 (y, x)

    # 🔹 2️⃣ Delaunay 삼각형 분할
    tri = Delaunay(src_points)

    # 🔹 3️⃣ 새로운 이미지 생성
    output_image = np.zeros_like(image)

    for simplex in tri.simplices:
        # 원본 삼각형 좌표
        src_tri = np.float32([src_points[i] for i in simplex])
        dst_tri = np.float32([dst_points[i] for i in simplex])

        # Affine 변환 행렬 계산
        matrix = cv2.getAffineTransform(src_tri, dst_tri)

        # 각 삼각형 영역만 변형 적용
        warp_img = cv2.warpAffine(image, matrix, (image.shape[1], image.shape[0]))

        # 변형된 영역만 저장
        mask_tri = np.zeros_like(mask)
        cv2.fillConvexPoly(mask_tri, dst_tri.astype(np.int32), 255)
        output_image[mask_tri > 0] = warp_img[mask_tri > 0]

    # 🔹 4️⃣ 결과 저장
    cv2.imwrite(output_img_path, output_image)
    print(f"✅ {img_file} 변형 완료 -> 저장됨: {output_img_path}")

# 🔹 모든 이미지 처리
for img_file in sorted(os.listdir(image_folder)):
    if img_file.endswith((".jpg", ".png", ".jpeg")):
        warp_with_delaunay(img_file)

print("🎉 모든 이미지 변형이 완료되었습니다!")
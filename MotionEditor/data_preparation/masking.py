import cv2
import os
import numpy as np

def apply_masks_to_images(image_folder, mask_folder, output_folder):
    """
    특정 폴더 안의 이미지와 마스크를 곱하고 결과를 저장.

    Args:
        image_folder (str): 입력 이미지 폴더 경로.
        mask_folder (str): 입력 마스크 폴더 경로.
        output_folder (str): 출력 결과 저장 폴더 경로.
    """
    # 출력 폴더 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 이미지와 마스크 파일 리스트 가져오기
    image_files = sorted(os.listdir(image_folder))
    mask_files = sorted(os.listdir(mask_folder))

    for image_file, mask_file in zip(image_files, mask_files):
        image_path = os.path.join(image_folder, image_file)
        mask_path = os.path.join(mask_folder, mask_file)
        output_path = os.path.join(output_folder, image_file)

        # 이미지와 마스크 읽기
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)


        # 이미지와 마스크의 크기 확인
        if image.shape[:2] != mask.shape:
            print(f"Skipping {image_file}: Image and mask sizes do not match.")
            continue


        # 데이터 타입 일치시키기
        image = image.astype(np.float32)  # 이미지를 float32로 변환
        mask = mask.astype(np.float32) / 255.0  # 마스크를 float32로 변환하고 [0, 1] 범위로 정규화


        # 마스크 차원 확장 (컬러 이미지의 경우)
        if len(image.shape) == 3:  # 컬러 이미지인 경우
            mask = cv2.merge([mask] * 3)

        # 이미지와 마스크 곱하기
        result = cv2.multiply(image, mask.astype(np.float32) / 255.0)
        # result[result == 0] = 1

        # 결과 저장
        cv2.imwrite(output_path, (result * 255).astype(np.uint8))
        print(f"Processed and saved: {output_path}")

# 사용 예시
image_folder = "/root/video-edit/MotionEditor/data/case-42/images"  # 이미지 폴더 경로
mask_folder = "/root/video-edit/MotionEditor/data/case-42/man.mask"    # 마스크 폴더 경로
output_folder = "/root/video-edit/MotionEditor/data/case-42/masked_img"  # 결과 저장 폴더 경로

apply_masks_to_images(image_folder, mask_folder, output_folder)


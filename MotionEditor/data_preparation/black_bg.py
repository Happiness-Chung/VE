import cv2
import numpy as np
import os

def replace_background_color(image, from_color=(200, 200, 200), to_color=(0, 0, 0)):
    # 정확히 일치하는 색상의 마스크 생성
    mask = np.all(image == from_color, axis=-1)
    image[mask] = to_color
    return image

def process_folder(input_folder, output_folder=None, from_color=(200, 200, 200), to_color=(0, 0, 0)):
    if output_folder is None:
        output_folder = input_folder  # 원본 덮어쓰기
    else:
        os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            # 이미지 로드
            image = cv2.imread(input_path)
            if image is None:
                print(f"⚠️ 이미지 로드 실패: {input_path}")
                continue

            # 색상 변환
            processed_image = replace_background_color(image, from_color, to_color)

            # 저장
            cv2.imwrite(output_path, processed_image)
            print(f"✅ 처리 완료: {output_path}")

# 예시 사용
input_folder = "/root/VE/MotionEditor/data/case-70/target_mask"  # <- 여기에 이미지 폴더 경로 지정
output_folder = None  # <- None이면 원본 덮어쓰기, 아니면 새 폴더 경로
process_folder(input_folder, output_folder)
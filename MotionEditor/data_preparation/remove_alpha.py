import cv2
import os
import glob

def remove_alpha_channel_from_folder(input_folder, output_folder):
    # 출력 폴더가 없으면 생성
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 폴더 내의 모든 PNG 파일 찾기
    png_files = glob.glob(os.path.join(input_folder, "*.png"))

    for file_path in png_files:
        # 이미지 읽기 (RGBA 포함 가능)
        image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

        # 파일명만 추출
        file_name = os.path.basename(file_path)

        # 알파 채널이 있는지 확인
        print(image.shape)
        if image.shape[2] == 4:
            # 알파 채널 제거 (RGB로 변환)
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            print(f"Alpha channel removed: {file_name}")
        else:
            print(f"No alpha channel found: {file_name}")

        # 변환된 이미지 저장
        output_path = os.path.join(output_folder, file_name)
        cv2.imwrite(output_path, image)
        print(f"Saved: {output_path}")

# 사용 예시
input_folder = "/root/VE/MotionEditor/data/case-73/images"   # 입력 폴더 (알파 채널 있는 PNG 이미지들이 있는 폴더)
output_folder = "/root/VE/MotionEditor/data/case-73/images" # 출력 폴더 (알파 채널 제거된 이미지 저장 폴더)

remove_alpha_channel_from_folder(input_folder, output_folder)
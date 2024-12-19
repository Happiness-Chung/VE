import cv2
import numpy as np
import os

def resize_and_shift_pose(image_path, output_path, scale=1, shift_x=100):
    """
    주인공의 위치와 크기를 조정하여 이미지를 왼쪽으로 옮기고, 크기를 축소합니다.
    Args:
    - image_path (str): 입력 이미지 폴더 경로.
    - output_path (str): 출력 이미지 저장 폴더 경로.
    - scale (float): 크기 축소 비율 (0~1 사이의 값).
    - shift_x (int): 왼쪽으로 이동할 픽셀 수.
    """
    # 이미지 로드
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    # 원본 크기 확인
    original_height, original_width = image.shape[:2]

    # 크기 조정
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    resized_image = cv2.resize(image, (new_width, new_height))

    # 검정 배경 이미지 생성 (빈 캔버스)
    canvas = np.zeros((original_height, original_width, 3), dtype=np.uint8)

    # 이동할 위치 계산 (왼쪽으로 이동)
    start_x = max(0, shift_x)  # 음수 값이 되지 않도록 보정
    start_y = (original_height - new_height) // 2  # 세로 중앙 정렬

    # 리사이즈된 이미지 붙여넣기
    canvas[start_y:start_y+new_height, start_x:min(512, start_x+new_width)] = resized_image[:, :512-start_x]

    # 이미지 저장
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    output_image_path = os.path.join(output_path, os.path.basename(image_path))
    cv2.imwrite(output_image_path, canvas)

# 이미지 폴더 경로 설정
input_folder = '/root/video-edit/MotionEditor/data/case-66/source_condition/openposefull'  # 포즈 이미지 폴더 경로 설정
output_folder = '/root/video-edit/MotionEditor/data/case-66/source_condition/moved'  # 출력 이미지 폴더 경로 설정

# 모든 이미지 처리
for filename in os.listdir(input_folder):
    if filename.endswith('.png'):
        input_image_path = os.path.join(input_folder, filename)
        resize_and_shift_pose(input_image_path, output_folder)

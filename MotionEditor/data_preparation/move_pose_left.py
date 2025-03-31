import cv2
import numpy as np
import os

def shift_pose_left(image_path, output_path, shift_x=100):
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    h, w = image.shape[:2]

    background_color = (0, 0, 0)

    # 밝은 배경 캔버스 생성
    canvas = np.full((h, w, 3), background_color, dtype=np.uint8)
    # 왼쪽으로 shift_x만큼 이동한 효과 (오른쪽에 붙여넣기)
    if shift_x < w:
        canvas[:, :w-shift_x] = image[:, shift_x:]

    # 저장
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    out_path = os.path.join(output_path, os.path.basename(image_path))
    cv2.imwrite(out_path, canvas)

# 예시 사용
input_folder = '/root/VE/MotionEditor/results/target_mask'
output_folder = '/root/VE/MotionEditor/results/target_mask'

for filename in os.listdir(input_folder):
    if filename.endswith('.png'):
        path = os.path.join(input_folder, filename)
        shift_pose_left(path, output_folder, shift_x=80)
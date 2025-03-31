import os
from PIL import Image
import numpy as np

def brighten_black_background(input_folder, save_folder=None, replace_color=(200, 200, 200)):
    """
    검은 배경 픽셀을 밝은 색으로 변경하는 함수.

    Args:
        input_folder (str): 이미지가 저장된 폴더 경로
        save_folder (str, optional): 수정된 이미지를 저장할 폴더 (None이면 원본 덮어쓰기)
        replace_color (tuple): (R, G, B) 형태의 밝은 색 (예: 흰색=(255,255,255), 밝은 회색=(200,200,200))
    """
    if save_folder and not os.path.exists(save_folder):
        os.makedirs(save_folder)

    for fname in os.listdir(input_folder):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        
        path = os.path.join(input_folder, fname)
        try:
            img = Image.open(path).convert("RGB")
            img_np = np.array(img)

            # 검은색 배경 마스크 생성
            black_mask = np.all(img_np == [0, 0, 0], axis=-1)

            # 밝은 색으로 변경
            img_np[black_mask] = replace_color

            # 저장
            new_img = Image.fromarray(img_np)
            save_path = os.path.join(save_folder if save_folder else input_folder, fname)
            new_img.save(save_path)
            print(f"✅ 수정 완료: {fname}")

        except Exception as e:
            print(f"⚠️ 오류 발생: {fname} -> {e}")

input_dir = "/root/VE/MotionEditor/data/case-68/protagonist_condition/former"
output_dir = "/root/VE/MotionEditor/data/case-68/protagonist_condition"  # 또는 None으로 덮어쓰기

brighten_black_background(input_dir, output_dir, replace_color=(200, 200, 200))  # 밝은 회색
# brighten_black_background(input_dir, output_dir, replace_color=(255, 255, 255))  # 흰색
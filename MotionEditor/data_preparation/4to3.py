import os
from PIL import Image
import numpy as np

def convert_images_to_rgb(input_folder, save_folder=None):
    """
    특정 폴더 내의 4채널(RGBA) 이미지를 3채널(RGB)로 변환하여 저장하는 함수.
    
    Args:
        input_folder (str): 변환할 이미지가 있는 폴더 경로.
        save_folder (str, optional): 변환된 이미지를 저장할 폴더 (None이면 원본 폴더에 덮어쓰기).
    """
    if not os.path.exists(input_folder):
        print(f"❌ 경로가 존재하지 않습니다: {input_folder}")
        return

    if save_folder and not os.path.exists(save_folder):
        os.makedirs(save_folder)  # 저장 폴더가 없으면 생성

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)

        try:
            with Image.open(file_path) as img:
                img_array = np.array(img.convert("RGBA")) if img.mode in ['L', 'P'] else np.array(img)
                original_shape = img_array.shape  # 변환 전 Shape
                print(original_shape)
                if len(original_shape) == 3 and original_shape[2] == 4:
                    img = img.convert("RGB")  # 3채널로 변환
                    
                    # 저장 경로 설정
                    save_path = os.path.join(save_folder if save_folder else input_folder, filename)
                    img.save(save_path)

                    print(f"✅ 변환 완료: {filename}")
                else:
                    print(f"ℹ️ 4채널이 아님 (변환 안 함): {filename}")

        except Exception as e:
            print(f"⚠️ 오류 발생 ({filename}): {e}")

# 사용 예시
input_dir = "/root/VE/MotionEditor/results/target_mask"  # 변환할 이미지가 있는 폴더
output_dir = None  # 원본 파일 덮어쓰기 (None이면 input_dir에 저장)
# output_dir = "/path/to/output/folder"  # 변환된 이미지를 다른 폴더에 저장하려면 설정

convert_images_to_rgb(input_dir, output_dir)
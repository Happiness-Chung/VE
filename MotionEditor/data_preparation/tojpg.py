import os
from PIL import Image

def convert_png_to_jpg(folder_path, new_folder_path):
    # 폴더 내 모든 파일 목록 가져오기
    files = os.listdir(folder_path)
    
    # .png 파일을 .jpg로 변환
    for filename in files:
        if filename.endswith(".png"):
            # .png 파일 경로
            png_file = os.path.join(folder_path, filename)
            
            # .jpg 파일로 저장할 경로 설정
            jpg_file = filename.replace(".png", ".jpg")
            
            # 이미지 열기
            img = Image.open(png_file)
            
            # RGB 모드로 변환 (JPG는 투명도 지원 안함)
            img = img.convert("RGB")
            
            # .jpg 파일로 저장
            img.save(os.path.join(new_folder_path, jpg_file), "JPEG")
            
            print(f"Converted {png_file} to {jpg_file}")

# 사용할 폴더 경로 (사용자가 바꿀 경로를 설정)
folder_path = "/root/video-edit/MotionEditor/data/case-62/images"
new_folder_path = "/root/video-edit/MotionEditor/data/case-62/jpgs"

# PNG -> JPG 변환 함수 실행
convert_png_to_jpg(folder_path, new_folder_path)

import os
from PIL import Image

# 이미지 파일이 있는 폴더 경로를 지정
input_folder = 'MotionEditor/data/case-46/target_images'  # 여기에 폴더 경로를 입력하세요
output_folder = 'MotionEditor/data/case-46/target_images'  # 리사이즈된 이미지를 저장할 폴더

# 출력 폴더가 없으면 생성
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 원하는 크기 설정 (256 x 256)
resize_size = (512, 512)

# 폴더 내의 모든 파일을 처리
for filename in os.listdir(input_folder):
    if filename.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):  # 이미지 파일만 처리
        try:
            # 이미지 파일 열기
            img_path = os.path.join(input_folder, filename)
            img = Image.open(img_path)

            # 이미지 리사이즈
            img_resized = img.resize(resize_size, Image.Resampling.LANCZOS)

            # 저장할 경로 설정
            output_path = os.path.join(output_folder, filename)

            # 리사이즈된 이미지 저장
            img_resized.save(output_path)
            print(f"Saved resized image: {output_path}")

        except Exception as e:
            print(f"Error processing file {filename}: {e}")

print("All images resized successfully!")

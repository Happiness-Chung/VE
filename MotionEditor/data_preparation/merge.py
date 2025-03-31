import os
import cv2
import numpy as np

# ✅ 입력 폴더 및 출력 경로 설정
input_folder = "/root/VE/MotionEditor/data/case-79/chunks/chunks4"  # 여러 이미지를 합칠 폴더
output_path = "/root/VE/MotionEditor/data/case-79/perotagonist_condition/0003.png"  # 합쳐진 최종 이미지 저장 경로

# ✅ 입력 폴더의 이미지 리스트 가져오기
image_files = sorted([f for f in os.listdir(input_folder) if f.endswith(('.png', '.jpg', '.jpeg'))])

if not image_files:
    print("⚠️ 이미지가 없습니다. 폴더를 확인하세요.")
    exit()

# ✅ 첫 번째 이미지를 기준으로 합성 이미지 초기화
first_image_path = os.path.join(input_folder, image_files[0])
merged_image = cv2.imread(first_image_path, cv2.IMREAD_UNCHANGED)

# ✅ 같은 크기의 빈 캔버스 생성 (검정 배경)
if merged_image is None:
    print(f"⚠️ {first_image_path} 로드 실패")
    exit()
canvas = np.zeros_like(merged_image)

# ✅ 모든 이미지 합치기
for img_file in image_files:
    img_path = os.path.join(input_folder, img_file)
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

    if img is None:
        print(f"⚠️ {img_file} 로드 실패, 건너뜁니다.")
        continue

    # ✅ 검은색이 아닌 픽셀만 선택해서 캔버스에 추가
    mask = np.any(img > 0, axis=-1)  # 검은색이 아닌 부분 찾기
    canvas[mask] = img[mask]  # 픽셀 정보 합치기

# ✅ 최종 이미지 저장
cv2.imwrite(output_path, canvas)
print(f"✅ 합성 완료, 저장됨 -> {output_path}")
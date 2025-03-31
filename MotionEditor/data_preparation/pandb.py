import cv2
import numpy as np
import os

def overlay_person_on_background(person_folder, background_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    person_files = sorted(os.listdir(person_folder))
    background_files = sorted(os.listdir(background_folder))

    for p_file, b_file in zip(person_files, background_files):
        person_path = os.path.join(person_folder, p_file)
        background_path = os.path.join(background_folder, b_file)

        # 이미지 불러오기
        person = cv2.imread(person_path, cv2.IMREAD_COLOR)
        background = cv2.imread(background_path, cv2.IMREAD_COLOR)

        if person is None or background is None:
            print(f"⚠️ Failed to read image: {p_file} or {b_file}")
            continue

        # 크기 맞추기 (작은 쪽에 맞춤)
        h = min(person.shape[0], background.shape[0])
        w = min(person.shape[1], background.shape[1])
        person = cv2.resize(person, (w, h))
        background = cv2.resize(background, (w, h))

        # 마스크 생성 (검정색이 아닌 부분을 인물로 간주)
        mask = np.any(person != [0, 0, 0], axis=-1).astype(np.uint8)  # (h, w)
        mask_3ch = np.repeat(mask[:, :, np.newaxis], 3, axis=2)  # (h, w, 3)

        # 인물만 복사
        combined = np.where(mask_3ch == 1, person, background)

        # 저장
        output_path = os.path.join(output_folder, p_file)
        cv2.imwrite(output_path, combined)
        print(f"✅ Saved: {output_path}")

# 사용 예시
person_frames = "/root/VE/MotionEditor/results/protagonist_after/moved"
background_frames = "/root/VE/MotionEditor/results/background"
output_frames = "/root/VE/MotionEditor/results/prediction2"

overlay_person_on_background(person_frames, background_frames, output_frames)
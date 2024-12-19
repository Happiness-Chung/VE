import cv2
import numpy as np
import os

# 경로 설정
video_frames_path = '/root/video-edit/MotionEditor/data/case-30-resized/images'  # 동영상에서 추출된 프레임들이 있는 경로
mask_frames_path = '/root/video-edit/MotionEditor/data/case-30-resized/man.mask'  # 마스크 프레임들이 있는 경로
output_path = '/root/video-edit/MotionEditor/data/case-30-resized/erased'  # 마스킹된 배경 이미지를 저장할 경로

# 출력 경로 생성
os.makedirs(output_path, exist_ok=True)

# 프레임 파일 목록을 불러옴 (동영상과 마스크의 파일 이름이 일치한다고 가정)
video_frame_files = sorted(os.listdir(video_frames_path))
mask_frame_files = sorted(os.listdir(mask_frames_path))

# 프레임마다 반복
for video_frame_file, mask_frame_file in zip(video_frame_files, mask_frame_files):
    # 동영상 프레임과 마스크 프레임 읽기
    video_frame = cv2.imread(os.path.join(video_frames_path, video_frame_file))
    mask_frame = cv2.imread(os.path.join(mask_frames_path, mask_frame_file), cv2.IMREAD_GRAYSCALE)  # 마스크는 흑백으로 읽음

    # 마스크의 값을 0~1 사이로 변환
    mask_frame = mask_frame / 255.0

    # 배경을 추출 (인물은 마스킹됨)
    masked_background = video_frame * (1 - mask_frame[:, :, np.newaxis])

    # 마스킹된 배경을 uint8 타입으로 변환 후 저장
    masked_background = np.uint8(masked_background)
    output_filename = os.path.join(output_path, video_frame_file)
    cv2.imwrite(output_filename, masked_background)

    print(f"Saved masked background to {output_filename}")

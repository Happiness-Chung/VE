import cv2
import numpy as np
import os

# 경로 설정
masked_frames_path = '/root/video-edit/MotionEditor/data/case-30-resized/erased'  # 인물이 지워진 배경 프레임 경로
output_path = '/root/video-edit/MotionEditor/data/case-30-resized/inpainted'  # 복원된 배경을 저장할 경로

# 출력 경로 생성
os.makedirs(output_path, exist_ok=True)

# 프레임 파일 목록 불러오기
masked_frame_files = sorted(os.listdir(masked_frames_path))

# 프레임마다 반복
for masked_frame_file in masked_frame_files:
    # 마스킹된 프레임 읽기
    masked_frame = cv2.imread(os.path.join(masked_frames_path, masked_frame_file))
    
    # 마스크 생성 (인물 부분이 검은색인 영역을 추출)
    # 검은색(0, 0, 0) 부분을 마스크로 설정
    mask_frame = cv2.inRange(masked_frame, (0, 0, 0), (0, 0, 0))

    # 마스크 영역 복원 (인페인팅)
    inpaint_radius = 3  # 보간 반경
    interpolated_background = cv2.inpaint(masked_frame, mask_frame, inpaint_radius, cv2.INPAINT_TELEA)

    # 복원된 배경 저장
    output_filename = os.path.join(output_path, masked_frame_file)
    cv2.imwrite(output_filename, interpolated_background)

    print(f"Saved interpolated background to {output_filename}")

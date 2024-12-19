import os
import subprocess

# 이미지와 마스크 파일이 있는 디렉터리
image_dir = '/root/video-edit/MotionEditor/data/case-30-resized/erased'
mask_dir = '/root/video-edit/MotionEditor/data/case-30-resized/man.mask'

# 출력 디렉터리
output_dir = '/root/video-edit/MotionEditor/data/case-30-resized/deepfill'

# checkpoint 디렉터리
checkpoint_dir = 'model_logs'

# 이미지 파일들을 반복해서 처리하는 함수
def process_images(image_dir, mask_dir, output_dir, checkpoint_dir):
    # 이미지 파일 목록 가져오기
    image_files = sorted([f for f in os.listdir(image_dir) if f.endswith('.png')])
    
    # 마스크 파일과 매칭되는 이미지 파일 찾기 및 실행
    for image_file in image_files:
        # 이미지 파일 경로
        image_path = os.path.join(image_dir, image_file)
        
        # 마스크 파일 경로 (이미지 파일 이름과 동일한 마스크 파일 찾기)
        mask_path = os.path.join(mask_dir, image_file)
        
        # 출력 파일 경로
        output_path = os.path.join(output_dir, image_file)
        
        # test.py 실행 명령어 만들기
        command = [
            'python', 'test.py',
            '--image', image_path,
            '--mask', mask_path,
            '--output', output_path,
            '--checkpoint_dir', checkpoint_dir
        ]
        
        # 명령어 실행
        print(f"Processing {image_file}...")
        subprocess.run(command)

# 실행
if __name__ == '__main__':
    process_images(image_dir, mask_dir, output_dir, checkpoint_dir)

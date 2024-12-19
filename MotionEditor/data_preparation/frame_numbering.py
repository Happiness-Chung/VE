def write_numbers_to_file(file_path, count):
    with open(file_path, 'w') as f:
        for i in range(count):
            # 4자리 숫자로 포맷 후 파일에 기록
            f.write(f"{i:04}\n")

# 사용할 파일 경로 (사용자가 바꿀 경로를 설정)
file_path = '/root/video-edit/MotionEditor/data/case-38/frame_list.txt'

# 원하는 숫자의 개수 (예: 100개)
write_numbers_to_file(file_path, 8)

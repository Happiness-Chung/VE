import os

def rename_files_in_folder(folder_path, start_number=10):
    # 폴더 내 파일 목록 가져오기
    files = sorted(os.listdir(folder_path))
    
    # 파일 이름 변경
    for i, filename in enumerate(files):
        # 파일의 확장자를 .png로 고정
        new_name = f"{start_number + i:04}.png"
        
        # 현재 파일의 전체 경로
        src = os.path.join(folder_path, filename)
        
        # 새 파일의 전체 경로
        dst = os.path.join(folder_path, new_name)
        
        # 파일 이름 변경
        os.rename(src, dst)
        print(f"Renamed {src} to {dst}")

# 사용할 폴더 경로 (사용자가 바꿀 경로를 설정)
folder_path = '/root/VE/MotionEditor/data/case-79/images'

# 파일 이름을 0010.png부터 변경
rename_files_in_folder(folder_path, start_number=0)

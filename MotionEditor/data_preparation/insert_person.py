import os
from PIL import Image
import numpy as np

def composite_foregrounds_on_backgrounds(foreground_dir, background_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    fg_files = sorted(os.listdir(foreground_dir))
    bg_files = sorted(os.listdir(background_dir))

    for fg_file, bg_file in zip(fg_files, bg_files):
        fg_path = os.path.join(foreground_dir, fg_file)
        bg_path = os.path.join(background_dir, bg_file)

        fg_img = Image.open(fg_path).convert("RGBA")
        bg_img = Image.open(bg_path).convert("RGBA")

        # Resize both to the smaller one’s size
        min_width = min(fg_img.width, bg_img.width)
        min_height = min(fg_img.height, bg_img.height)

        fg_img = fg_img.resize((min_width, min_height), Image.BILINEAR)
        bg_img = bg_img.resize((min_width, min_height), Image.BILINEAR)

        # Convert foreground black background to transparency
        fg_np = np.array(fg_img)
        r, g, b, a = fg_np[:,:,0], fg_np[:,:,1], fg_np[:,:,2], fg_np[:,:,3]
        mask = (r == 0) & (g == 0) & (b == 0)  # 검정색 배경 찾기
        fg_np[mask] = [0, 0, 0, 0]             # 완전 투명으로 바꾸기
        fg_img = Image.fromarray(fg_np)

        # Composite foreground over background
        composed = Image.alpha_composite(bg_img, fg_img)

        save_path = os.path.join(output_dir, fg_file)
        composed.convert("RGB").save(save_path)
        print(f"✅ Saved: {save_path}")

# 사용 예시
foreground_dir = "/root/VE/MotionEditor/data/case-67/protagonist_condition"   # 인물 이미지 폴더
background_dir = "/root/VE/MotionEditor/data/case-67/background_condition"   # 배경 이미지 폴더
output_dir = "/root/VE/MotionEditor/data/case-67/merged_condition"

composite_foregrounds_on_backgrounds(foreground_dir, background_dir, output_dir)

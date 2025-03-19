import cv2
import numpy as np
import matplotlib.pyplot as plt
from numpy.polynomial.polynomial import Polynomial
from scipy.interpolate import griddata
from scipy.interpolate import CubicSpline

# ✅ 1️⃣ 마스크 이미지 로드
mask = cv2.imread("/root/VE/MotionEditor/data/case-79/chunks/materials/source1.png", cv2.IMREAD_GRAYSCALE)
target_mask = cv2.imread("/root/VE/MotionEditor/data/case-79/chunks/materials/target1.png", cv2.IMREAD_GRAYSCALE)
image = cv2.imread("/root/VE/MotionEditor/data/case-79/chunks/materials/image1.png")
output_image = "/root/VE/MotionEditor/data/case-79/chunks/chunks1/chunk2.png"

# ✅ 2️⃣ 팔에 해당하는 픽셀 좌표 추출
mask_points = np.column_stack(np.where(mask > 128))  # (y, x)
x_vals = mask_points[:, 1]
y_vals = mask_points[:, 0]

# ✅ 3️⃣ x 좌표별 평균 y 좌표 계산 (팔의 중간선 찾기)
unique_x = np.unique(x_vals)
mean_y = np.array([np.mean(y_vals[x_vals == x]) for x in unique_x])

# ✅ 4️⃣ 2차 회귀(Quadratic Regression) 적용
poly = Polynomial.fit(unique_x, mean_y, deg=2)
y_pred = poly(unique_x)

# ✅ 5️⃣ 타겟 팔 중심선 추출
target_mask_points = np.column_stack(np.where(target_mask > 60))
x_target = target_mask_points[:, 1]
y_target = target_mask_points[:, 0]
unique_x_target = np.unique(x_target)
mean_y_target = np.array([np.mean(y_target[x_target == x]) for x in unique_x_target])

# ✅ 6️⃣ 2차 회귀 적용 (타겟 팔 곡선)
target_poly = Polynomial.fit(unique_x_target, mean_y_target, deg=2)
y_target_pred = target_poly(unique_x_target)

# # ✅ 7️⃣ 보간하여 크기 맞추기
# x_common = np.linspace(min(unique_x_target), max(unique_x_target), len(unique_x_target))
# y_pred_resampled = np.interp(x_common, unique_x, y_pred)
# y_target_pred_resampled = np.interp(x_common, unique_x_target, y_target_pred)

# ✅ 7️⃣ 보간하여 크기 맞추기 (Cubic Spline 적용)
x_common = np.linspace(min(unique_x_target), max(unique_x_target), num=200)  # 샘플 수 증가
spline_source = CubicSpline(unique_x, y_pred)  # 원본 팔 곡선 보간
spline_target = CubicSpline(unique_x_target, y_target_pred)  # 타겟 팔 곡선 보간

y_pred_resampled = spline_source(x_common)  # 보간된 곡선
y_target_pred_resampled = spline_target(x_common)  # 보간된 곡선

# ✅ 8️⃣ 변형 적용 (원본 → 타겟)
delta_y = y_pred_resampled - y_target_pred_resampled
map_x, map_y = np.meshgrid(np.arange(mask.shape[1]), np.arange(mask.shape[0]))
map_y = (map_y + np.interp(map_x, x_common, delta_y))

# ✅ 변형 맵 데이터 타입 변환 (OpenCV remap 오류 해결)
map_x = map_x.astype(np.float32)
map_y = map_y.astype(np.float32)

# ✅ 9️⃣ 원본 이미지 변형 적용
warped_image = cv2.remap(image, map_x, map_y, interpolation=cv2.INTER_LINEAR)

# ✅  🔹 10️⃣ Target mask 기반 크롭 (불필요한 배경 제거)
cropped_warped = np.zeros_like(image)
cropped_warped[target_mask > 128] = warped_image[target_mask > 128]

# ✅ 11️⃣ **HSV 변환하여 밝은 부분을 우선 반영**
hsv_warped = cv2.cvtColor(cropped_warped, cv2.COLOR_BGR2HSV)
brightness = hsv_warped[:, :, 2]  # V 채널 (명도)

# ✅ 유효한 픽셀 (검은색 제외 & 밝은 영역만 선택)
valid_pixels = np.where((np.sum(cropped_warped, axis=-1) > 0) & (brightness > 10))  # 밝은 픽셀 우선

# ✅  🔹 11️⃣ 빈 부분 보간 (검은색 제외)
# valid_pixels = np.where((np.sum(cropped_warped, axis=-1) > 0) & (np.all(cropped_warped != [0, 0, 0], axis=-1)))  # 유효한 픽셀
empty_pixels = np.where((target_mask > 128) & (np.all(cropped_warped == [0, 0, 0], axis=-1)))  # 채울 영역

if len(valid_pixels[0]) > 0 and len(empty_pixels[0]) > 0:
    for c in range(3):  # R, G, B 각각 보간
        values = cropped_warped[valid_pixels[0], valid_pixels[1], c]
        interpolated_values = griddata(valid_pixels, values, empty_pixels, method='nearest')  # 최근접 보간
        cropped_warped[empty_pixels[0], empty_pixels[1], c] = np.nan_to_num(interpolated_values)

#  ✅ 14️⃣ 만약 모든 픽셀이 여전히 검은색이라면 원본 이미지에서 무작위 샘플링하여 보간
if np.all(cropped_warped == 0):
    print("⚠️ 결과 이미지가 비어 있음. 무작위 샘플링을 통해 복원합니다.")
    
    # `warped_image`에서 랜덤 샘플링하여 target_mask 형태로 채우기
    valid_warped_pixels = np.column_stack(np.where(np.sum(warped_image, axis=-1) > 0))  # 원본에서 유효한 픽셀 좌표
    if len(valid_warped_pixels) > 0:
        sampled_pixels = valid_warped_pixels[np.random.choice(len(valid_warped_pixels), size=len(empty_pixels[0]), replace=True)]
        cropped_warped[empty_pixels[0], empty_pixels[1]] = warped_image[sampled_pixels[:, 0], sampled_pixels[:, 1]]

        
# ✅  🔹 12️⃣ 최종 저장
cv2.imwrite(output_image, cropped_warped)
print("✅ 최종 변형 완료, 저장됨 -> final_result.png")



# ✅ 13️⃣ **곡선 시각화 저장**
plt.figure(figsize=(8, 6))
plt.scatter(unique_x, mean_y, color="blue", label="Source Arm (Data)", alpha=0.5, s=10)
plt.scatter(unique_x_target, mean_y_target, color="red", label="Target Arm (Data)", alpha=0.5, s=10)
plt.plot(x_common, y_pred_resampled, linestyle="dashed", color="blue", label="Source Arm (Fitted)")
plt.plot(x_common, y_target_pred_resampled, linestyle="dashed", color="red", label="Target Arm (Fitted)")

plt.xlabel("X Coordinate (Width)")
plt.ylabel("Y Coordinate (Height)")
plt.title("Arm Shape Transformation (Source → Target)")
plt.legend()
plt.gca().invert_yaxis()
plt.grid()

# ✅ 그래프 저장
plt.savefig("/root/VE/MotionEditor/data/case-79/chunks/chunks1/curve_fitting.png", dpi=300)
plt.close()
print("✅ 곡선 비교 그래프 저장됨 -> curve_fitting.png")
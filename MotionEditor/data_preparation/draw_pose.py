import cv2
import numpy as np

# 원본 이미지를 불러옵니다. (사용자가 올린 이미지로 대체)
image = cv2.imread('/root/video-edit/MotionEditor/data_preparation/frames2/0070.png')

# 포즈 맵을 그릴 빈 캔버스를 원본 이미지 크기로 생성 (검정 배경)
pose_map = np.zeros_like(image)

# 마우스로 클릭한 관절 좌표를 저장할 리스트
points = []

# 마우스 클릭 이벤트 함수
def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # 좌표를 저장
        points.append((x, y))
        # 클릭한 좌표에 포즈 맵(검정 배경) 상에서 원 그리기
        cv2.circle(pose_map, (x, y), 5, (0, 255, 0), -1)

        # 두 개 이상의 포인트가 있으면 선으로 연결
        if len(points) > 1:
            cv2.line(pose_map, points[-2], points[-1], (255, 0, 0), 2)

        # 원본 이미지와 포즈 맵을 중첩하여 화면에 표시
        combined_image = cv2.addWeighted(image, 0.5, pose_map, 0.5, 0)
        cv2.imshow("Pose Map", combined_image)

# 원본 이미지를 띄우고 마우스 이벤트 설정
cv2.imshow("Pose Map", image)
cv2.setMouseCallback("Pose Map", click_event)

# 'q'를 누르면 종료
while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 포즈 맵만 이미지로 저장 (검정 배경 위에 그려진 포즈만)
cv2.imwrite('/root/video-edit/MotionEditor/data_preparation/0070.png', pose_map)

cv2.destroyAllWindows()


import cv2
import mediapipe as mp
import numpy as np
import time

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
#hello
# ----------------------------
# Load Face Landmarker
# ----------------------------
base_options = python.BaseOptions(
    model_asset_path="face_landmarker.task"
)

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1
)

detector = vision.FaceLandmarker.create_from_options(options)

# ----------------------------
# Eye Landmark Indices
# ----------------------------
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# ----------------------------
# Thresholds
# ----------------------------
EAR_THRESHOLD = 0.23
EYE_CONTACT_THRESHOLD = 60  # %

# ----------------------------
# Variables
# ----------------------------
closed_frames = 0
sleep_alert_triggered = False

eye_contact_frames_window = 0
window_frames = 0
not_active_alert_triggered = False

# ----------------------------
# EAR Calculation
# ----------------------------
def calculate_EAR(eye):
    vertical1 = np.linalg.norm(eye[1] - eye[5])
    vertical2 = np.linalg.norm(eye[2] - eye[4])
    horizontal = np.linalg.norm(eye[0] - eye[3])
    return (vertical1 + vertical2) / (2.0 * horizontal)

# ----------------------------
# Webcam Setup
# ----------------------------
cap = cv2.VideoCapture(0)

fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 30

CLOSED_FRAMES_THRESHOLD = int(5 * fps)  # 5 sec sleep
WINDOW_FRAME_THRESHOLD = int(5 * fps)  # 5 sec engagement window

print("Monitoring started... Press Q to quit.")

# ----------------------------
# Main Loop
# ----------------------------
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_frame
    )

    timestamp = int(time.time() * 1000)
    result = detector.detect_for_video(mp_image, timestamp)

    if result.face_landmarks:
        landmarks = result.face_landmarks[0]
        h, w, _ = frame.shape

        coords = np.array([
            (int(p.x * w), int(p.y * h))
            for p in landmarks
        ])

        left_eye = coords[LEFT_EYE]
        right_eye = coords[RIGHT_EYE]

        # -----------------
        # Sleep Detection
        # -----------------
        left_ear = calculate_EAR(left_eye)
        right_ear = calculate_EAR(right_eye)
        ear = (left_ear + right_ear) / 2

        if ear < EAR_THRESHOLD:
            closed_frames += 1
        else:
            closed_frames = 0
            sleep_alert_triggered = False

        if closed_frames >= CLOSED_FRAMES_THRESHOLD and not sleep_alert_triggered:
            print("⚠ ALERT: Student is SLEEPY")
            sleep_alert_triggered = True

        # -----------------
        # Eye Contact Detection
        # -----------------
        nose_x = coords[1][0]
        left_face = coords[234][0]
        right_face = coords[454][0]

        face_center = (left_face + right_face) / 2

        window_frames += 1

        if abs(nose_x - face_center) < 30 and ear > EAR_THRESHOLD:
            eye_contact_frames_window += 1

        # Check every 5 seconds
        if window_frames >= WINDOW_FRAME_THRESHOLD:

            score = (eye_contact_frames_window / window_frames) * 100
            print(f"Eye Contact (5s Window): {score:.2f}%")

            if score < EYE_CONTACT_THRESHOLD and not not_active_alert_triggered:
                print("⚠ ALERT: Student is NOT ACTIVE")
                not_active_alert_triggered = True

            if score >= EYE_CONTACT_THRESHOLD:
                not_active_alert_triggered = False

            # Reset window
            window_frames = 0
            eye_contact_frames_window = 0

    cv2.imshow("Attention Monitor", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
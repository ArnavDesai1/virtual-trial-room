from tkinter import *
from PIL import Image, ImageTk
import cv2, threading, time, sys
import numpy as np
from threading import Thread

try:
    import mediapipe as mp
except Exception as exc:
    print("Mediapipe not available:", exc)
    raise

SPRITES = [0, 0, 0, 0, 0, 0]
image_path = ''

def put_sprite(num):
    global SPRITES
    SPRITES = [0] * len(SPRITES)
    if 0 <= num < len(SPRITES):
        SPRITES[num] = 1

mp_pose = mp.solutions.pose

def detect_pose_keypoints(image_bgr):
    h, w = image_bgr.shape[:2]
    with mp_pose.Pose(static_image_mode=False,
                      model_complexity=1,
                      enable_segmentation=False,
                      min_detection_confidence=0.6,
                      min_tracking_confidence=0.6) as pose:
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        result = pose.process(image_rgb)
        if not result.pose_landmarks:
            return None
        lm = result.pose_landmarks.landmark
        def p(idx):
            return int(lm[idx].x * w), int(lm[idx].y * h)
        left_shoulder = p(mp_pose.PoseLandmark.LEFT_SHOULDER)
        right_shoulder = p(mp_pose.PoseLandmark.RIGHT_SHOULDER)
        left_hip = p(mp_pose.PoseLandmark.LEFT_HIP)
        right_hip = p(mp_pose.PoseLandmark.RIGHT_HIP)
        return {
            'left_shoulder': left_shoulder,
            'right_shoulder': right_shoulder,
            'left_hip': left_hip,
            'right_hip': right_hip,
            'detected': True
        }

_CLOTH_CACHE = {'path': None, 'img': None}
_LAST_FRAME = None

def overlay_pose_clothing(image, clothing_path, pose):
    global _CLOTH_CACHE, _LAST_FRAME
    if not pose or not pose.get('detected'):
        return image
    if _CLOTH_CACHE['path'] != clothing_path or _CLOTH_CACHE['img'] is None:
        _CLOTH_CACHE['path'] = clothing_path
        _CLOTH_CACHE['img'] = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
    cloth = _CLOTH_CACHE['img']
    if cloth is None:
        return image

    ls, rs = pose['left_shoulder'], pose['right_shoulder']
    lh, rh = pose['left_hip'], pose['right_hip']

    shoulder_width = max(20, rs[0]-ls[0])
    body_height = max(40, int((lh[1] + rh[1])//2 - ls[1]))

    ch, cw = cloth.shape[:2]
    scale_x = shoulder_width / float(cw)
    scale_y = body_height / float(ch)
    scale = min(max(0.6, min(scale_x, scale_y)), 2.2)
    new_w, new_h = int(cw*scale), int(ch*scale)
    cloth_r = cv2.resize(cloth, (new_w, new_h))

    start_x = ls[0] + (shoulder_width - new_w)//2
    start_y = ls[1]
    h, w = image.shape[:2]
    start_x = max(0, min(start_x, w-new_w))
    start_y = max(0, min(start_y, h-new_h))
    end_x, end_y = start_x+new_w, start_y+new_h

    roi = image[start_y:end_y, start_x:end_x]
    cloth_roi = cloth_r[:end_y-start_y, :end_x-start_x]
    if cloth_roi.shape[:2] != roi.shape[:2]:
        cloth_roi = cv2.resize(cloth_roi, (roi.shape[1], roi.shape[0]))

    if cloth_roi.shape[2] == 4:
        alpha = cloth_roi[:, :, 3:4] / 255.0
        for c in range(3):
            roi[:, :, c] = (cloth_roi[:, :, c]*alpha[:, :, 0] + roi[:, :, c]*(1-alpha[:, :, 0])).astype(np.uint8)
    else:
        roi[:, :, :3] = cloth_roi[:, :, :3]

    _LAST_FRAME = image.copy()
    return image

def cvloop(run_event):
    global panelA, SPRITES, image_path
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 24)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    frame_i = 0
    last_pose = None
    DETECT_EVERY = 2
    APPLY_EVERY = 2
    while run_event.is_set():
        ok, frame = cap.read()
        if not ok:
            continue
        frame_i += 1
        if frame_i % DETECT_EVERY == 0:
            last_pose = detect_pose_keypoints(frame)

        pose = last_pose
        if pose and SPRITES[0] and image_path and frame_i % APPLY_EVERY == 0:
            status_label.config(text="Pose-based mapping: applying overlay...")
            frame = overlay_pose_clothing(frame, image_path, pose)
        elif SPRITES[0] and _LAST_FRAME is not None:
            frame = _LAST_FRAME.copy()
        else:
            status_label.config(text="Pose ready - click Try it ON")

        disp = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        disp = ImageTk.PhotoImage(Image.fromarray(disp))
        panelA.configure(image=disp)
        panelA.image = disp
        time.sleep(0.02)
    cap.release()

def main():
    global panelA, status_label, image_path
    if len(sys.argv) != 2:
        print("Usage: python tryOn_pose_based.py <path_to_clothing_image>")
        return
    image_path = sys.argv[1]

    root = Tk()
    root.title("E-Dressing Room - Pose Based")
    root.geometry("720x700")

    panelA = Label(root)
    panelA.pack(pady=10)
    status_label = Label(root, text="Initializing pose model...", font=("Arial", 12))
    status_label.pack(pady=5)

    button_frame = Frame(root)
    button_frame.pack(pady=8)
    Button(button_frame, text="Try it ON", bg="green", fg="white", command=lambda: put_sprite(0), font=("Arial",12,"bold")).pack(side=LEFT, padx=5)
    Button(button_frame, text="Clear", bg="orange", fg="white", command=lambda: put_sprite(-1), font=("Arial",12,"bold")).pack(side=LEFT, padx=5)
    Button(button_frame, text="Close", bg="red", fg="white", command=root.quit, font=("Arial",12,"bold")).pack(side=LEFT, padx=5)

    run_event = threading.Event(); run_event.set()
    t = Thread(target=cvloop, args=(run_event,), daemon=True)
    t.start()

    def on_close():
        run_event.clear()
        root.quit()
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()



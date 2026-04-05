from tkinter import *
from PIL import Image, ImageTk
import cv2, threading, os, time, sys, math
from threading import Thread
from os.path import basename, dirname
import dlib
from imutils import face_utils, rotate_bound

# Globals
SPRITES = [0, 0, 0, 0, 0, 0]
image_path = ''

def put_sprite(num):
    global SPRITES
    SPRITES = [0] * len(SPRITES)
    SPRITES[num] = 1

def draw_sprite(frame, sprite, x_offset, y_offset):
    h, w = sprite.shape[0], sprite.shape[1]
    imgH, imgW = frame.shape[0], frame.shape[1]

    if y_offset + h >= imgH:
        sprite = sprite[0:imgH - y_offset, :, :]
    if x_offset + w >= imgW:
        sprite = sprite[:, 0:imgW - x_offset, :]

    if x_offset < 0:
        sprite = sprite[:, abs(x_offset):, :]
        w = sprite.shape[1]
        x_offset = 0

    for c in range(3):
        frame[y_offset:y_offset + h, x_offset:x_offset + w, c] = \
            sprite[:, :, c] * (sprite[:, :, 3] / 255.0) + \
            frame[y_offset:y_offset + h, x_offset:x_offset + w, c] * (1.0 - sprite[:, :, 3] / 255.0)

    return frame

def adjust_sprite2head(sprite, head_width, head_ypos, ontop=True):
    h_sprite, w_sprite = sprite.shape[0], sprite.shape[1]
    factor = 1.0 * head_width / w_sprite
    sprite = cv2.resize(sprite, (0, 0), fx=factor, fy=factor)

    h_sprite = sprite.shape[0]
    y_orig = head_ypos - h_sprite if ontop else head_ypos

    if y_orig < 0:
        sprite = sprite[abs(y_orig):, :, :]
        y_orig = 0
    return sprite, y_orig

def apply_sprite(image, path2sprite, w, x, y, angle, ontop=True):
    sprite = cv2.imread(path2sprite, -1)
    sprite = rotate_bound(sprite, angle)
    sprite, y_final = adjust_sprite2head(sprite, w, y, ontop)
    draw_sprite(image, sprite, x, y_final)

def calculate_inclination(p1, p2):
    x1, y1, x2, y2 = p1[0], p1[1], p2[0], p2[1]
    return 180 / math.pi * math.atan2((y2 - y1), (x2 - x1))

def calculate_boundbox(coords):
    x = min(coords[:, 0])
    y = min(coords[:, 1])
    w = max(coords[:, 0]) - x
    h = max(coords[:, 1]) - y
    return x, y, w, h

def get_face_boundbox(points, part):
    parts = {
        1: (17, 22),
        2: (22, 27),
        3: (36, 42),
        4: (42, 48),
        5: (29, 36),
        6: (0, 17),
        7: (1, 5),
        8: (12, 16),
    }
    start, end = parts.get(part, (0, 17))
    return calculate_boundbox(points[start:end])

def add_sprite(img):
    global image_path
    image_path = img
    folder_name = basename(dirname(img))
    try:
        index = int(folder_name[-1])
        put_sprite(index)
    except ValueError:
        print("Invalid folder format, expected ending with index.")

def cvloop(run_event):
    global panelA, SPRITES, image_path

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("data/shape_predictor_68_face_landmarks.dat")
    video_capture = cv2.VideoCapture(0)

    while run_event.is_set():
        ret, image = video_capture.read()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 0)

        for face in faces:
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            shape = predictor(gray, face)
            shape = face_utils.shape_to_np(shape)
            incl = calculate_inclination(shape[17], shape[26])

            if SPRITES[0]:
                apply_sprite(image, image_path, w, x, y + 40, incl)

            if SPRITES[1]:
                x1, y1, w1, h1 = get_face_boundbox(shape, 6)
                apply_sprite(image, image_path, w1, x1, y1 + 275, incl)

            if SPRITES[3]:
                x3, y3, _, h3 = get_face_boundbox(shape, 1)
                apply_sprite(image, image_path, w, x, y3, incl, ontop=False)

            if SPRITES[4]:
                x3, y3, w3, h3 = get_face_boundbox(shape, 7)
                apply_sprite(image, image_path, w3, x3 - 20, y3 + 25, incl)
                x3, y3, w3, h3 = get_face_boundbox(shape, 8)
                apply_sprite(image, image_path, w3, x3 + 20, y3 + 25, incl)

            if SPRITES[5]:
                upper_cascade = cv2.CascadeClassifier("data/haarcascade_upperbody.xml")
                gray_upper = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                upper_rects = upper_cascade.detectMultiScale(gray_upper, 1.1, 1)
                if len(upper_rects) > 0:
                    x, y, w, h = upper_rects[0]
                    apply_sprite(image, image_path, w, x, y, 0)

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ImageTk.PhotoImage(image)

        panelA.configure(image=image)
        panelA.image = image

    video_capture.release()

# GUI Setup
root = Tk()
root.title("E-Dressing Room")

panelA = Label(root)
panelA.pack(padx=10, pady=10)

# Start with button for selected image path
def try_on(img_path):
    Button(root, text="Try it ON", command=lambda: add_sprite(img_path)).pack(side="top", fill="x", padx=5, pady=5)

# CLI argument must be the image path
if len(sys.argv) < 2:
    print("Usage: python tryOn.py <path_to_sprite_image>")
    sys.exit(1)

# Convert static path to full path
image_path = sys.argv[1]
if image_path.startswith('static/images/'):
    # Convert to full path from project root
    image_path = image_path.replace('static/images/', 'images/')

try_on(image_path)

# Start camera thread
run_event = threading.Event()
run_event.set()
Thread(target=cvloop, args=(run_event,), daemon=True).start()

def terminate():
    run_event.clear()
    time.sleep(1)
    root.destroy()

root.protocol("WM_DELETE_WINDOW", terminate)
root.mainloop()

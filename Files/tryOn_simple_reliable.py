from tkinter import *
from PIL import Image, ImageTk
import cv2, threading, os, time, sys, math
import numpy as np
from threading import Thread

# Globals
SPRITES = [0, 0, 0, 0, 0, 0]
image_path = ''

def put_sprite(num):
    global SPRITES
    SPRITES = [0] * len(SPRITES)
    SPRITES[num] = 1

def detect_face_simple(image):
    """Simple face detection that always works"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) > 0:
        return faces[0]  # Return first face
    return None

def calculate_body_from_face(face, image_shape):
    """Calculate body position from face detection"""
    if face is None:
        return None
    
    face_x, face_y, face_w, face_h = face
    img_h, img_w = image_shape[:2]
    
    # Face center
    face_center_x = face_x + face_w // 2
    face_center_y = face_y + face_h // 2
    
    # Calculate shoulders (below face)
    shoulder_width = face_w * 2.0  # Shoulders are wider than face
    shoulder_y = face_y + face_h + 20  # Below the face
    
    left_shoulder_x = face_center_x - shoulder_width // 2
    right_shoulder_x = face_center_x + shoulder_width // 2
    
    # Calculate waist (further down)
    waist_y = shoulder_y + face_h * 1.2  # Waist is below shoulders
    waist_width = shoulder_width * 0.9  # Waist is narrower than shoulders
    
    left_waist_x = face_center_x - waist_width // 2
    right_waist_x = face_center_x + waist_width // 2
    
    # Ensure coordinates are within image bounds
    left_shoulder_x = max(0, min(int(left_shoulder_x), img_w))
    right_shoulder_x = max(0, min(int(right_shoulder_x), img_w))
    shoulder_y = max(0, min(int(shoulder_y), img_h))
    left_waist_x = max(0, min(int(left_waist_x), img_w))
    right_waist_x = max(0, min(int(right_waist_x), img_w))
    waist_y = max(0, min(int(waist_y), img_h))
    
    return {
        'left_shoulder': (left_shoulder_x, shoulder_y),
        'right_shoulder': (right_shoulder_x, shoulder_y),
        'left_waist': (left_waist_x, waist_y),
        'right_waist': (right_waist_x, waist_y),
        'shoulder_width': shoulder_width,
        'body_height': waist_y - shoulder_y,
        'detected': True
    }

def apply_clothing_simple(image, clothing_path, body_data):
    """Apply clothing with simple but effective method"""
    if not body_data or not body_data.get('detected', False):
        return image
        
    # Load clothing
    clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
    if clothing is None:
        print(f"Could not load clothing: {clothing_path}")
        return image
    
    # Get body measurements
    left_shoulder = body_data['left_shoulder']
    right_shoulder = body_data['right_shoulder']
    left_waist = body_data['left_waist']
    right_waist = body_data['right_waist']
    
    # Calculate clothing dimensions
    shoulder_width = right_shoulder[0] - left_shoulder[0]
    body_height = left_waist[1] - left_shoulder[1]
    
    # Resize clothing to match body
    orig_h, orig_w = clothing.shape[:2]
    scale_x = shoulder_width / orig_w
    scale_y = body_height / orig_h
    scale = min(scale_x, scale_y)
    
    new_width = int(orig_w * scale)
    new_height = int(orig_h * scale)
    
    # Resize clothing
    resized_clothing = cv2.resize(clothing, (new_width, new_height))
    
    # Apply clothing at shoulder position
    result = overlay_clothing(image, resized_clothing, left_shoulder)
    
    return result

def overlay_clothing(body_image, clothing, start_pos):
    """Simple clothing overlay that always works"""
    result = body_image.copy()
    h, w = clothing.shape[:2]
    img_h, img_w = body_image.shape[:2]
    
    # Calculate placement region
    start_x, start_y = start_pos
    end_x = min(start_x + w, img_w)
    end_y = min(start_y + h, img_h)
    start_x = max(0, start_x)
    start_y = max(0, start_y)
    
    # Extract regions
    body_region = result[start_y:end_y, start_x:end_x]
    clothing_region = clothing[:end_y-start_y, :end_x-start_x]
    
    # Ensure same dimensions
    if body_region.shape != clothing_region.shape:
        clothing_region = cv2.resize(clothing_region, (body_region.shape[1], body_region.shape[0]))
    
    # Simple alpha blending
    if clothing_region.shape[2] == 4:  # Has alpha channel
        alpha = clothing_region[:, :, 3:4] / 255.0
        
        # Blend each color channel
        for c in range(3):
            body_region[:, :, c] = (
                clothing_region[:, :, c] * alpha[:, :, 0] + 
                body_region[:, :, c] * (1.0 - alpha[:, :, 0])
            ).astype(np.uint8)
    else:
        # No alpha channel, use simple overlay
        body_region[:, :, :3] = clothing_region[:, :, :3]
    
    return result

def draw_simple_markers(image, body_data):
    """Draw simple body markers"""
    if not body_data or not body_data.get('detected', False):
        return image
    
    # Draw shoulder points (green)
    cv2.circle(image, body_data['left_shoulder'], 8, (0, 255, 0), -1)
    cv2.circle(image, body_data['right_shoulder'], 8, (0, 255, 0), -1)
    
    # Draw waist points (blue)
    cv2.circle(image, body_data['left_waist'], 6, (255, 0, 0), -1)
    cv2.circle(image, body_data['right_waist'], 6, (255, 0, 0), -1)
    
    # Draw connecting lines
    cv2.line(image, body_data['left_shoulder'], body_data['right_shoulder'], (0, 255, 0), 3)
    cv2.line(image, body_data['left_waist'], body_data['right_waist'], (255, 0, 0), 3)
    
    # Draw body outline
    cv2.line(image, body_data['left_shoulder'], body_data['left_waist'], (0, 255, 255), 2)
    cv2.line(image, body_data['right_shoulder'], body_data['right_waist'], (0, 255, 255), 2)
    
    return image

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label
    
    cap = cv2.VideoCapture(0)
    
    while run_event.is_set():
        ret, image = cap.read()
        if not ret:
            continue
            
        # Detect face
        face = detect_face_simple(image)
        
        if face is not None:
            # Calculate body from face
            body_data = calculate_body_from_face(face, image.shape)
            
            if body_data:
                # Draw body markers
                image = draw_simple_markers(image, body_data)
                
                # Apply clothing if sprite is active
                if SPRITES[0] and image_path:
                    status_label.config(text="Face detected! Applying clothing...")
                    image = apply_clothing_simple(image, image_path, body_data)
                else:
                    status_label.config(text="Face detected! Ready for clothing...")
            else:
                status_label.config(text="Face detected, calculating body...")
        else:
            status_label.config(text="Looking for face...")
        
        # Resize for display
        height, width = image.shape[:2]
        max_width = 700
        if width > max_width:
            scale = max_width / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))
        
        # Convert and display
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        image_tk = ImageTk.PhotoImage(image_pil)
        
        panelA.configure(image=image_tk)
        panelA.image = image_tk
        
        time.sleep(0.03)
    
    cap.release()

def main():
    global panelA, status_label, image_path
    
    if len(sys.argv) != 2:
        print("Usage: python tryOn_simple_reliable.py <path_to_clothing_image>")
        return
    
    image_path = sys.argv[1]
    
    # Create GUI
    root = Tk()
    root.title("E-Dressing Room - Simple & Reliable")
    root.geometry("800x700")
    
    # Video display
    panelA = Label(root)
    panelA.pack(pady=10)
    
    # Status label
    status_label = Label(root, text="Initializing simple face detection...", font=("Arial", 12))
    status_label.pack(pady=5)
    
    # Control buttons
    button_frame = Frame(root)
    button_frame.pack(pady=10)
    
    try_on_btn = Button(button_frame, text="Try it ON", bg="green", fg="white", 
                       command=lambda: put_sprite(0), font=("Arial", 12, "bold"))
    try_on_btn.pack(side=LEFT, padx=5)
    
    clear_btn = Button(button_frame, text="Clear Clothing", bg="orange", fg="white",
                     command=lambda: put_sprite(-1), font=("Arial", 12, "bold"))
    clear_btn.pack(side=LEFT, padx=5)
    
    close_btn = Button(button_frame, text="Close", bg="red", fg="white",
                      command=root.quit, font=("Arial", 12, "bold"))
    close_btn.pack(side=LEFT, padx=5)
    
    # Start video loop
    run_event = threading.Event()
    run_event.set()
    
    video_thread = Thread(target=cvloop, args=(run_event,))
    video_thread.daemon = True
    video_thread.start()
    
    # Handle window close
    def on_closing():
        run_event.clear()
        root.quit()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()


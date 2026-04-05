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

def detect_body_landmarks(image, face):
    """Detect body landmarks for better clothing fitting"""
    x, y, w, h = face
    
    # Estimate body landmarks based on face position
    # These are rough estimates - in a real system, you'd use pose detection
    shoulder_y = y + h + 20
    chest_y = y + h + 40
    waist_y = y + h + 80
    
    # Estimate shoulder width (typically 1.5x face width)
    shoulder_width = int(w * 1.5)
    shoulder_x = x - (shoulder_width - w) // 2
    
    # Estimate chest width (slightly wider than shoulders)
    chest_width = int(shoulder_width * 1.1)
    chest_x = x - (chest_width - w) // 2
    
    return {
        'shoulder': (shoulder_x, shoulder_y, shoulder_width),
        'chest': (chest_x, chest_y, chest_width),
        'waist': (chest_x, waist_y, int(chest_width * 0.9))
    }

def create_clothing_mask(sprite, body_landmarks, clothing_type='shirt'):
    """Create a realistic clothing mask based on body landmarks"""
    h, w = sprite.shape[0], sprite.shape[1]
    
    # Get body measurements
    chest_x, chest_y, chest_w = body_landmarks['chest']
    shoulder_x, shoulder_y, shoulder_w = body_landmarks['shoulder']
    
    # Create a mask for realistic clothing fitting
    mask = np.zeros((h, w), dtype=np.uint8)
    
    if clothing_type == 'shirt':
        # For shirts, create a more realistic shape
        # Top part (shoulders) - wider
        top_width = int(shoulder_w * 0.8)
        top_x = (w - top_width) // 2
        
        # Bottom part (waist) - narrower
        bottom_width = int(chest_w * 0.7)
        bottom_x = (w - bottom_width) // 2
        
        # Create trapezoid shape
        pts = np.array([
            [top_x, 0],
            [top_x + top_width, 0],
            [bottom_x + bottom_width, h],
            [bottom_x, h]
        ], np.int32)
        
        cv2.fillPoly(mask, [pts], 255)
        
    elif clothing_type == 'dress':
        # For dresses, create a more fitted shape
        top_width = int(chest_w * 0.6)
        top_x = (w - top_width) // 2
        
        bottom_width = int(chest_w * 0.4)
        bottom_x = (w - bottom_width) // 2
        
        pts = np.array([
            [top_x, 0],
            [top_x + top_width, 0],
            [bottom_x + bottom_width, h],
            [bottom_x, h]
        ], np.int32)
        
        cv2.fillPoly(mask, [pts], 255)
    
    return mask

def apply_realistic_clothing(image, path2sprite, body_landmarks, clothing_type='shirt'):
    """Apply clothing with realistic fitting and perspective"""
    sprite = cv2.imread(path2sprite, -1)
    if sprite is None:
        print(f"Could not load sprite: {path2sprite}")
        return image
    
    # Get body measurements
    chest_x, chest_y, chest_w = body_landmarks['chest']
    shoulder_x, shoulder_y, shoulder_w = body_landmarks['shoulder']
    
    # Determine clothing type from filename
    if 'dress' in path2sprite.lower():
        clothing_type = 'dress'
    elif 'shirt' in path2sprite.lower() or 'top' in path2sprite.lower():
        clothing_type = 'shirt'
    
    # Calculate realistic sizing based on body measurements
    if clothing_type == 'shirt':
        # Shirt sizing
        target_width = int(chest_w * 1.2)  # 20% wider than chest
        target_height = int(target_width * 1.3)  # 30% taller
    else:  # dress
        # Dress sizing
        target_width = int(chest_w * 1.1)  # 10% wider than chest
        target_height = int(target_width * 1.8)  # 80% taller for dress length
    
    # Resize sprite to target dimensions
    sprite = cv2.resize(sprite, (target_width, target_height))
    
    # Create realistic clothing mask
    mask = create_clothing_mask(sprite, body_landmarks, clothing_type)
    
    # Apply perspective transformation for more realistic look
    h, w = sprite.shape[0], sprite.shape[1]
    
    # Create perspective points for 3D effect
    if clothing_type == 'shirt':
        # Shirt perspective - slight inward curve
        pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        pts2 = np.float32([[w*0.05, 0], [w*0.95, 0], [w*0.1, h], [w*0.9, h]])
    else:  # dress
        # Dress perspective - more fitted
        pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        pts2 = np.float32([[w*0.1, 0], [w*0.9, 0], [w*0.15, h], [w*0.85, h]])
    
    # Apply perspective transform
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    sprite = cv2.warpPerspective(sprite, matrix, (w, h))
    mask = cv2.warpPerspective(mask, matrix, (w, h))
    
    # Position the sprite
    sprite_x = max(0, chest_x - (target_width - chest_w) // 2)
    sprite_y = max(0, chest_y - 20)  # Start slightly above chest
    
    # Apply the clothing with the mask
    draw_sprite_with_mask(image, sprite, mask, sprite_x, sprite_y)
    
    return image

def draw_sprite_with_mask(frame, sprite, mask, x_offset, y_offset):
    """Draw sprite with realistic masking and blending"""
    h, w = sprite.shape[0], sprite.shape[1]
    imgH, imgW = frame.shape[0], frame.shape[1]

    # Ensure sprite has alpha channel
    if sprite.shape[2] != 4:
        alpha = np.ones((h, w, 1), dtype=sprite.dtype) * 255
        sprite = np.concatenate([sprite, alpha], axis=2)

    # Clamp coordinates
    y_start = max(0, y_offset)
    y_end = min(imgH, y_offset + h)
    x_start = max(0, x_offset)
    x_end = min(imgW, x_offset + w)

    if y_start >= imgH or x_start >= imgW or y_end <= 0 or x_end <= 0:
        return frame

    # Calculate sprite regions
    sprite_y_start = max(0, -y_offset)
    sprite_y_end = sprite_y_start + (y_end - y_start)
    sprite_x_start = max(0, -x_offset)
    sprite_x_end = sprite_x_start + (x_end - x_start)

    if sprite_y_start >= h or sprite_x_start >= w or sprite_y_end <= 0 or sprite_x_end <= 0:
        return frame

    # Extract regions
    frame_region = frame[y_start:y_end, x_start:x_end]
    sprite_region = sprite[sprite_y_start:sprite_y_end, sprite_x_start:sprite_x_end]
    mask_region = mask[sprite_y_start:sprite_y_end, sprite_x_start:sprite_x_end]

    # Ensure all regions have the same shape
    if frame_region.shape != sprite_region.shape:
        sprite_region = cv2.resize(sprite_region, (frame_region.shape[1], frame_region.shape[0]))
        mask_region = cv2.resize(mask_region, (frame_region.shape[1], frame_region.shape[0]))

    # Apply realistic blending with mask
    if sprite_region.shape[2] == 4:  # Has alpha channel
        # Combine alpha channel with mask
        combined_alpha = (sprite_region[:, :, 3:4] / 255.0) * (mask_region[:, :, np.newaxis] / 255.0)
        
        # Apply color blending
        for c in range(3):
            frame_region[:, :, c] = (sprite_region[:, :, c] * combined_alpha[:, :, 0] + 
                                   frame_region[:, :, c] * (1.0 - combined_alpha[:, :, 0])).astype(np.uint8)
    else:
        # No alpha channel, use mask only
        mask_3d = mask_region[:, :, np.newaxis] / 255.0
        for c in range(3):
            frame_region[:, :, c] = (sprite_region[:, :, c] * mask_3d[:, :, 0] + 
                                   frame_region[:, :, c] * (1.0 - mask_3d[:, :, 0])).astype(np.uint8)

    return frame

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label

    try:
        # Use OpenCV's built-in face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            status_label.config(text="Error: Could not open camera")
            return
            
        status_label.config(text="Camera ready - Looking for faces...")
        
        while run_event.is_set():
            ret, image = video_capture.read()
            if not ret:
                continue
                
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            if len(faces) > 0:
                status_label.config(text=f"Face detected! Applying clothing...")
                
                if SPRITES[0] and image_path:
                    # Detect body landmarks for better fitting
                    body_landmarks = detect_body_landmarks(image, faces[0])
                    
                    # Draw body landmarks for debugging
                    for landmark_name, (lx, ly, lw) in body_landmarks.items():
                        cv2.rectangle(image, (lx, ly), (lx + lw, ly + 20), (0, 255, 255), 2)
                        cv2.putText(image, landmark_name, (lx, ly - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    
                    # Apply realistic clothing
                    image = apply_realistic_clothing(image, image_path, body_landmarks)
            else:
                status_label.config(text="Looking for faces...")

            # Resize image to fit the display
            height, width = image.shape[:2]
            max_width = 600
            if width > max_width:
                scale = max_width / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image = ImageTk.PhotoImage(image)

            panelA.configure(image=image)
            panelA.image = image

    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")
        print(f"Camera error: {e}")
    finally:
        video_capture.release()

# GUI Setup
root = Tk()
root.title("E-Dressing Room - Enhanced Virtual Try-On")
root.geometry("900x700")
root.configure(bg='black')

# Create a frame for the camera display
camera_frame = Frame(root, bg='black')
camera_frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

panelA = Label(camera_frame, bg='black')
panelA.pack(expand=True, fill=BOTH)

# Add status label
status_label = Label(root, text="Loading camera...", fg='white', bg='black')
status_label.pack(pady=5)

# Add info label
info_label = Label(root, text="Enhanced fitting with body landmark detection", fg='yellow', bg='black')
info_label.pack(pady=2)

def try_on(img_path):
    try_button = Button(root, text="Try it ON", command=lambda: add_sprite(img_path), 
                       bg='green', fg='white', font=('Arial', 12, 'bold'))
    try_button.pack(side="top", fill="x", padx=10, pady=5)
    
    # Auto-activate the clothing
    add_sprite(img_path)

def add_sprite(img):
    global image_path
    image_path = img
    put_sprite(0)  # Activate first sprite
    status_label.config(text="Enhanced clothing activated! Look at the camera.")

def clear_clothing():
    global image_path
    image_path = ''
    put_sprite(0)  # Deactivate sprite
    status_label.config(text="Clothing cleared. Add new clothing to try on.")

# CLI argument must be the image path
if len(sys.argv) < 2:
    print("Usage: python tryOn_enhanced.py <path_to_sprite_image>")
    sys.exit(1)

# Use the path as provided by Flask
image_path = sys.argv[1]
print("Loading image from:", image_path)

# Check if the image exists
if not os.path.exists(image_path):
    print(f"Error: Image file not found: {image_path}")
    sys.exit(1)

try_on(image_path)

# Start camera thread
run_event = threading.Event()
run_event.set()
Thread(target=cvloop, args=(run_event,), daemon=True).start()

def terminate():
    run_event.clear()
    time.sleep(1)
    root.destroy()

# Add control buttons
button_frame = Frame(root, bg='black')
button_frame.pack(side="bottom", fill="x", padx=10, pady=5)

clear_button = Button(button_frame, text="Clear Clothing", command=clear_clothing, 
                     bg='orange', fg='white', font=('Arial', 10))
clear_button.pack(side="left", fill="x", expand=True, padx=(0, 5))

close_button = Button(button_frame, text="Close", command=terminate, 
                     bg='red', fg='white', font=('Arial', 10))
close_button.pack(side="right", fill="x", expand=True, padx=(5, 0))

# Make sure window is on top and focused
root.lift()
root.attributes('-topmost', True)
root.after_idle(lambda: root.attributes('-topmost', False))

root.protocol("WM_DELETE_WINDOW", terminate)
root.mainloop()


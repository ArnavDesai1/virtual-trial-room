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

def draw_sprite(frame, sprite, x_offset, y_offset):
    h, w = sprite.shape[0], sprite.shape[1]
    imgH, imgW = frame.shape[0], frame.shape[1]

    # Ensure sprite has alpha channel
    if sprite.shape[2] != 4:
        print("Warning: Sprite doesn't have alpha channel, creating one")
        # Create alpha channel
        alpha = np.ones((h, w, 1), dtype=sprite.dtype) * 255
        sprite = np.concatenate([sprite, alpha], axis=2)

    # Clamp coordinates to valid ranges
    y_start = max(0, y_offset)
    y_end = min(imgH, y_offset + h)
    x_start = max(0, x_offset)
    x_end = min(imgW, x_offset + w)

    # Calculate sprite region to use
    sprite_y_start = max(0, -y_offset)
    sprite_y_end = sprite_y_start + (y_end - y_start)
    sprite_x_start = max(0, -x_offset)
    sprite_x_end = sprite_x_start + (x_end - x_start)

    # Ensure we don't go out of bounds
    if y_start >= imgH or x_start >= imgW or y_end <= 0 or x_end <= 0:
        return frame

    if sprite_y_start >= h or sprite_x_start >= w or sprite_y_end <= 0 or sprite_x_end <= 0:
        return frame

    # Extract the regions
    frame_region = frame[y_start:y_end, x_start:x_end]
    sprite_region = sprite[sprite_y_start:sprite_y_end, sprite_x_start:sprite_x_end]

    # Ensure both regions have the same shape by resizing if needed
    if frame_region.shape != sprite_region.shape:
        print(f"Shape mismatch: frame_region {frame_region.shape}, sprite_region {sprite_region.shape}")
        # Resize sprite_region to match frame_region
        sprite_region = cv2.resize(sprite_region, (frame_region.shape[1], frame_region.shape[0]))
        print(f"Resized sprite_region to: {sprite_region.shape}")

    # Apply alpha blending
    if sprite_region.shape[2] == 4:  # Has alpha channel
        alpha = sprite_region[:, :, 3:4] / 255.0
        for c in range(3):
            frame_region[:, :, c] = (sprite_region[:, :, c] * alpha[:, :, 0] + 
                                   frame_region[:, :, c] * (1.0 - alpha[:, :, 0])).astype(np.uint8)
    else:  # No alpha channel, just overlay
        frame_region[:, :, :3] = sprite_region[:, :, :3]

    return frame

def detect_existing_shirt(frame, face_x, face_y, face_w, face_h):
    """Detect the existing shirt using color segmentation"""
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define color range for the user's purple shirt - BROADER RANGE
    # Purple can be in different HSV ranges, so let's try multiple ranges
    lower_purple1 = np.array([120, 30, 30])  # Lower threshold
    upper_purple1 = np.array([160, 255, 255])  # Upper threshold
    
    lower_purple2 = np.array([130, 20, 20])  # Alternative range
    upper_purple2 = np.array([170, 255, 255])
    
    # Create masks for both ranges
    mask1 = cv2.inRange(hsv_frame, lower_purple1, upper_purple1)
    mask2 = cv2.inRange(hsv_frame, lower_purple2, upper_purple2)
    
    # Combine both masks
    mask = cv2.bitwise_or(mask1, mask2)
    
    # Morphological operations to clean up the mask
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    shirt_info = None
    if contours:
        # Find the largest contour, likely to be the shirt
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get bounding box of the shirt
        sx, sy, sw, sh = cv2.boundingRect(largest_contour)
        
        # More lenient conditions for shirt detection
        if sy > face_y + face_h / 3 and sw > face_w * 0.5 and sh > face_h * 0.3:
            shirt_info = {
                'x': sx,
                'y': sy,
                'width': sw,
                'height': sh,
                'contour': largest_contour
            }
    
    return shirt_info

def apply_sprite_to_shirt(image, path2sprite, shirt_info):
    """Apply virtual clothing to match the existing shirt exactly"""
    if shirt_info is None:
        return image
    
    sprite = cv2.imread(path2sprite, -1)
    if sprite is None:
        print(f"Could not load sprite: {path2sprite}")
        return image
    
    # Resize sprite to match the existing shirt dimensions exactly
    sprite_width = shirt_info['width']
    sprite_height = shirt_info['height']
    
    sprite = cv2.resize(sprite, (sprite_width, sprite_height))
    
    # Position sprite to match the existing shirt exactly
    sprite_x = shirt_info['x']
    sprite_y = shirt_info['y']
    
    # Apply the sprite
    draw_sprite(image, sprite, sprite_x, sprite_y)
    return image

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label

    try:
        # Use OpenCV's built-in face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            status_label.config(text="Error: Could not open camera")
            return
            
        status_label.config(text="Camera ready - Looking for faces and shirts...")
        
        while run_event.is_set():
            ret, image = video_capture.read()
            if not ret:
                continue
                
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            if len(faces) > 0:
                x, y, w, h = faces[0]
                
                # Detect existing shirt
                shirt_info = detect_existing_shirt(image, x, y, w, h)
                
                if shirt_info:
                    status_label.config(text="Shirt detected! Applying virtual clothing...")
                    
                    # Draw detected shirt area (yellow rectangle)
                    cv2.rectangle(image, 
                                (shirt_info['x'], shirt_info['y']), 
                                (shirt_info['x'] + shirt_info['width'], 
                                 shirt_info['y'] + shirt_info['height']), 
                                (0, 255, 255), 2)
                    
                    # Apply virtual clothing to match existing shirt exactly
                    if SPRITES[0] and image_path:
                        image = apply_sprite_to_shirt(image, image_path, shirt_info)
                else:
                    status_label.config(text="Face detected - Looking for shirt... (Debug: No shirt found)")
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
root.title("E-Dressing Room - Actual Body Mapping")
root.geometry("800x600")
root.configure(bg='black')

# Create a frame for the camera display
camera_frame = Frame(root, bg='black')
camera_frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

panelA = Label(camera_frame, bg='black')
panelA.pack(expand=True, fill=BOTH)

# Add status label
status_label = Label(root, text="Loading camera...", fg='white', bg='black')
status_label.pack(pady=5)

# Start with button for selected image path
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
    status_label.config(text="Clothing activated! Look at the camera.")

def clear_clothing():
    global image_path
    image_path = ''
    put_sprite(0)  # Deactivate sprite
    status_label.config(text="Clothing cleared. Add new clothing to try on.")

# CLI argument must be the image path
if len(sys.argv) < 2:
    print("Usage: python tryOn_actual_body_mapping.py <path_to_sprite_image>")
    sys.exit(1)

# Use the path as provided by Flask
image_path = sys.argv[1]
print("Loading image from:", image_path)

# Check if the image exists
if not os.path.exists(image_path):
    print(f"Error: Image file not found: {image_path}")
    print("Available files in current directory:")
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith('.png'):
                print(f"  {os.path.join(root, file)}")
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

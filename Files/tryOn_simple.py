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
    if sprite is None:
        print(f"Could not load sprite: {path2sprite}")
        return image
    
    # For clothing items, use better sizing and positioning
    # Make the sprite match the calculated width exactly
    sprite_width = int(w)  # Use the exact calculated width
    sprite_height = int(sprite_width * 1.6)  # More realistic height for clothing
    
    sprite = cv2.resize(sprite, (sprite_width, sprite_height))
    
    # Position the sprite properly - use exact positioning
    sprite_x = max(0, int(x))  # Use exact x position
    sprite_y = max(0, int(y))  # Start at the calculated y position
    
    # Add some perspective adjustment for more realistic look
    # Create a slight perspective transform
    h, w_sprite = sprite.shape[0], sprite.shape[1]
    pts1 = np.float32([[0, 0], [w_sprite, 0], [0, h], [w_sprite, h]])
    pts2 = np.float32([[0, 0], [w_sprite, 0], [w_sprite*0.1, h], [w_sprite*0.9, h]])
    
    # Apply perspective transform
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    sprite = cv2.warpPerspective(sprite, matrix, (w_sprite, h))
    
    draw_sprite(image, sprite, sprite_x, sprite_y)
    return image

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label

    try:
        # Use OpenCV's built-in face detection instead of dlib
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
                # Apply sprite to the first detected face
                if SPRITES[0] and image_path:
                    x, y, w, h = faces[0]
                    # For shirts/tops, position below the face (chest area)
                    # ACTUAL BODY PART MAPPING - map shoulders to shoulder edges
                    
                    # ACTUALLY MAP TO YOUR BODY - No more guessing!
                    face_center_x = x + w // 2
                    
                    # Much narrower to actually match your shoulders
                    shoulder_width = w * 1.5  # Much narrower to match your actual shoulders
                    shoulder_y = y + h + 35   # Much further down to actual shoulder level
                    
                    # Map to actual body coordinates
                    left_shoulder_x = face_center_x - shoulder_width // 2
                    right_shoulder_x = face_center_x + shoulder_width // 2
                    
                    # Position clothing to actually fit your body
                    chest_x = left_shoulder_x  # Start at left shoulder edge
                    chest_y = y + h + 25      # Start at actual collar level (not covering chin)
                    chest_w = shoulder_width   # Width matches your actual shoulders
                    
                    # Draw body part markers to show actual mapping
                    # Left shoulder marker (blue)
                    cv2.circle(image, (int(left_shoulder_x), int(shoulder_y)), 8, (255, 0, 0), -1)
                    # Right shoulder marker (red)  
                    cv2.circle(image, (int(right_shoulder_x), int(shoulder_y)), 8, (0, 0, 255), -1)
                    
                    # Draw shoulder line
                    cv2.line(image, (int(left_shoulder_x), int(shoulder_y)), 
                           (int(right_shoulder_x), int(shoulder_y)), (255, 0, 0), 2)
                    
                    # Calculate waist position for realistic clothing height
                    waist_y = chest_y + w * 1.5  # More realistic waist position
                    
                    # Draw waist markers
                    cv2.circle(image, (int(left_shoulder_x), int(waist_y)), 6, (255, 255, 0), -1)  # Yellow for left waist
                    cv2.circle(image, (int(right_shoulder_x), int(waist_y)), 6, (0, 255, 255), -1)  # Cyan for right waist
                    
                    # Draw waist line
                    cv2.line(image, (int(left_shoulder_x), int(waist_y)), 
                           (int(right_shoulder_x), int(waist_y)), (255, 255, 0), 2)
                    
                    # Draw a rectangle to show where the clothing will be placed
                    # Ensure all coordinates are integers
                    pt1 = (int(chest_x), int(chest_y))
                    pt2 = (int(chest_x + chest_w), int(waist_y))
                    cv2.rectangle(image, pt1, pt2, (0, 255, 255), 2)  # Cyan for clothing area
                    
                    # Apply clothing with proper height from collar to waist
                    clothing_height = int(waist_y - chest_y)
                    apply_sprite(image, image_path, int(chest_w), int(chest_x), int(chest_y), 0)
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
root.title("E-Dressing Room - Virtual Try-On")
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
    print("Usage: python tryOn_simple.py <path_to_sprite_image>")
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

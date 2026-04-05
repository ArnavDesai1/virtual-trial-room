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

def detect_face(image):
    """Simple face detection for clothing positioning"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Load face cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Detect face
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    if len(faces) == 0:
        return None
    
    return faces[0]  # Return first face

def apply_clothing(image, path2sprite, face):
    """Apply clothing with simple positioning"""
    print(f"Attempting to load sprite from: {path2sprite}")
    sprite = cv2.imread(path2sprite, -1)
    if sprite is None:
        print(f"Could not load sprite: {path2sprite}")
        # Try alternative path
        alt_path = path2sprite.replace('static/images/', 'images/')
        print(f"Trying alternative path: {alt_path}")
        sprite = cv2.imread(alt_path, -1)
        if sprite is None:
            print(f"Could not load sprite from alternative path: {alt_path}")
            return image
    
    print(f"Successfully loaded sprite with shape: {sprite.shape}")
    
    if face is None:
        return image
    
    # Get face dimensions
    fx, fy, fw, fh = face
    
    # Calculate clothing dimensions based on face size
    clothing_width = int(fw * 2.5)  # 2.5x face width
    clothing_height = int(fh * 2.0)  # 2x face height
    
    # Resize sprite
    sprite = cv2.resize(sprite, (clothing_width, clothing_height))
    
    # Position clothing on chest (below face)
    chest_x = fx + fw//2 - clothing_width // 2
    chest_y = fy + fh + 20  # 20 pixels below face
    
    # Ensure coordinates are within image bounds
    chest_x = max(0, min(chest_x, image.shape[1] - clothing_width))
    chest_y = max(0, min(chest_y, image.shape[0] - clothing_height))
    
    print(f"Positioning clothing at: ({chest_x}, {chest_y}) with size: {clothing_width}x{clothing_height}")
    
    # Apply clothing with simple overlay
    draw_sprite_simple(image, sprite, chest_x, chest_y)
    
    print("Clothing applied successfully!")
    
    return image

def draw_sprite_simple(frame, sprite, x_offset, y_offset):
    """Simple sprite drawing with basic error handling"""
    try:
        h, w = sprite.shape[0], sprite.shape[1]
        imgH, imgW = frame.shape[0], frame.shape[1]

        print(f"Drawing sprite: {w}x{h} at offset ({x_offset}, {y_offset}) on frame {imgW}x{imgH}")

        # Clamp coordinates
        y_start = max(0, y_offset)
        y_end = min(imgH, y_offset + h)
        x_start = max(0, x_offset)
        x_end = min(imgW, x_offset + w)

        print(f"Clamped coordinates: ({x_start}, {y_start}) to ({x_end}, {y_end})")

        if y_start >= imgH or x_start >= imgW or y_end <= 0 or x_end <= 0:
            print("Coordinates out of bounds, skipping draw")
            return frame

        # Calculate sprite regions
        sprite_y_start = max(0, -y_offset)
        sprite_y_end = sprite_y_start + (y_end - y_start)
        sprite_x_start = max(0, -x_offset)
        sprite_x_end = sprite_x_start + (x_end - x_start)

        print(f"Sprite region: ({sprite_x_start}, {sprite_y_start}) to ({sprite_x_end}, {sprite_y_end})")

        if sprite_y_start >= h or sprite_x_start >= w or sprite_y_end <= 0 or sprite_x_end <= 0:
            print("Sprite region out of bounds, skipping draw")
            return frame

        # Extract regions
        frame_region = frame[y_start:y_end, x_start:x_end]
        sprite_region = sprite[sprite_y_start:sprite_y_end, sprite_x_start:sprite_x_end]

        print(f"Frame region shape: {frame_region.shape}, Sprite region shape: {sprite_region.shape}")

        # Handle alpha channel properly
        if len(sprite_region.shape) == 3 and sprite_region.shape[2] == 4:  # Has alpha channel
            # Extract alpha channel
            alpha = sprite_region[:, :, 3] / 255.0
            # Extract RGB channels
            sprite_rgb = sprite_region[:, :, :3]
            
            # Blend with frame using alpha
            for c in range(3):
                frame_region[:, :, c] = (sprite_rgb[:, :, c] * alpha + 
                                       frame_region[:, :, c] * (1.0 - alpha)).astype(np.uint8)
            print("Applied sprite with alpha blending")
        else:
            # No alpha channel, simple overlay
            if frame_region.shape == sprite_region.shape:
                frame_region[:] = sprite_region
                print("Applied sprite with same shape")
            else:
                # Resize sprite to match frame region
                sprite_resized = cv2.resize(sprite_region, (frame_region.shape[1], frame_region.shape[0]))
                frame_region[:] = sprite_resized
                print("Applied resized sprite")

    except Exception as e:
        print(f"Error in draw_sprite_simple: {e}")
    
    return frame

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label

    try:
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            status_label.config(text="Error: Could not open camera")
            return
            
        status_label.config(text="Camera ready - Looking for face...")
        
        while run_event.is_set():
            ret, image = video_capture.read()
            if not ret:
                continue
            
            if SPRITES[0] and image_path:
                # Detect face
                face = detect_face(image)
                
                if face is not None:
                    status_label.config(text="Face detected! Applying clothing...")
                    
                    # Draw face rectangle for debugging
                    fx, fy, fw, fh = face
                    cv2.rectangle(image, (fx, fy), (fx + fw, fy + fh), (0, 255, 0), 2)
                    
                    # Apply clothing
                    image = apply_clothing(image, image_path, face)
                else:
                    status_label.config(text="Looking for face...")
            else:
                status_label.config(text="Add clothing to try on...")

            # Resize image to fit the display
            height, width = image.shape[:2]
            max_width = 700
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
root.title("E-Dressing Room - Simple Fixed Virtual Try-On")
root.geometry("1000x800")
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
info_label = Label(root, text="Simple fixed virtual try-on with face detection", fg='yellow', bg='black')
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
    status_label.config(text="Clothing activated! Face detection active.")

def clear_clothing():
    global image_path
    image_path = ''
    put_sprite(0)  # Deactivate sprite
    status_label.config(text="Clothing cleared. Add new clothing to try on.")

# CLI argument must be the image path
if len(sys.argv) < 2:
    print("Usage: python tryOn_simple_fixed.py <path_to_sprite_image>")
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

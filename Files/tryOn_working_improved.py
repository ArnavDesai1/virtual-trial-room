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
    """Draw sprite with perfect alpha blending (from working version)"""
    h, w = sprite.shape[0], sprite.shape[1]
    imgH, imgW = frame.shape[0], frame.shape[1]

    # Ensure sprite has alpha channel
    if sprite.shape[2] != 4:
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
        sprite_region = cv2.resize(sprite_region, (frame_region.shape[1], frame_region.shape[0]))

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
    """Adjust sprite size based on head/face size"""
    h_sprite, w_sprite = sprite.shape[0], sprite.shape[1]
    factor = 1.0 * head_width / w_sprite
    sprite = cv2.resize(sprite, (0, 0), fx=factor, fy=factor)

    h_sprite = sprite.shape[0]
    y_orig = head_ypos - h_sprite if ontop else head_ypos

    if y_orig < 0:
        sprite = sprite[abs(y_orig):, :, :]
        y_orig = 0
    return sprite, y_orig

def apply_sprite(image, clothing_path, head_width, head_x, head_y, sprite_type):
    """Apply clothing sprite with improved positioning"""
    try:
        # Load clothing image
        sprite = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
        if sprite is None:
            print(f"Could not load clothing image: {clothing_path}")
            return image
        
        # Calculate better positioning based on head/face
        if sprite_type == 0:  # Shirt/top
            # Much better positioning for shirts
            sprite_width = head_width * 2.2  # Wider than face for shoulder coverage
            sprite_height = head_width * 1.8  # Proportional height
            
            # Position at shoulders - right below the face
            sprite_x = head_x - head_width * 0.6  # Start wider to the left
            sprite_y = head_y + head_width * 0.3  # Just below the face/neck area
            
            # Resize sprite to calculated dimensions
            sprite = cv2.resize(sprite, (int(sprite_width), int(sprite_height)))
            
            # Apply the sprite with perfect blending
            return draw_sprite(image, sprite, int(sprite_x), int(sprite_y))
        
        return image
        
    except Exception as e:
        print(f"Error applying sprite: {e}")
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
            
        status_label.config(text="Camera ready - Looking for body for perfect fitting...")
        
        while run_event.is_set():
            ret, image = video_capture.read()
            if not ret:
                continue
                
            # Flip image horizontally
            image = cv2.flip(image, 1)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            if len(faces) > 0:
                status_label.config(text="Body detected! Applying perfect fitting...")
                
                if SPRITES[0] and image_path:
                    # Use the largest face
                    face = max(faces, key=lambda x: x[2] * x[3])
                    x, y, w, h = face
                    
                    # Draw face detection rectangle for debugging
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Apply clothing with improved positioning
                    image = apply_sprite(image, image_path, w, x, y, 0)
            else:
                status_label.config(text="Looking for body...")

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

def try_on(clothing_path):
    global panelA, SPRITES, image_path, status_label
    
    # Set up GUI
    root = Tk()
    root.title("E-Dressing Room - Perfect Virtual Try-On")
    root.geometry("800x600")
    
    # Create main frame
    main_frame = Frame(root)
    main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
    
    # Video display
    panelA = Label(main_frame)
    panelA.pack(pady=10)
    
    # Status label
    status_label = Label(main_frame, text="Initializing camera...", font=("Arial", 12))
    status_label.pack(pady=5)
    
    # Control buttons
    button_frame = Frame(main_frame)
    button_frame.pack(pady=10)
    
    def try_on_clothing():
        global image_path
        image_path = clothing_path
        put_sprite(0)
        status_label.config(text="Clothing loaded - Position yourself for perfect fitting")
    
    def clear_clothing():
        global image_path
        image_path = ""
        put_sprite(0)
        status_label.config(text="Clothing cleared")
    
    def close_app():
        run_event.clear()
        root.quit()
        root.destroy()
    
    # Buttons
    try_button = Button(button_frame, text="Try it ON", command=try_on_clothing, 
                       bg="green", fg="white", font=("Arial", 12, "bold"), width=15)
    try_button.pack(side=LEFT, padx=5)
    
    clear_button = Button(button_frame, text="Clear Clothing", command=clear_clothing,
                         bg="orange", fg="white", font=("Arial", 12), width=15)
    clear_button.pack(side=LEFT, padx=5)
    
    close_button = Button(button_frame, text="Close", command=close_app,
                         bg="red", fg="white", font=("Arial", 12), width=15)
    close_button.pack(side=LEFT, padx=5)
    
    # Start camera thread
    run_event = threading.Event()
    run_event.set()
    
    camera_thread = Thread(target=cvloop, args=(run_event,))
    camera_thread.daemon = True
    camera_thread.start()
    
    # Start GUI
    root.mainloop()

# Get image path from command line arguments
if len(sys.argv) > 1:
    image_path = sys.argv[1]
else:
    print("Usage: python tryOn_working_improved.py <image_path>")
    sys.exit(1)

# Check if the image exists
if not os.path.exists(image_path):
    print(f"Error: Image file not found: {image_path}")
    sys.exit(1)

try_on(image_path)



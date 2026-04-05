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
    """Draw sprite with perfect alpha blending"""
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

    # Ensure both regions have the same shape
    if frame_region.shape != sprite_region.shape:
        sprite_region = cv2.resize(sprite_region, (frame_region.shape[1], frame_region.shape[0]))

    # Apply perfect alpha blending
    if sprite_region.shape[2] == 4:
        alpha = sprite_region[:, :, 3:4] / 255.0
        for c in range(3):
            frame_region[:, :, c] = (sprite_region[:, :, c] * alpha[:, :, 0] + 
                                   frame_region[:, :, c] * (1.0 - alpha[:, :, 0])).astype(np.uint8)
    else:
        frame_region[:, :, :3] = sprite_region[:, :, :3]

    return frame

def calculate_perfect_positioning(face_x, face_y, face_w, face_h, image_h, image_w):
    """Calculate perfect clothing positioning based on face detection"""
    
    # Calculate face center
    face_center_x = face_x + face_w // 2
    face_center_y = face_y + face_h // 2
    
    # Much more realistic shoulder width - should be wider than face
    shoulder_width = face_w * 1.8  # More realistic shoulder width
    
    # Shoulder position - right at the bottom of the face/neck area
    shoulder_y = face_y + face_h - 10  # Start at the bottom of the face
    left_shoulder_x = face_center_x - shoulder_width // 2
    right_shoulder_x = face_center_x + shoulder_width // 2
    
    # Waist position - much closer to shoulders for realistic shirt length
    waist_y = face_y + face_h + 60  # Not too far down
    waist_width = face_w * 1.6  # Slightly narrower than shoulders
    left_waist_x = face_center_x - waist_width // 2
    right_waist_x = face_center_x + waist_width // 2
    
    # Calculate clothing dimensions - use shoulder width for width
    clothing_width = int(shoulder_width)
    clothing_height = int(waist_y - shoulder_y + 10)  # From shoulders to waist
    
    # Position the clothing to start at the shoulders
    position_x = int(left_shoulder_x)
    position_y = int(shoulder_y)
    
    # Ensure minimum dimensions
    clothing_width = max(clothing_width, 80)
    clothing_height = max(clothing_height, 80)
    
    # Ensure position is within image bounds
    position_x = max(0, min(image_w - clothing_width, position_x))
    position_y = max(0, min(image_h - clothing_height, position_y))
    
    return {
        'position': (position_x, position_y),
        'size': (clothing_width, clothing_height),
        'shoulders': (int(left_shoulder_x), int(right_shoulder_x), int(shoulder_y)),
        'waist': (int(left_waist_x), int(right_waist_x), int(waist_y))
    }

def apply_perfect_clothing(image, clothing_path, positioning):
    """Apply clothing with perfect body fitting"""
    try:
        # Load clothing image
        clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
        if clothing is None:
            print(f"Could not load clothing image: {clothing_path}")
            return image
        
        position_x, position_y = positioning['position']
        clothing_width, clothing_height = positioning['size']
        
        # Resize clothing to fit body dimensions
        clothing_resized = cv2.resize(clothing, (clothing_width, clothing_height))
        
        # Apply clothing using perfect blending
        return draw_sprite(image, clothing_resized, position_x, position_y)
            
    except Exception as e:
        print(f"Error applying clothing: {e}")
        return image

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label

    try:
        # Use OpenCV's built-in face detection
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        upper_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
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
            h, w = image.shape[:2]
            
            # Detect face
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                status_label.config(text="Body detected! Applying perfect fitting...")
                
                if SPRITES[0] and image_path:
                    # Use the largest face
                    face = max(faces, key=lambda x: x[2] * x[3])
                    fx, fy, fw, fh = face
                    
                    # Calculate perfect positioning
                    positioning = calculate_perfect_positioning(fx, fy, fw, fh, h, w)
                    
                    # Draw body landmarks for debugging
                    left_shoulder_x, right_shoulder_x, shoulder_y = positioning['shoulders']
                    left_waist_x, right_waist_x, waist_y = positioning['waist']
                    
                    # Draw shoulder line
                    cv2.line(image, (left_shoulder_x, shoulder_y), (right_shoulder_x, shoulder_y), (0, 255, 0), 2)
                    cv2.circle(image, (left_shoulder_x, shoulder_y), 5, (0, 255, 0), -1)
                    cv2.circle(image, (right_shoulder_x, shoulder_y), 5, (0, 255, 0), -1)
                    
                    # Draw waist line
                    cv2.line(image, (left_waist_x, waist_y), (right_waist_x, waist_y), (0, 255, 0), 2)
                    cv2.circle(image, (left_waist_x, waist_y), 5, (0, 255, 0), -1)
                    cv2.circle(image, (right_waist_x, waist_y), 5, (0, 255, 0), -1)
                    
                    # Draw clothing area
                    pos_x, pos_y = positioning['position']
                    cloth_w, cloth_h = positioning['size']
                    cv2.rectangle(image, (int(pos_x), int(pos_y)), (int(pos_x + cloth_w), int(pos_y + cloth_h)), (255, 0, 0), 2)
                    
                    # Apply perfect clothing
                    image = apply_perfect_clothing(image, image_path, positioning)
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
    print("Usage: python tryOn_simple_improved.py <image_path>")
    sys.exit(1)

# Check if the image exists
if not os.path.exists(image_path):
    print(f"Error: Image file not found: {image_path}")
    sys.exit(1)

try_on(image_path)

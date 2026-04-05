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

class SimplePoseDetector:
    """Simple pose detection using OpenCV face detection"""
    
    def __init__(self):
        # Load face detection cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.upper_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        print("Simple pose detection initialized")
    
    def detect_body_landmarks(self, image):
        """Detect basic body landmarks using face detection"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect face
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) == 0:
                return None, None
            
            # Use the largest face
            face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = face
            
            # Calculate approximate body landmarks based on face position
            h, img_h = image.shape[:2]
            
            # Estimate body landmarks from face position
            key_points = {
                'face': (x + w//2, y + h//2),
                'left_shoulder': (x - w//4, y + h + 20),
                'right_shoulder': (x + w + w//4, y + h + 20),
                'left_hip': (x - w//6, y + h + 80),
                'right_hip': (x + w + w//6, y + h + 80),
                'chest_center': (x + w//2, y + h + 40),
                'waist_center': (x + w//2, y + h + 70)
            }
            
            return key_points, None
        except Exception as e:
            print(f"Error in simple pose detection: {e}")
            return None, None

def calculate_simple_fit_parameters(key_points, clothing_type='shirt'):
    """Calculate simple fit parameters using face-based estimation"""
    if not key_points:
        return None
    
    # Get face and estimated body positions
    face = key_points['face']
    left_shoulder = key_points['left_shoulder']
    right_shoulder = key_points['right_shoulder']
    left_hip = key_points['left_hip']
    right_hip = key_points['right_hip']
    
    # Calculate clothing boundaries
    left_edge = left_shoulder[0]
    right_edge = right_shoulder[0]
    top_edge = min(left_shoulder[1], right_shoulder[1])
    bottom_edge = max(left_hip[1], right_hip[1])
    
    # Calculate dimensions
    clothing_width = int(right_edge - left_edge)
    clothing_height = int(bottom_edge - top_edge)
    
    # Position clothing
    position_x = left_edge
    position_y = top_edge
    
    return {
        'position': (position_x, position_y),
        'size': (clothing_width, clothing_height),
        'landmarks': {
            'left_shoulder': left_shoulder,
            'right_shoulder': right_shoulder,
            'left_hip': left_hip,
            'right_hip': right_hip
        }
    }

def apply_simple_clothing(image, clothing_path, key_points, clothing_type='shirt'):
    """Apply clothing using simple face-based positioning"""
    try:
        # Load clothing image
        clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
        if clothing is None:
            print(f"Could not load clothing image: {clothing_path}")
            return image
        
        # Get fit parameters
        fit_params = calculate_simple_fit_parameters(key_points, clothing_type)
        if not fit_params:
            return image
        
        position_x, position_y = fit_params['position']
        clothing_width, clothing_height = fit_params['size']
        
        # Resize clothing to fit
        clothing_resized = cv2.resize(clothing, (clothing_width, clothing_height))
        
        # Use the working draw_sprite approach
        return draw_sprite(image, clothing_resized, position_x, position_y)
            
    except Exception as e:
        print(f"Error applying clothing: {e}")
        return image

def draw_sprite(frame, sprite, x_offset, y_offset):
    """Draw sprite with proper alpha blending (from working version)"""
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

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label, pose_detector

    try:
        video_capture = cv2.VideoCapture(0)
        
        # Optimize camera settings
        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        video_capture.set(cv2.CAP_PROP_FPS, 30)
        video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        if not video_capture.isOpened():
            status_label.config(text="Error: Could not open camera")
            return
            
        status_label.config(text="Camera ready - Looking for face...")
        
        while run_event.is_set():
            try:
                ret, image = video_capture.read()
                if not ret:
                    continue
                
                # Flip image horizontally
                image = cv2.flip(image, 1)
                
                if SPRITES[0] and image_path:
                    try:
                        # Detect body landmarks
                        key_points, landmarks = pose_detector.detect_body_landmarks(image)
                        
                        if key_points:
                            status_label.config(text="Face detected! Applying clothing...")
                            
                            # Draw landmarks for debugging
                            for point_name, (px, py) in key_points.items():
                                cv2.circle(image, (px, py), 3, (0, 255, 0), -1)
                                cv2.putText(image, point_name, (px + 5, py - 5), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                            
                            # Determine clothing type
                            clothing_type = 'shirt'
                            if 'dress' in image_path.lower():
                                clothing_type = 'dress'
                            elif 'top' in image_path.lower():
                                clothing_type = 'shirt'
                            
                            # Apply clothing
                            image = apply_simple_clothing(image, image_path, key_points, clothing_type)
                        else:
                            status_label.config(text="Looking for face...")
                    except Exception as e:
                        print(f"Error in clothing application: {e}")
                        status_label.config(text="Clothing application error...")
                else:
                    status_label.config(text="Add clothing to try on...")
            except Exception as e:
                print(f"Error in camera loop: {e}")
                status_label.config(text=f"Camera error: {str(e)}")
                break

            # Resize image to fit display
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
    global panelA, SPRITES, image_path, status_label, pose_detector
    
    # Initialize pose detector
    pose_detector = SimplePoseDetector()
    
    # Set up GUI
    root = Tk()
    root.title("E-Dressing Room - Simple Virtual Try-On")
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
        status_label.config(text="Clothing loaded - Position yourself in front of camera")
    
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
    print("Usage: python tryOn_simple_fixed_v2.py <image_path>")
    sys.exit(1)

# Check if the image exists
if not os.path.exists(image_path):
    print(f"Error: Image file not found: {image_path}")
    sys.exit(1)

try_on(image_path)

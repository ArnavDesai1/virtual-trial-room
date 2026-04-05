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

    # Apply alpha blending
    if sprite_region.shape[2] == 4:
        alpha = sprite_region[:, :, 3:4] / 255.0
        for c in range(3):
            frame_region[:, :, c] = (sprite_region[:, :, c] * alpha[:, :, 0] + 
                                   frame_region[:, :, c] * (1.0 - alpha[:, :, 0])).astype(np.uint8)
    else:
        frame_region[:, :, :3] = sprite_region[:, :, :3]

    return frame

class PreciseBodyDetector:
    """Detect actual body parts for precise clothing mapping"""
    
    def __init__(self):
        # Load cascades for body part detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.upper_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        print("Precise body detector initialized")
    
    def detect_body_landmarks(self, image):
        """Detect precise body landmarks for exact clothing mapping"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            h, w = image.shape[:2]
            
            # Detect face first
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) == 0:
                return None
            
            # Use the largest face
            face = max(faces, key=lambda x: x[2] * x[3])
            fx, fy, fw, fh = face
            
            # Detect upper body
            upper_bodies = self.upper_body_cascade.detectMultiScale(gray, 1.1, 4)
            upper_body = None
            
            if len(upper_bodies) > 0:
                # Find upper body that contains or overlaps with face
                for ub in upper_bodies:
                    ubx, uby, ubw, ubh = ub
                    # Check if upper body contains the face
                    if (ubx <= fx and uby <= fy and 
                        ubx + ubw >= fx + fw and uby + ubh >= fy + fh):
                        upper_body = ub
                        break
                
                # If no containing upper body, find the closest one
                if upper_body is None:
                    face_center = (fx + fw//2, fy + fh//2)
                    min_dist = float('inf')
                    for ub in upper_bodies:
                        ubx, uby, ubw, ubh = ub
                        ub_center = (ubx + ubw//2, uby + ubh//2)
                        dist = math.sqrt((face_center[0] - ub_center[0])**2 + (face_center[1] - ub_center[1])**2)
                        if dist < min_dist:
                            min_dist = dist
                            upper_body = ub
            
            if upper_body is not None:
                ubx, uby, ubw, ubh = upper_body
                
                # Calculate PRECISE shoulder positions from upper body detection
                # Shoulders are at the top of the upper body, slightly inward
                shoulder_y = uby + ubh * 0.1  # 10% down from top of upper body
                left_shoulder_x = ubx + ubw * 0.1   # 10% from left edge
                right_shoulder_x = ubx + ubw * 0.9  # 90% from left edge
                
                # Calculate PRECISE waist positions
                waist_y = uby + ubh * 0.7  # 70% down from top of upper body
                left_waist_x = ubx + ubw * 0.15  # 15% from left edge
                right_waist_x = ubx + ubw * 0.85  # 85% from left edge
                
                # Calculate chest center
                chest_y = (shoulder_y + waist_y) / 2
                chest_x = (left_shoulder_x + right_shoulder_x) / 2
                
            else:
                # Fallback to face-based estimation with better proportions
                face_center_x = fx + fw // 2
                face_center_y = fy + fh // 2
                
                # Estimate shoulders based on face
                shoulder_width = fw * 2.0  # Realistic shoulder width
                shoulder_y = fy + fh - 5  # Just below face
                left_shoulder_x = face_center_x - shoulder_width // 2
                right_shoulder_x = face_center_x + shoulder_width // 2
                
                # Estimate waist
                waist_width = fw * 1.7  # Slightly narrower than shoulders
                waist_y = fy + fh + 50  # Further down
                left_waist_x = face_center_x - waist_width // 2
                right_waist_x = face_center_x + waist_width // 2
                
                chest_y = (shoulder_y + waist_y) / 2
                chest_x = face_center_x
            
            # Return precise body landmarks
            landmarks = {
                'face': (fx + fw//2, fy + fh//2),
                'left_shoulder': (int(left_shoulder_x), int(shoulder_y)),
                'right_shoulder': (int(right_shoulder_x), int(shoulder_y)),
                'left_waist': (int(left_waist_x), int(waist_y)),
                'right_waist': (int(right_waist_x), int(waist_y)),
                'chest_center': (int(chest_x), int(chest_y)),
                'shoulder_center': (int((left_shoulder_x + right_shoulder_x) / 2), int(shoulder_y)),
                'waist_center': (int((left_waist_x + right_waist_x) / 2), int(waist_y))
            }
            
            return landmarks
            
        except Exception as e:
            print(f"Error in body detection: {e}")
            return None

def calculate_precise_clothing_mapping(landmarks, clothing_path):
    """Calculate precise clothing mapping to detected body parts"""
    if not landmarks:
        return None
    
    # Get the detected body parts
    left_shoulder = landmarks['left_shoulder']
    right_shoulder = landmarks['right_shoulder']
    left_waist = landmarks['left_waist']
    right_waist = landmarks['right_waist']
    
    # Load clothing to get its dimensions
    clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
    if clothing is None:
        return None
    
    orig_h, orig_w = clothing.shape[:2]
    
    # Calculate clothing dimensions based on detected body parts
    # Width = distance between left and right shoulders
    shoulder_width = right_shoulder[0] - left_shoulder[0]
    
    # Height = distance from shoulders to waist
    clothing_height = left_waist[1] - left_shoulder[1]
    
    # Calculate scale factors
    scale_x = shoulder_width / orig_w
    scale_y = clothing_height / orig_h
    
    # Use the smaller scale to maintain aspect ratio
    scale = min(scale_x, scale_y)
    
    # Calculate final dimensions
    final_width = int(orig_w * scale)
    final_height = int(orig_h * scale)
    
    # Position clothing so left edge maps to left shoulder
    position_x = left_shoulder[0]
    position_y = left_shoulder[1]
    
    return {
        'position': (position_x, position_y),
        'size': (final_width, final_height),
        'scale': scale,
        'landmarks': landmarks
    }

def apply_precise_clothing(image, clothing_path, mapping):
    """Apply clothing with precise body part mapping"""
    try:
        if not mapping:
            return image
        
        # Load clothing image
        clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
        if clothing is None:
            return image
        
        position_x, position_y = mapping['position']
        final_width, final_height = mapping['size']
        
        # Resize clothing to calculated dimensions
        clothing_resized = cv2.resize(clothing, (final_width, final_height))
        
        # Apply clothing with precise positioning
        return draw_sprite(image, clothing_resized, position_x, position_y)
        
    except Exception as e:
        print(f"Error applying precise clothing: {e}")
        return image

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label, body_detector

    try:
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            status_label.config(text="Error: Could not open camera")
            return
            
        status_label.config(text="Camera ready - Detecting body parts for precise mapping...")
        
        while run_event.is_set():
            ret, image = video_capture.read()
            if not ret:
                continue
                
            # Flip image horizontally
            image = cv2.flip(image, 1)
            
            if SPRITES[0] and image_path:
                # Detect precise body landmarks
                landmarks = body_detector.detect_body_landmarks(image)
                
                if landmarks:
                    status_label.config(text="Body parts detected! Mapping clothing precisely...")
                    
                    # Draw detected body parts
                    cv2.circle(image, landmarks['left_shoulder'], 8, (0, 255, 0), -1)
                    cv2.circle(image, landmarks['right_shoulder'], 8, (0, 255, 0), -1)
                    cv2.circle(image, landmarks['left_waist'], 8, (255, 0, 0), -1)
                    cv2.circle(image, landmarks['right_waist'], 8, (255, 0, 0), -1)
                    
                    # Draw lines connecting body parts
                    cv2.line(image, landmarks['left_shoulder'], landmarks['right_shoulder'], (0, 255, 0), 3)
                    cv2.line(image, landmarks['left_waist'], landmarks['right_waist'], (255, 0, 0), 3)
                    
                    # Calculate precise clothing mapping
                    mapping = calculate_precise_clothing_mapping(landmarks, image_path)
                    
                    if mapping:
                        # Draw clothing area
                        pos_x, pos_y = mapping['position']
                        cloth_w, cloth_h = mapping['size']
                        cv2.rectangle(image, (pos_x, pos_y), (pos_x + cloth_w, pos_y + cloth_h), (0, 0, 255), 2)
                        
                        # Apply precise clothing
                        image = apply_precise_clothing(image, image_path, mapping)
                else:
                    status_label.config(text="Looking for body parts...")
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

def try_on(clothing_path):
    global panelA, SPRITES, image_path, status_label, body_detector
    
    # Initialize precise body detector
    body_detector = PreciseBodyDetector()
    
    # Set up GUI
    root = Tk()
    root.title("E-Dressing Room - Precise Body Mapping")
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
        status_label.config(text="Clothing loaded - Detecting body parts for precise mapping")
    
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
    print("Usage: python tryOn_precise_body_mapping.py <image_path>")
    sys.exit(1)

# Check if the image exists
if not os.path.exists(image_path):
    print(f"Error: Image file not found: {image_path}")
    sys.exit(1)

try_on(image_path)



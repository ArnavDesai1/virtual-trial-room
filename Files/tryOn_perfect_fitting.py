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

class AdvancedBodyDetector:
    """Advanced body detection for perfect clothing fitting"""
    
    def __init__(self):
        # Load multiple cascades for better body detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.upper_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        print("Advanced body detector initialized")
    
    def detect_body_landmarks(self, image):
        """Detect detailed body landmarks for perfect fitting"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            h, w = image.shape[:2]
            
            # Detect face
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) == 0:
                return None, None
            
            # Use the largest face
            face = max(faces, key=lambda x: x[2] * x[3])
            fx, fy, fw, fh = face
            
            # Detect upper body
            upper_bodies = self.upper_body_cascade.detectMultiScale(gray, 1.1, 4)
            upper_body = None
            if len(upper_bodies) > 0:
                # Find upper body that overlaps with face
                for ub in upper_bodies:
                    ubx, uby, ubw, ubh = ub
                    # Check if upper body contains or is near the face
                    if (ubx <= fx + fw//2 <= ubx + ubw and 
                        uby <= fy + fh <= uby + ubh):
                        upper_body = ub
                        break
                
                # If no overlapping upper body, use the closest one
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
            
            # Calculate body landmarks with improved positioning
            if upper_body is not None:
                ubx, uby, ubw, ubh = upper_body
                
                # Calculate shoulders based on upper body detection
                shoulder_y = uby + ubh * 0.2  # Shoulders are 20% down from top of upper body
                left_shoulder_x = ubx + ubw * 0.15  # 15% from left edge
                right_shoulder_x = ubx + ubw * 0.85  # 85% from left edge
                
                # Calculate waist based on upper body
                waist_y = uby + ubh * 0.8  # Waist is 80% down from top of upper body
                left_waist_x = ubx + ubw * 0.2  # 20% from left edge
                right_waist_x = ubx + ubw * 0.8  # 80% from left edge
                
                # Ensure waist coordinates are valid
                left_waist_x = max(0, min(w-1, left_waist_x))
                right_waist_x = max(0, min(w-1, right_waist_x))
                waist_y = max(0, min(h-1, waist_y))
                
                # Calculate chest center
                chest_y = (shoulder_y + waist_y) / 2
                chest_x = (left_shoulder_x + right_shoulder_x) / 2
                
                # Detect body tilt/rotation
                body_tilt = self._detect_body_tilt(left_shoulder_x, right_shoulder_x, left_waist_x, right_waist_x)
                
            else:
                # Fallback to face-based estimation with better scaling
                face_center_x = fx + fw // 2
                face_center_y = fy + fh // 2
                
                # Better shoulder estimation based on face size
                shoulder_width = fw * 2.2  # Wider shoulders
                shoulder_y = fy + fh + 15  # Just below face
                left_shoulder_x = face_center_x - shoulder_width // 2
                right_shoulder_x = face_center_x + shoulder_width // 2
                
                # Waist estimation
                waist_width = fw * 1.8  # Slightly narrower than shoulders
                waist_y = fy + fh + 80  # Further down
                left_waist_x = face_center_x - waist_width // 2
                right_waist_x = face_center_x + waist_width // 2
                
                # Ensure all coordinates are valid
                left_shoulder_x = max(0, min(w-1, left_shoulder_x))
                right_shoulder_x = max(0, min(w-1, right_shoulder_x))
                left_waist_x = max(0, min(w-1, left_waist_x))
                right_waist_x = max(0, min(w-1, right_waist_x))
                shoulder_y = max(0, min(h-1, shoulder_y))
                waist_y = max(0, min(h-1, waist_y))
                
                chest_y = (shoulder_y + waist_y) / 2
                chest_x = face_center_x
                body_tilt = 0
            
            # Create key points with improved accuracy
            key_points = {
                'face': (fx + fw//2, fy + fh//2),
                'left_shoulder': (int(left_shoulder_x), int(shoulder_y)),
                'right_shoulder': (int(right_shoulder_x), int(shoulder_y)),
                'left_waist': (int(left_waist_x), int(waist_y)),
                'right_waist': (int(right_waist_x), int(waist_y)),
                'chest_center': (int(chest_x), int(chest_y)),
                'waist_center': (int((left_waist_x + right_waist_x) / 2), int(waist_y)),
                'shoulder_center': (int((left_shoulder_x + right_shoulder_x) / 2), int(shoulder_y)),
                'body_tilt': body_tilt
            }
            
            return key_points, None
            
        except Exception as e:
            print(f"Error in body detection: {e}")
            return None, None
    
    def _detect_body_tilt(self, left_shoulder_x, right_shoulder_x, left_waist_x, right_waist_x):
        """Detect body tilt/rotation for better fitting"""
        try:
            # Calculate shoulder angle
            shoulder_dx = right_shoulder_x - left_shoulder_x
            shoulder_angle = 0  # Default no tilt
            
            # Calculate waist angle
            waist_dx = right_waist_x - left_waist_x
            
            # If shoulders and waist have different widths, there's tilt
            if abs(shoulder_dx - waist_dx) > 10:  # Significant difference
                shoulder_angle = math.atan2(shoulder_dx - waist_dx, 100) * 180 / math.pi
                shoulder_angle = max(-15, min(15, shoulder_angle))  # Limit to ±15 degrees
            
            return shoulder_angle
        except:
            return 0

def calculate_perfect_fit_parameters(key_points, clothing_type='shirt'):
    """Calculate perfect fit parameters with body shape consideration"""
    if not key_points:
        return None
    
    # Get body landmarks
    left_shoulder = key_points.get('left_shoulder', (0, 0))
    right_shoulder = key_points.get('right_shoulder', (0, 0))
    left_waist = key_points.get('left_waist', (0, 0))
    right_waist = key_points.get('right_waist', (0, 0))
    body_tilt = key_points.get('body_tilt', 0)
    
    # Calculate exact clothing boundaries
    # Shoulder-to-shoulder fitting
    left_edge = left_shoulder[0]
    right_edge = right_shoulder[0]
    shoulder_width = right_edge - left_edge
    
    # Waist-to-waist fitting
    left_waist_edge = left_waist[0]
    right_waist_edge = right_waist[0]
    waist_width = right_waist_edge - left_waist_edge
    
    # Use the wider of shoulder or waist width for better coverage
    clothing_width = max(shoulder_width, waist_width)
    
    # Position clothing to center on shoulders
    shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
    position_x = int(shoulder_center_x - clothing_width / 2)
    
    # Vertical positioning - from shoulders to waist
    top_edge = min(left_shoulder[1], right_shoulder[1])
    bottom_edge = max(left_waist[1], right_waist[1])
    clothing_height = int(bottom_edge - top_edge)
    position_y = int(top_edge)
    
    # Apply body tilt correction
    if abs(body_tilt) > 2:  # Significant tilt
        # Adjust position slightly based on tilt
        tilt_offset = int(body_tilt * 0.1)  # Small adjustment
        position_x += tilt_offset
    
    # Ensure minimum dimensions
    clothing_width = max(clothing_width, 100)
    clothing_height = max(clothing_height, 150)
    
    return {
        'position': (position_x, position_y),
        'size': (int(clothing_width), int(clothing_height)),
        'body_tilt': body_tilt,
        'landmarks': {
            'left_shoulder': left_shoulder,
            'right_shoulder': right_shoulder,
            'left_waist': left_waist,
            'right_waist': right_waist
        }
    }

def apply_perfect_clothing(image, clothing_path, key_points, clothing_type='shirt'):
    """Apply clothing with perfect body fitting"""
    try:
        # Load clothing image
        clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
        if clothing is None:
            print(f"Could not load clothing image: {clothing_path}")
            return image
        
        # Get perfect fit parameters
        fit_params = calculate_perfect_fit_parameters(key_points, clothing_type)
        if not fit_params:
            return image
        
        position_x, position_y = fit_params['position']
        clothing_width, clothing_height = fit_params['size']
        body_tilt = fit_params['body_tilt']
        
        # Resize clothing to fit body dimensions
        clothing_resized = cv2.resize(clothing, (clothing_width, clothing_height))
        
        # Apply body tilt if significant
        if abs(body_tilt) > 2:
            # Create rotation matrix
            center = (clothing_width // 2, clothing_height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, body_tilt, 1.0)
            
            # Rotate clothing to match body tilt
            clothing_resized = cv2.warpAffine(clothing_resized, rotation_matrix, 
                                            (clothing_width, clothing_height))
        
        # Use the working draw_sprite approach for perfect blending
        return draw_sprite(image, clothing_resized, position_x, position_y)
            
    except Exception as e:
        print(f"Error applying perfect clothing: {e}")
        return image

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

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label, body_detector

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
            
        status_label.config(text="Camera ready - Detecting body for perfect fitting...")
        
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
                        key_points, landmarks = body_detector.detect_body_landmarks(image)
                        
                        if key_points:
                            status_label.config(text="Body detected! Applying perfect fitting...")
                            
                            # Draw body landmarks for debugging
                            for point_name, (px, py) in key_points.items():
                                if isinstance(px, (int, float)) and isinstance(py, (int, float)):
                                    cv2.circle(image, (int(px), int(py)), 3, (0, 255, 0), -1)
                                    cv2.putText(image, point_name, (int(px) + 5, int(py) - 5), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                            
                            # Determine clothing type
                            clothing_type = 'shirt'
                            if 'dress' in image_path.lower():
                                clothing_type = 'dress'
                            elif 'top' in image_path.lower():
                                clothing_type = 'shirt'
                            
                            # Apply perfect clothing fitting
                            image = apply_perfect_clothing(image, image_path, key_points, clothing_type)
                        else:
                            status_label.config(text="Looking for body...")
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
    global panelA, SPRITES, image_path, status_label, body_detector
    
    # Initialize advanced body detector
    body_detector = AdvancedBodyDetector()
    
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
    print("Usage: python tryOn_perfect_fitting.py <image_path>")
    sys.exit(1)

# Check if the image exists
if not os.path.exists(image_path):
    print(f"Error: Image file not found: {image_path}")
    sys.exit(1)

try_on(image_path)

from tkinter import *
from PIL import Image, ImageTk
import cv2, threading, time, sys, os
import numpy as np
from threading import Thread

# Try to import mediapipe, fallback to simple detection if not available
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    print("Mediapipe not available, using simple face detection")
    MEDIAPIPE_AVAILABLE = False

# Globals
SPRITES = [0, 0, 0, 0, 0, 0]
image_path = ''
panelA = None
status_label = None

def put_sprite(num):
    global SPRITES
    SPRITES = [0] * len(SPRITES)
    if 0 <= num < len(SPRITES):
        SPRITES[num] = 1

def detect_face_simple(image):
    """Simple face detection that always works"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) > 0:
        return faces[0]  # Return first face
    return None

def detect_pose_keypoints_mediapipe(image_bgr):
    """MediaPipe pose detection with proper error handling"""
    if not MEDIAPIPE_AVAILABLE:
        return None
        
    h, w = image_bgr.shape[:2]
    try:
        with mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        ) as pose:
            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            result = pose.process(image_rgb)
            
            if not result.pose_landmarks:
                return None
                
            lm = result.pose_landmarks.landmark
            
            def p(idx):
                return int(lm[idx].x * w), int(lm[idx].y * h)
            
            # Get key points with validation
            left_shoulder = p(mp.solutions.pose.PoseLandmark.LEFT_SHOULDER)
            right_shoulder = p(mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER)
            left_hip = p(mp.solutions.pose.PoseLandmark.LEFT_HIP)
            right_hip = p(mp.solutions.pose.PoseLandmark.RIGHT_HIP)
            
            # Validate that points are reasonable
            shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
            body_height = abs(left_hip[1] - left_shoulder[1])
            
            if shoulder_width < 20 or body_height < 30:  # Too small to be realistic
                return None
                
            return {
                'left_shoulder': left_shoulder,
                'right_shoulder': right_shoulder,
                'left_hip': left_hip,
                'right_hip': right_hip,
                'detected': True
            }
    except Exception as e:
        print(f"Pose detection error: {e}")
        return None

def calculate_body_from_face_enhanced(face, image_shape):
    """Enhanced body calculation from face detection"""
    if face is None:
        return None
    
    face_x, face_y, face_w, face_h = face
    img_h, img_w = image_shape[:2]
    
    # Face center
    face_center_x = face_x + face_w // 2
    face_center_y = face_y + face_h // 2
    
    # Enhanced shoulder calculation
    shoulder_width = face_w * 2.3  # Slightly wider
    shoulder_y = face_y + face_h + 10  # Closer to face
    
    left_shoulder_x = face_center_x - shoulder_width // 2
    right_shoulder_x = face_center_x + shoulder_width // 2
    
    # Enhanced waist calculation
    waist_y = shoulder_y + face_h * 1.1  # Better proportion
    waist_width = shoulder_width * 0.9  # More realistic ratio
    
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
        'left_hip': (left_waist_x, waist_y),
        'right_hip': (right_waist_x, waist_y),
        'detected': True
    }

def apply_clothing_perfect(image, clothing_path, body_data):
    """Perfect clothing application with accurate body mapping"""
    if not body_data or not body_data.get('detected', False):
        return image
        
    # Load clothing with error handling
    clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
    if clothing is None:
        print(f"Could not load clothing: {clothing_path}")
        return image
    
    # Ensure clothing has proper format
    if len(clothing.shape) == 2:
        # Grayscale, convert to BGRA
        clothing = cv2.cvtColor(clothing, cv2.COLOR_GRAY2BGRA)
    elif clothing.shape[2] == 3:
        # BGR, add alpha channel
        alpha = np.ones((clothing.shape[0], clothing.shape[1], 1), dtype=np.uint8) * 255
        clothing = np.concatenate([clothing, alpha], axis=2)
    
    # Get body measurements
    left_shoulder = np.array(body_data['left_shoulder'], dtype=np.float32)
    right_shoulder = np.array(body_data['right_shoulder'], dtype=np.float32)
    left_hip = np.array(body_data.get('left_hip', body_data['left_shoulder']), dtype=np.float32)
    right_hip = np.array(body_data.get('right_hip', body_data['right_shoulder']), dtype=np.float32)
    
    # Calculate torso dimensions
    shoulder_width = np.linalg.norm(right_shoulder - left_shoulder)
    torso_height = np.linalg.norm((left_hip + right_hip) / 2 - (left_shoulder + right_shoulder) / 2)
    
    # Ensure minimum dimensions
    shoulder_width = max(40, shoulder_width)
    torso_height = max(60, torso_height)
    
    # Calculate clothing scale
    orig_h, orig_w = clothing.shape[:2]
    scale_x = shoulder_width / orig_w
    scale_y = torso_height / orig_h
    scale = min(scale_x, scale_y)
    scale = max(0.3, min(scale, 3.0))  # Reasonable scale limits
    
    # Resize clothing
    new_width = int(orig_w * scale)
    new_height = int(orig_h * scale)
    resized_clothing = cv2.resize(clothing, (new_width, new_height))
    
    # Calculate positioning - center on shoulders with neck gap
    neck_gap = max(8, shoulder_width * 0.05)  # Small neck gap
    start_x = int(left_shoulder[0] + (shoulder_width - new_width) // 2)
    start_y = int(left_shoulder[1] - neck_gap)
    
    # Apply clothing with perfect overlay
    return overlay_clothing_perfect(image, resized_clothing, (start_x, start_y))

def overlay_clothing_perfect(body_image, clothing, start_pos):
    """Perfect clothing overlay with accurate positioning"""
    result = body_image.copy()
    h, w = clothing.shape[:2]
    img_h, img_w = body_image.shape[:2]
    
    # Calculate placement region with bounds checking
    start_x, start_y = start_pos
    end_x = min(start_x + w, img_w)
    end_y = min(start_y + h, img_h)
    start_x = max(0, start_x)
    start_y = max(0, start_y)
    
    # Ensure we have valid dimensions
    if end_x <= start_x or end_y <= start_y:
        return result
    
    # Extract regions
    body_region = result[start_y:end_y, start_x:end_x]
    clothing_region = clothing[:end_y-start_y, :end_x-start_x]
    
    # Ensure same dimensions
    if body_region.shape != clothing_region.shape:
        clothing_region = cv2.resize(clothing_region, (body_region.shape[1], body_region.shape[0]))
    
    # Perfect alpha blending
    if len(clothing_region.shape) == 3 and clothing_region.shape[2] == 4:
        alpha = clothing_region[:, :, 3:4] / 255.0
        
        # Apply slight blur to alpha for smoother edges
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
        
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

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label
    
    # Initialize camera with optimal settings
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        status_label.config(text="Error: Could not open camera")
        return
    
    # Optimize camera settings for stability
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    
    # Frame processing variables
    frame_count = 0
    last_body_data = None
    detection_interval = 3
    clothing_interval = 2
    
    try:
        while run_event.is_set():
            ret, image = cap.read()
            if not ret:
                # Camera recovery
                cap.release()
                time.sleep(0.1)
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    status_label.config(text="Camera error - trying to reconnect...")
                    time.sleep(1)
                    continue
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                continue
            
            frame_count += 1
            
            # Flip image horizontally for mirror effect
            image = cv2.flip(image, 1)
            
            # Detect body periodically
            if frame_count % detection_interval == 0:
                body_data = None
                
                # Try MediaPipe pose detection first
                if MEDIAPIPE_AVAILABLE:
                    body_data = detect_pose_keypoints_mediapipe(image)
                
                # Fallback to face detection
                if body_data is None:
                    face = detect_face_simple(image)
                    if face is not None:
                        body_data = calculate_body_from_face_enhanced(face, image.shape)
                
                if body_data:
                    last_body_data = body_data
            
            # Apply clothing if body detected and sprite active
            if last_body_data:
                if SPRITES[0] and image_path and frame_count % clothing_interval == 0:
                    status_label.config(text="Body detected! Applying clothing...")
                    image = apply_clothing_perfect(image, image_path, last_body_data)
                else:
                    status_label.config(text="Body detected! Ready for clothing...")
            else:
                status_label.config(text="Looking for body...")
            
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
            
            # Small delay
            time.sleep(0.02)
            
    except Exception as e:
        print(f"Camera loop error: {e}")
        status_label.config(text=f"Error: {str(e)}")
    finally:
        cap.release()

def main():
    global panelA, status_label, image_path
    
    if len(sys.argv) != 2:
        print("Usage: python tryOn_final_perfect.py <path_to_clothing_image>")
        return
    
    image_path = sys.argv[1]
    
    # Verify clothing image exists
    if not os.path.exists(image_path):
        print(f"Error: Clothing image not found: {image_path}")
        return
    
    # Create GUI
    root = Tk()
    root.title("E-Dressing Room - Final Perfect")
    root.geometry("800x700")
    
    # Video display
    panelA = Label(root)
    panelA.pack(pady=10)
    
    # Status label
    status_label = Label(root, text="Initializing perfect body detection...", font=("Arial", 12))
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

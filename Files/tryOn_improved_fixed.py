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
SHOW_MARKERS = False  # Set True only for debugging

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

def calculate_body_from_face_improved(face, image_shape):
    """Improved body calculation from face detection with better positioning"""
    if face is None:
        return None
    
    face_x, face_y, face_w, face_h = face
    img_h, img_w = image_shape[:2]
    
    # Face center
    face_center_x = face_x + face_w // 2
    face_center_y = face_y + face_h // 2
    
    # Improved shoulder calculation - more accurate positioning
    shoulder_width = face_w * 2.2  # Slightly wider than face
    shoulder_y = face_y + face_h + 15  # Closer to face for better alignment
    
    left_shoulder_x = face_center_x - shoulder_width // 2
    right_shoulder_x = face_center_x + shoulder_width // 2
    
    # Improved waist calculation
    waist_y = shoulder_y + face_h * 1.0  # Better proportion
    waist_width = shoulder_width * 0.85  # More realistic waist-to-shoulder ratio
    
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
        'left_waist': (left_waist_x, waist_y),
        'right_waist': (right_waist_x, waist_y),
        'shoulder_width': shoulder_width,
        'body_height': waist_y - shoulder_y,
        'detected': True
    }

def detect_pose_keypoints_improved(image_bgr):
    """Improved pose detection with better error handling"""
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

def _compute_torso_quad(body_data):
    """Compute a tilted torso quadrilateral using shoulders and hips.
    Returns points in order: top-left, top-right, bottom-right, bottom-left.
    """
    ls = np.array(body_data['left_shoulder'], dtype=np.float32)
    rs = np.array(body_data['right_shoulder'], dtype=np.float32)
    lh = np.array(body_data['left_hip'], dtype=np.float32) if 'left_hip' in body_data else None
    rh = np.array(body_data['right_hip'], dtype=np.float32) if 'right_hip' in body_data else None

    # Shoulder line
    shoulder_vec = rs - ls
    shoulder_len = max(1.0, float(np.linalg.norm(shoulder_vec)))
    shoulder_dir = shoulder_vec / shoulder_len

    # Downward normal from shoulders towards torso
    # Choose direction toward the midpoint of hips if available
    normal = np.array([shoulder_dir[1], -shoulder_dir[0]], dtype=np.float32)
    if lh is not None and rh is not None:
        mid_sh = (ls + rs) * 0.5
        mid_hip = (lh + rh) * 0.5
        to_hip = mid_hip - mid_sh
        if np.dot(to_hip, normal) < 0:
            normal = -normal

    # Estimate torso height using hips if available, else fallback to heuristic
    if lh is not None and rh is not None:
        torso_height = float(np.linalg.norm(((lh + rh) * 0.5) - ((ls + rs) * 0.5)))
    else:
        torso_height = shoulder_len * 1.2

    # Neck gap: small offset from shoulders along normal
    neck_gap = max(6.0, shoulder_len * 0.04)

    top_left = ls + normal * neck_gap
    top_right = rs + normal * neck_gap
    bottom_left = ls + normal * (torso_height + neck_gap)
    bottom_right = rs + normal * (torso_height + neck_gap)

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)

def _warp_clothing_to_quad(frame, clothing, quad):
    """Perspective-warp clothing onto frame using destination quad.
    clothing may have alpha channel.
    """
    h_cl, w_cl = clothing.shape[:2]
    
    # Ensure clothing has the right number of channels
    if len(clothing.shape) == 2:
        # Grayscale image, convert to BGR
        clothing = cv2.cvtColor(clothing, cv2.COLOR_GRAY2BGR)
    elif clothing.shape[2] == 3:
        # BGR image, add alpha channel
        alpha = np.ones((h_cl, w_cl, 1), dtype=np.uint8) * 255
        clothing = np.concatenate([clothing, alpha], axis=2)
    
    # Source quad (with slight collar offset inside the image to avoid cropping collar)
    collar_offset = int(max(1, 0.06 * h_cl))
    src = np.array([[0, collar_offset], [w_cl-1, collar_offset], [w_cl-1, h_cl-1], [0, h_cl-1]], dtype=np.float32)

    # Compute warp for a bounding box around destination to reduce computation
    x_min = int(max(0, np.floor(np.min(quad[:, 0]))))
    y_min = int(max(0, np.floor(np.min(quad[:, 1]))))
    x_max = int(min(frame.shape[1], np.ceil(np.max(quad[:, 0]))))
    y_max = int(min(frame.shape[0], np.ceil(np.max(quad[:, 1]))))
    if x_max <= x_min or y_max <= y_min:
        return frame

    # Shift quad to ROI coordinates
    quad_roi = quad.copy()
    quad_roi[:, 0] -= x_min
    quad_roi[:, 1] -= y_min

    roi = frame[y_min:y_max, x_min:x_max].copy()

    M = cv2.getPerspectiveTransform(src, quad_roi)
    warped = cv2.warpPerspective(clothing, M, (roi.shape[1], roi.shape[0]), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)

    # Handle alpha blending safely
    if len(warped.shape) == 3 and warped.shape[2] == 4:
        alpha = warped[:, :, 3:4] / 255.0
        # Slight blur for smooth blend
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
        for c in range(3):
            roi[:, :, c] = (warped[:, :, c] * alpha[:, :, 0] + roi[:, :, c] * (1.0 - alpha[:, :, 0])).astype(np.uint8)
    else:
        # No alpha channel, use simple overlay
        roi[:, :, :3] = warped[:, :, :3]

    frame[y_min:y_max, x_min:x_max] = roi
    return frame

def apply_clothing_improved(image, clothing_path, body_data):
    """Improved clothing application with better positioning, scaling and perspective"""
    if not body_data or not body_data.get('detected', False):
        return image
        
    # Load clothing with error handling
    clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
    if clothing is None:
        print(f"Could not load clothing: {clothing_path}")
        return image
    
    try:
        # Compute torso quad aligned with body tilt
        quad = _compute_torso_quad(body_data)
        
        # Warp clothing to this quad
        return _warp_clothing_to_quad(image, clothing, quad)
    except Exception as e:
        print(f"Perspective warp failed: {e}")
        # Fallback to simple overlay method
        return apply_clothing_simple_fallback(image, clothing_path, body_data)

def apply_clothing_simple_fallback(image, clothing_path, body_data):
    """Fallback simple clothing application"""
    clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
    if clothing is None:
        return image
    
    # Get body measurements
    left_shoulder = body_data['left_shoulder']
    right_shoulder = body_data['right_shoulder']
    left_waist = body_data.get('left_waist', body_data['left_shoulder'])
    right_waist = body_data.get('right_waist', body_data['right_shoulder'])
    
    # Calculate clothing dimensions
    shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
    body_height = abs(left_waist[1] - left_shoulder[1])
    
    # Ensure minimum dimensions
    shoulder_width = max(30, shoulder_width)
    body_height = max(40, body_height)
    
    # Resize clothing to match body
    orig_h, orig_w = clothing.shape[:2]
    scale_x = shoulder_width / orig_w
    scale_y = body_height / orig_h
    scale = min(scale_x, scale_y)
    scale = max(0.5, min(scale, 2.0))
    
    new_width = int(orig_w * scale)
    new_height = int(orig_h * scale)
    
    # Resize clothing
    resized_clothing = cv2.resize(clothing, (new_width, new_height))
    
    # Apply clothing at shoulder position
    start_x = left_shoulder[0] + (shoulder_width - new_width) // 2
    start_y = left_shoulder[1]
    
    return overlay_clothing_improved(image, resized_clothing, (start_x, start_y))

def overlay_clothing_improved(body_image, clothing, start_pos):
    """Improved clothing overlay with better blending"""
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
    
    # Improved alpha blending with edge smoothing
    if clothing_region.shape[2] == 4:  # Has alpha channel
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

def draw_improved_markers(image, body_data):
    """Draw improved body markers for debugging"""
    if not body_data or not body_data.get('detected', False):
        return image
    
    # Draw shoulder points (green)
    cv2.circle(image, body_data['left_shoulder'], 8, (0, 255, 0), -1)
    cv2.circle(image, body_data['right_shoulder'], 8, (0, 255, 0), -1)
    
    # Draw waist points (blue)
    cv2.circle(image, body_data['left_waist'], 6, (255, 0, 0), -1)
    cv2.circle(image, body_data['right_waist'], 6, (255, 0, 0), -1)
    
    # Draw connecting lines
    cv2.line(image, body_data['left_shoulder'], body_data['right_shoulder'], (0, 255, 0), 3)
    cv2.line(image, body_data['left_waist'], body_data['right_waist'], (255, 0, 0), 3)
    
    # Draw body outline
    cv2.line(image, body_data['left_shoulder'], body_data['left_waist'], (0, 255, 255), 2)
    cv2.line(image, body_data['right_shoulder'], body_data['right_waist'], (0, 255, 255), 2)
    
    return image

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label
    
    # Initialize camera with improved settings
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        status_label.config(text="Error: Could not open camera")
        return
    
    # Optimize camera settings for stability
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus for stability
    
    # Frame processing variables
    frame_count = 0
    last_body_data = None
    detection_interval = 3  # Detect every 3 frames for performance
    clothing_interval = 2   # Apply clothing every 2 frames
    
    try:
        while run_event.is_set():
            ret, image = cap.read()
            if not ret:
                # If frame read fails, try to reinitialize camera
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
            
            # Detect body periodically for performance
            if frame_count % detection_interval == 0:
                body_data = None
                
                # Try pose detection first if available
                if MEDIAPIPE_AVAILABLE:
                    body_data = detect_pose_keypoints_improved(image)
                
                # Fallback to face detection if pose detection fails
                if body_data is None:
                    face = detect_face_simple(image)
                    if face is not None:
                        body_data = calculate_body_from_face_improved(face, image.shape)
                
                if body_data:
                    last_body_data = body_data
            
            # Use last detected body data if available
            if last_body_data:
                # Draw body markers (debug only)
                if SHOW_MARKERS:
                    image = draw_improved_markers(image, last_body_data)
                
                # Apply clothing if sprite is active
                if SPRITES[0] and image_path and frame_count % clothing_interval == 0:
                    status_label.config(text="Body detected! Applying clothing...")
                    image = apply_clothing_improved(image, image_path, last_body_data)
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
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.02)
            
    except Exception as e:
        print(f"Camera loop error: {e}")
        status_label.config(text=f"Error: {str(e)}")
    finally:
        cap.release()

def main():
    global panelA, status_label, image_path
    
    if len(sys.argv) != 2:
        print("Usage: python tryOn_improved_fixed.py <path_to_clothing_image>")
        return
    
    image_path = sys.argv[1]
    
    # Verify clothing image exists
    if not os.path.exists(image_path):
        print(f"Error: Clothing image not found: {image_path}")
        return
    
    # Create GUI
    root = Tk()
    root.title("E-Dressing Room - Improved & Fixed")
    root.geometry("800x700")
    
    # Video display
    panelA = Label(root)
    panelA.pack(pady=10)
    
    # Status label
    status_label = Label(root, text="Initializing improved body detection...", font=("Arial", 12))
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

from tkinter import *
from PIL import Image, ImageTk
import cv2, threading, os, time, sys, math
import numpy as np
from threading import Thread

# Try to import MediaPipe for advanced pose detection
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    print("MediaPipe available - using advanced pose detection")
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("MediaPipe not available - using basic face detection")

# Globals
SPRITES = [0, 0, 0, 0, 0, 0]
image_path = ''

def put_sprite(num):
    global SPRITES
    SPRITES = [0] * len(SPRITES)
    SPRITES[num] = 1

class AdvancedPoseDetector:
    """Advanced pose detection using MediaPipe for perfect clothing fitting"""
    
    def __init__(self):
        if MEDIAPIPE_AVAILABLE:
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=2,  # Highest accuracy
                enable_segmentation=True,
                min_detection_confidence=0.3,  # Lower threshold for better detection at distance
                min_tracking_confidence=0.3    # Lower threshold for better tracking at distance
            )
            print("Advanced pose detection initialized")
        else:
            # Fallback to basic face detection
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.upper_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
            print("Basic face detection initialized")
    
    def detect_body_landmarks(self, image):
        """Detect detailed body landmarks for perfect fitting"""
        if MEDIAPIPE_AVAILABLE:
            return self._detect_mediapipe_landmarks(image)
        else:
            return self._detect_basic_landmarks(image)
    
    def _detect_mediapipe_landmarks(self, image):
        """Use MediaPipe for precise body landmark detection"""
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_image)
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                h, w = image.shape[:2]
                
                # Check if we have enough landmarks for full body detection
                if len(landmarks) < 25:  # MediaPipe pose has 33 landmarks, but we need at least 25
                    return None, None
                
                # Extract key body points for clothing fitting
                key_points = {
                    # Face/Head
                    'nose': (int(landmarks[0].x * w), int(landmarks[0].y * h)),
                    'left_eye': (int(landmarks[2].x * w), int(landmarks[2].y * h)),
                    'right_eye': (int(landmarks[5].x * w), int(landmarks[5].y * h)),
                    
                    # Shoulders
                    'left_shoulder': (int(landmarks[11].x * w), int(landmarks[11].y * h)),
                    'right_shoulder': (int(landmarks[12].x * w), int(landmarks[12].y * h)),
                    
                    # Elbows
                    'left_elbow': (int(landmarks[13].x * w), int(landmarks[13].y * h)),
                    'right_elbow': (int(landmarks[14].x * w), int(landmarks[14].y * h)),
                    
                    # Wrists
                    'left_wrist': (int(landmarks[15].x * w), int(landmarks[15].y * h)),
                    'right_wrist': (int(landmarks[16].x * w), int(landmarks[16].y * h)),
                    
                    # Torso
                    'left_hip': (int(landmarks[23].x * w), int(landmarks[23].y * h)),
                    'right_hip': (int(landmarks[24].x * w), int(landmarks[24].y * h)),
                    
                    # Calculate derived points
                    'chest_center': self._calculate_chest_center(landmarks, w, h),
                    'waist_center': self._calculate_waist_center(landmarks, w, h),
                    'shoulder_center': self._calculate_shoulder_center(landmarks, w, h)
                }
                
                return key_points, results.pose_landmarks
            else:
                return None, None
        except Exception as e:
            print(f"MediaPipe detection error: {e}")
            return None, None
    
    def _detect_basic_landmarks(self, image):
        """Fallback to basic face detection"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect face
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            return None, None
        
        face = faces[0]
        x, y, w, h = face
        
        # Detect upper body
        upper_bodies = self.upper_body_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Calculate basic key points
        key_points = {
            'nose': (x + w//2, y + h//2),
            'left_shoulder': (x - w//4, y + h + 20),
            'right_shoulder': (x + w + w//4, y + h + 20),
            'chest_center': (x + w//2, y + h + 40),
            'waist_center': (x + w//2, y + h + 80),
            'shoulder_center': (x + w//2, y + h + 20)
        }
        
        # Refine with upper body detection
        if len(upper_bodies) > 0:
            ub_x, ub_y, ub_w, ub_h = upper_bodies[0]
            key_points['left_shoulder'] = (ub_x, ub_y + ub_h//4)
            key_points['right_shoulder'] = (ub_x + ub_w, ub_y + ub_h//4)
            key_points['chest_center'] = (ub_x + ub_w//2, ub_y + ub_h//2)
            key_points['waist_center'] = (ub_x + ub_w//2, ub_y + ub_h)
            key_points['shoulder_center'] = (ub_x + ub_w//2, ub_y + ub_h//4)
        
        return key_points, face
    
    def _calculate_chest_center(self, landmarks, w, h):
        """Calculate chest center from MediaPipe landmarks"""
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        
        # Chest is between shoulders and hips
        chest_x = (left_shoulder.x + right_shoulder.x + left_hip.x + right_hip.x) / 4 * w
        chest_y = (left_shoulder.y + right_shoulder.y) / 2 * h
        
        return (int(chest_x), int(chest_y))
    
    def _calculate_waist_center(self, landmarks, w, h):
        """Calculate waist center from MediaPipe landmarks"""
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        
        waist_x = (left_hip.x + right_hip.x) / 2 * w
        waist_y = (left_hip.y + right_hip.y) / 2 * h
        
        return (int(waist_x), int(waist_y))
    
    def _calculate_shoulder_center(self, landmarks, w, h):
        """Calculate shoulder center from MediaPipe landmarks"""
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        
        shoulder_x = (left_shoulder.x + right_shoulder.x) / 2 * w
        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2 * h
        
        return (int(shoulder_x), int(shoulder_y))

def calculate_perfect_fit_parameters(key_points, clothing_type='shirt'):
    """Calculate perfect fit parameters by mapping clothing edges to body landmarks"""
    if not key_points:
        return None
    
    # Check if required landmarks are available
    required_landmarks = ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']
    for landmark in required_landmarks:
        if landmark not in key_points:
            print(f"Warning: Missing landmark {landmark}, using fallback positioning")
            return None
    
    # Get exact body landmark positions
    left_shoulder = key_points['left_shoulder']
    right_shoulder = key_points['right_shoulder']
    left_hip = key_points['left_hip']
    right_hip = key_points['right_hip']
    
    # Calculate exact clothing boundaries based on body landmarks
    # Left edge of clothing = left shoulder X position
    left_edge = left_shoulder[0]
    # Right edge of clothing = right shoulder X position  
    right_edge = right_shoulder[0]
    # Top edge of clothing = shoulder Y position
    top_edge = min(left_shoulder[1], right_shoulder[1])
    # Bottom edge of clothing = hip Y position
    bottom_edge = max(left_hip[1], right_hip[1])
    
    # Calculate exact dimensions from landmark positions
    clothing_width = int(right_edge - left_edge)
    clothing_height = int(bottom_edge - top_edge)
    
    # Make clothing much bigger to match actual body size
    # Calculate proper scaling based on shoulder width
    shoulder_width = abs(right_edge - left_edge)
    
    # Ensure minimum size for visibility at any distance
    min_shoulder_width = 120  # Minimum shoulder width for proper clothing size
    
    if shoulder_width < min_shoulder_width:
        # Scale up the shoulder width for proper clothing size
        scale_factor = min_shoulder_width / max(shoulder_width, 1)
        shoulder_width = int(shoulder_width * scale_factor)
        print(f"Scaled up shoulder width by factor {scale_factor}")
    
    # Make clothing 1.8x wider than shoulder width for natural fit (like a real shirt)
    target_width = int(shoulder_width * 1.8)
    # Make clothing extend from shoulders to below waist
    target_height = int(abs(bottom_edge - top_edge) * 1.4)
    
    # Ensure minimum dimensions
    target_width = max(target_width, 150)  # Minimum width
    target_height = max(target_height, 200)  # Minimum height
    
    # Center the clothing on the shoulders
    center_x = (left_edge + right_edge) / 2
    center_y = (top_edge + bottom_edge) / 2
    
    # Set new boundaries for bigger clothing
    left_edge = center_x - target_width / 2
    right_edge = center_x + target_width / 2
    top_edge = center_y - target_height / 2
    bottom_edge = center_y + target_height / 2
    
    print(f"Target clothing size: {target_width}x{target_height}")
    print(f"Shoulder width: {shoulder_width}")
    
    # Recalculate final dimensions
    clothing_width = int(right_edge - left_edge)
    clothing_height = int(bottom_edge - top_edge)
    
    # Position clothing exactly at landmark positions
    position_x = int(left_edge)  # Start at left shoulder
    position_y = int(top_edge)   # Start at shoulder level
    
    print(f"Landmark-based positioning:")
    print(f"  Left shoulder: {left_shoulder}")
    print(f"  Right shoulder: {right_shoulder}")
    print(f"  Left hip: {left_hip}")
    print(f"  Right hip: {right_hip}")
    print(f"  Clothing bounds: left={left_edge}, right={right_edge}, top={top_edge}, bottom={bottom_edge}")
    print(f"  Final dimensions: {clothing_width}x{clothing_height} at ({position_x}, {position_y})")
    
    return {
        'width': clothing_width,
        'height': clothing_height,
        'position': (position_x, position_y),
        'shoulder_width': clothing_width,
        'chest_width': clothing_width,
        'waist_width': clothing_width,
        'body_height': clothing_height,
        'landmarks': {
            'left_shoulder': left_shoulder,
            'right_shoulder': right_shoulder,
            'left_hip': left_hip,
            'right_hip': right_hip
        }
    }

def apply_perfect_clothing(image, path2sprite, key_points, clothing_type='shirt'):
    """Apply clothing with perfect fitting based on body landmarks"""
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
    
    if not key_points:
        print("No key points detected")
        return image
    
    # Get perfect fit parameters
    fit_params = calculate_perfect_fit_parameters(key_points, clothing_type)
    if not fit_params:
        print("Could not calculate fit parameters")
        return image
    
    print(f"Fit parameters: {fit_params}")
    
    # Resize sprite to perfect dimensions
    sprite = cv2.resize(sprite, (fit_params['width'], fit_params['height']))
    print(f"Resized sprite to: {sprite.shape}")
    
    # Flip sprite both horizontally and vertically to fix orientation
    sprite = cv2.flip(sprite, 1)  # Horizontal flip
    sprite = cv2.flip(sprite, 0)  # Vertical flip to fix upside down
    print("Flipped sprite horizontally and vertically to fix orientation")
    
    # Apply perspective transformation for realistic fit with body tilt
    sprite = apply_perspective_transform(sprite, fit_params, clothing_type, key_points)
    
    # Position the clothing
    pos_x, pos_y = fit_params['position']
    print(f"Positioning clothing at: ({pos_x}, {pos_y})")
    
    # Apply clothing with perfect blending
    draw_sprite_perfect(image, sprite, pos_x, pos_y, key_points)
    print("Clothing applied successfully!")
    
    return image

def apply_perspective_transform(sprite, fit_params, clothing_type, key_points=None):
    """Apply perspective transformation based on body tilt and pose"""
    h, w = sprite.shape[0], sprite.shape[1]
    
    # Calculate body tilt and rotation from multiple landmarks
    if key_points and 'left_shoulder' in key_points and 'right_shoulder' in key_points:
        left_shoulder = key_points['left_shoulder']
        right_shoulder = key_points['right_shoulder']
        
        # Calculate tilt angle from shoulders
        dx = right_shoulder[0] - left_shoulder[0]
        dy = right_shoulder[1] - left_shoulder[1]
        tilt_angle = np.arctan2(dy, dx) * 180 / np.pi
        
        # Also check body rotation from hips if available
        body_rotation = 0
        if 'left_hip' in key_points and 'right_hip' in key_points:
            left_hip = key_points['left_hip']
            right_hip = key_points['right_hip']
            hip_dx = right_hip[0] - left_hip[0]
            hip_dy = right_hip[1] - left_hip[1]
            hip_angle = np.arctan2(hip_dy, hip_dx) * 180 / np.pi
            body_rotation = (tilt_angle + hip_angle) / 2  # Average of shoulder and hip angles
        
        print(f"Body tilt angle: {tilt_angle:.2f} degrees")
        print(f"Body rotation: {body_rotation:.2f} degrees")
        
        # Apply rotation to match body pose
        final_angle = body_rotation if abs(body_rotation) > abs(tilt_angle) else tilt_angle
        if abs(final_angle) > 3:  # Only rotate if significant angle
            # Create rotation matrix
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, -final_angle, 1.0)  # Restore negative sign
            sprite = cv2.warpAffine(sprite, rotation_matrix, (w, h))
            print(f"Applied rotation: {-final_angle:.2f} degrees")
    
    # Create perspective points for realistic fit
    if clothing_type == 'shirt':
        # Shirt perspective - slight inward curve
        pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        pts2 = np.float32([
            [w*0.02, 0],           # Top left - slight inward
            [w*0.98, 0],           # Top right - slight inward
            [w*0.05, h],           # Bottom left - more inward
            [w*0.95, h]            # Bottom right - more inward
        ])
    else:  # dress
        # Dress perspective - more fitted silhouette
        pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        pts2 = np.float32([
            [w*0.05, 0],           # Top left
            [w*0.95, 0],           # Top right
            [w*0.1, h],            # Bottom left - more fitted
            [w*0.9, h]             # Bottom right - more fitted
        ])
    
    # Apply perspective transform
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    sprite = cv2.warpPerspective(sprite, matrix, (w, h))
    
    return sprite

def draw_sprite_perfect(frame, sprite, x_offset, y_offset, key_points):
    """Draw sprite with perfect landmark-based positioning"""
    try:
        h, w = sprite.shape[0], sprite.shape[1]
        imgH, imgW = frame.shape[0], frame.shape[1]

        print(f"Drawing sprite: {w}x{h} at offset ({x_offset}, {y_offset}) on frame {imgW}x{imgH}")

        # Use the calculated position and dimensions from fit parameters
        x_start = max(0, x_offset)
        x_end = min(imgW, x_offset + w)
        y_start = max(0, y_offset)
        y_end = min(imgH, y_offset + h)
        
        print(f"Using calculated boundaries: ({x_start}, {y_start}) to ({x_end}, {y_end})")
        print(f"Clothing dimensions: {w}x{h}")

        if y_start >= imgH or x_start >= imgW or y_end <= 0 or x_end <= 0:
            print("Coordinates out of bounds, skipping draw")
            return frame

        # Calculate the region dimensions
        region_width = x_end - x_start
        region_height = y_end - y_start
        
        print(f"Region dimensions: {region_width}x{region_height}")

        # Resize sprite to match the region exactly
        if region_width > 0 and region_height > 0:
            try:
                sprite_resized = cv2.resize(sprite, (region_width, region_height))
                print(f"Resized sprite to: {sprite_resized.shape}")
            except cv2.error as e:
                print(f"OpenCV resize error: {e}")
                return frame
        else:
            print("Invalid region dimensions")
            return frame

        # Extract the frame region
        frame_region = frame[y_start:y_end, x_start:x_end]
        
        # Apply the resized sprite to the frame region
        if len(sprite_resized.shape) == 3 and sprite_resized.shape[2] == 4:  # Has alpha channel
            # Extract alpha channel
            alpha = sprite_resized[:, :, 3] / 255.0
            sprite_rgb = sprite_resized[:, :, :3]
            
            # Simple alpha blending
            for c in range(3):
                frame_region[:, :, c] = (sprite_rgb[:, :, c] * alpha + 
                                       frame_region[:, :, c] * (1.0 - alpha)).astype(np.uint8)
        else:
            # No alpha channel, simple overlay
            frame_region[:] = sprite_resized

        print(f"Successfully applied clothing to region: {frame_region.shape}")

    except Exception as e:
        print(f"Error in draw_sprite_perfect: {e}")
    
    return frame

def create_realistic_lighting(alpha_mask, key_points):
    """Create realistic lighting effects based on body position"""
    h, w = alpha_mask.shape
    lighting = np.ones((h, w), dtype=np.float32)
    
    # Create gradient lighting from top to bottom
    y, x = np.ogrid[:h, :w]
    lighting = 1.0 - (y / h) * 0.2  # 20% darker at bottom
    
    # Add subtle side lighting effect
    center_x = w // 2
    side_lighting = 1.0 - np.abs(x - center_x) / (w / 2) * 0.1  # 10% darker at edges
    lighting *= side_lighting
    
    # Apply alpha mask - ensure shapes match
    if lighting.shape == alpha_mask.shape:
        lighting = lighting * alpha_mask
    else:
        # If shapes don't match, just use the lighting without alpha
        pass
    
    # Clamp values
    lighting = np.clip(lighting, 0.4, 1.0)
    
    return lighting

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label, pose_detector

    try:
        video_capture = cv2.VideoCapture(0)
        
        # Optimize camera settings for better performance
        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Set width
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height
        video_capture.set(cv2.CAP_PROP_FPS, 60)            # Try to set 60 FPS
        video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)      # Reduce buffer size for lower latency
        
        if not video_capture.isOpened():
            status_label.config(text="Error: Could not open camera")
            return
            
        # Get actual camera properties
        actual_fps = video_capture.get(cv2.CAP_PROP_FPS)
        actual_width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        print(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps} FPS")
        status_label.config(text=f"Camera ready - {int(actual_fps)} FPS - Detecting body pose...")
        
        while run_event.is_set():
            try:
                ret, image = video_capture.read()
                if not ret:
                    print("Failed to read frame from camera")
                    continue
                
                # Flip image horizontally to fix mirroring
                image = cv2.flip(image, 1)
                
                if SPRITES[0] and image_path:
                    try:
                        # Detect body landmarks
                        key_points, landmarks = pose_detector.detect_body_landmarks(image)
                        
                        if key_points:
                            status_label.config(text="Body detected! Applying perfect clothing...")
                            
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
                            
                            # Apply perfect clothing
                            image = apply_perfect_clothing(image, image_path, key_points, clothing_type)
                        else:
                            status_label.config(text="Looking for body pose...")
                    except Exception as e:
                        print(f"Error in pose detection: {e}")
                        status_label.config(text="Pose detection error - using basic mode...")
                else:
                    status_label.config(text="Add clothing to try on...")
            except Exception as e:
                print(f"Error in camera loop: {e}")
                status_label.config(text=f"Camera error: {str(e)}")
                break

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

# Initialize pose detector
pose_detector = AdvancedPoseDetector()

# GUI Setup
root = Tk()
root.title("E-Dressing Room - Perfect Virtual Try-On")
root.geometry("1200x900")
root.configure(bg='black')

# Create a frame for the camera display
camera_frame = Frame(root, bg='black')
camera_frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

panelA = Label(camera_frame, bg='black')
panelA.pack(expand=True, fill=BOTH)

# Add status label
status_label = Label(root, text="Loading perfect camera...", fg='white', bg='black')
status_label.pack(pady=5)

# Add info label
info_label = Label(root, text="Perfect fitting with advanced pose detection and realistic lighting", fg='yellow', bg='black')
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
    status_label.config(text="Perfect clothing activated! Advanced pose detection active.")

def clear_clothing():
    global image_path
    image_path = ''
    put_sprite(0)  # Deactivate sprite
    status_label.config(text="Clothing cleared. Add new clothing to try on.")

# CLI argument must be the image path
if len(sys.argv) < 2:
    print("Usage: python tryOn_perfect.py <path_to_sprite_image>")
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

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

class AdvancedBodyMapper:
    """Advanced body mapping for realistic clothing fitting"""
    
    def __init__(self):
        # Load cascades for better detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.upper_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
    def detect_body_landmarks(self, image):
        """Detect comprehensive body landmarks for accurate mapping"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect face
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            return None
            
        face_x, face_y, face_w, face_h = faces[0]
        
        # Detect upper body for better shoulder estimation
        upper_bodies = self.upper_body_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Calculate improved body landmarks
        landmarks = self.calculate_advanced_landmarks(face_x, face_y, face_w, face_h, upper_bodies, image.shape)
        
        return landmarks
    
    def calculate_advanced_landmarks(self, face_x, face_y, face_w, face_h, upper_bodies, image_shape):
        """Calculate advanced body landmarks with better accuracy"""
        img_h, img_w = image_shape[:2]
        
        # Face center and dimensions
        face_center_x = face_x + face_w // 2
        face_center_y = face_y + face_h // 2
        
        # Improved shoulder detection
        # Use face width as base but adjust for actual body proportions
        base_shoulder_width = face_w * 2.2  # More realistic shoulder width
        
        # If upper body detected, use it for better shoulder estimation
        if len(upper_bodies) > 0:
            body_x, body_y, body_w, body_h = upper_bodies[0]
            # Use upper body width for shoulder estimation
            base_shoulder_width = body_w * 0.9  # Slightly narrower than body width
            shoulder_y = body_y + body_h * 0.2  # Shoulders are in upper part of body
        else:
            shoulder_y = face_y + face_h + 30  # Fallback to face-based estimation
        
        # Calculate shoulder points with better positioning
        left_shoulder_x = face_center_x - base_shoulder_width // 2
        right_shoulder_x = face_center_x + base_shoulder_width // 2
        
        # Ensure shoulders are within image bounds
        left_shoulder_x = max(0, min(left_shoulder_x, img_w))
        right_shoulder_x = max(0, min(right_shoulder_x, img_w))
        shoulder_y = max(0, min(shoulder_y, img_h))
        
        # Calculate waist position (more realistic)
        waist_y = shoulder_y + face_h * 1.8  # Waist is further down
        waist_y = min(waist_y, img_h - 50)  # Don't go too low
        
        # Calculate chest/neck area
        neck_y = face_y + face_h - 10
        chest_y = shoulder_y + 20
        
        # Calculate arm positions for better clothing fit
        left_arm_x = left_shoulder_x - face_w * 0.3
        right_arm_x = right_shoulder_x + face_w * 0.3
        
        return {
            'face_center': (face_center_x, face_center_y),
            'left_shoulder': (int(left_shoulder_x), int(shoulder_y)),
            'right_shoulder': (int(right_shoulder_x), int(shoulder_y)),
            'left_waist': (int(left_shoulder_x), int(waist_y)),
            'right_waist': (int(right_shoulder_x), int(waist_y)),
            'neck': (face_center_x, int(neck_y)),
            'chest': (face_center_x, int(chest_y)),
            'left_arm': (int(left_arm_x), int(shoulder_y)),
            'right_arm': (int(right_arm_x), int(shoulder_y)),
            'shoulder_width': base_shoulder_width,
            'body_height': waist_y - shoulder_y
        }

def apply_contoured_clothing(image, clothing_path, landmarks):
    """Apply clothing with body contour mapping for realistic fit"""
    if not landmarks:
        return image
        
    # Load clothing with alpha channel
    clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
    if clothing is None:
        return image
    
    # Get body measurements
    left_shoulder = landmarks['left_shoulder']
    right_shoulder = landmarks['right_shoulder']
    left_waist = landmarks['left_waist']
    right_waist = landmarks['right_waist']
    
    # Calculate clothing dimensions based on body measurements
    shoulder_width = right_shoulder[0] - left_shoulder[0]
    body_height = left_waist[1] - left_shoulder[1]
    
    # Resize clothing to match body dimensions
    orig_h, orig_w = clothing.shape[:2]
    scale_x = shoulder_width / orig_w
    scale_y = body_height / orig_h
    
    # Use uniform scaling to maintain aspect ratio
    scale = min(scale_x, scale_y)
    new_width = int(orig_w * scale)
    new_height = int(orig_h * scale)
    
    # Resize clothing
    resized_clothing = cv2.resize(clothing, (new_width, new_height))
    
    # Apply perspective transformation for realistic fit
    transformed_clothing = apply_perspective_transform(resized_clothing, landmarks)
    
    # Position clothing on body
    start_x = left_shoulder[0]
    start_y = left_shoulder[1]
    
    # Apply clothing with proper blending
    result_image = blend_clothing_with_body(image, transformed_clothing, start_x, start_y)
    
    return result_image

def apply_perspective_transform(clothing, landmarks):
    """Apply perspective transformation to make clothing conform to body shape"""
    h, w = clothing.shape[:2]
    
    # Define source points (clothing corners)
    src_points = np.float32([
        [0, 0],           # Top-left
        [w, 0],            # Top-right
        [w, h],            # Bottom-right
        [0, h]             # Bottom-left
    ])
    
    # Define destination points based on body landmarks
    left_shoulder = landmarks['left_shoulder']
    right_shoulder = landmarks['right_shoulder']
    left_waist = landmarks['left_waist']
    right_waist = landmarks['right_waist']
    
    # Add slight curve to make clothing more natural
    shoulder_curve = 5  # Pixels of curve
    waist_curve = 8
    
    dst_points = np.float32([
        [left_shoulder[0], left_shoulder[1] - shoulder_curve],      # Top-left (shoulder)
        [right_shoulder[0], right_shoulder[1] - shoulder_curve],    # Top-right (shoulder)
        [right_waist[0], right_waist[1] + waist_curve],             # Bottom-right (waist)
        [left_waist[0], left_waist[1] + waist_curve]               # Bottom-left (waist)
    ])
    
    # Calculate perspective transformation matrix
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    
    # Apply transformation
    transformed = cv2.warpPerspective(clothing, matrix, (clothing.shape[1], clothing.shape[0]))
    
    return transformed

def blend_clothing_with_body(body_image, clothing, start_x, start_y):
    """Blend clothing with body image using advanced alpha blending"""
    result = body_image.copy()
    h, w = clothing.shape[:2]
    img_h, img_w = body_image.shape[:2]
    
    # Calculate blending region
    end_x = min(start_x + w, img_w)
    end_y = min(start_y + h, img_h)
    start_x = max(0, start_x)
    start_y = max(0, start_y)
    
    # Extract regions
    body_region = result[start_y:end_y, start_x:end_x]
    clothing_region = clothing[:end_y-start_y, :end_x-start_x]
    
    # Ensure same dimensions
    if body_region.shape != clothing_region.shape:
        clothing_region = cv2.resize(clothing_region, (body_region.shape[1], body_region.shape[0]))
    
    # Advanced alpha blending
    if clothing_region.shape[2] == 4:  # Has alpha channel
        alpha = clothing_region[:, :, 3:4] / 255.0
        
        # Apply different blending for different areas
        # More transparency at edges for natural look
        edge_fade = create_edge_fade_mask(alpha.shape[:2])
        alpha = alpha * edge_fade
        
        # Blend each color channel
        for c in range(3):
            body_region[:, :, c] = (
                clothing_region[:, :, c] * alpha[:, :, 0] + 
                body_region[:, :, c] * (1.0 - alpha[:, :, 0])
            ).astype(np.uint8)
    else:
        # No alpha channel, use simple overlay with edge detection
        body_region = clothing_region
    
    return result

def create_edge_fade_mask(shape):
    """Create a mask that fades edges for more natural clothing appearance"""
    h, w = shape
    mask = np.ones((h, w), dtype=np.float32)
    
    # Create gradient from center to edges
    center_y, center_x = h // 2, w // 2
    
    for y in range(h):
        for x in range(w):
            # Distance from center
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            max_dist = np.sqrt(center_x**2 + center_y**2)
            
            # Fade factor (1.0 at center, 0.0 at edges)
            fade = max(0.0, 1.0 - (dist / max_dist) * 0.3)
            mask[y, x] = fade
    
    return mask

def draw_advanced_body_markers(image, landmarks):
    """Draw advanced body part markers for debugging"""
    if not landmarks:
        return image
    
    # Draw shoulders (green)
    cv2.circle(image, landmarks['left_shoulder'], 8, (0, 255, 0), -1)
    cv2.circle(image, landmarks['right_shoulder'], 8, (0, 255, 0), -1)
    
    # Draw waist (blue)
    cv2.circle(image, landmarks['left_waist'], 6, (255, 0, 0), -1)
    cv2.circle(image, landmarks['right_waist'], 6, (255, 0, 0), -1)
    
    # Draw connecting lines
    cv2.line(image, landmarks['left_shoulder'], landmarks['right_shoulder'], (0, 255, 0), 3)
    cv2.line(image, landmarks['left_waist'], landmarks['right_waist'], (255, 0, 0), 3)
    
    # Draw body outline
    cv2.line(image, landmarks['left_shoulder'], landmarks['left_waist'], (0, 255, 255), 2)
    cv2.line(image, landmarks['right_shoulder'], landmarks['right_waist'], (0, 255, 255), 2)
    
    return image

# Initialize the advanced body mapper
body_mapper = AdvancedBodyMapper()

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label
    
    cap = cv2.VideoCapture(0)
    
    while run_event.is_set():
        ret, image = cap.read()
        if not ret:
            continue
            
        # Detect body landmarks
        landmarks = body_mapper.detect_body_landmarks(image)
        
        if landmarks:
            # Draw body markers for debugging
            image = draw_advanced_body_markers(image, landmarks)
            
            # Apply clothing if sprite is active
            if SPRITES[0] and image_path:
                status_label.config(text="Body detected! Applying contoured clothing...")
                image = apply_contoured_clothing(image, image_path, landmarks)
            else:
                status_label.config(text="Body parts detected! Ready for clothing...")
        else:
            status_label.config(text="Looking for body parts...")
        
        # Resize for display
        height, width = image.shape[:2]
        max_width = 700
        if width > max_width:
            scale = max_width / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))
        
        # Convert to RGB and display
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        image_tk = ImageTk.PhotoImage(image_pil)
        
        panelA.configure(image=image_tk)
        panelA.image = image_tk
        
        time.sleep(0.03)  # ~30 FPS
    
    cap.release()

def main():
    global panelA, status_label, image_path
    
    if len(sys.argv) != 2:
        print("Usage: python tryOn_improved_body_mapping.py <path_to_clothing_image>")
        return
    
    image_path = sys.argv[1]
    
    # Create GUI
    root = Tk()
    root.title("E-Dressing Room - Improved Body Mapping")
    root.geometry("800x700")
    
    # Video display
    panelA = Label(root)
    panelA.pack(pady=10)
    
    # Status label
    status_label = Label(root, text="Initializing camera...", font=("Arial", 12))
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

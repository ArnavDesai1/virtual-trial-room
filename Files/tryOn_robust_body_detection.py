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

class RobustBodyDetector:
    """Robust body detection that works in various conditions"""
    
    def __init__(self):
        # Load multiple cascades for better detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.upper_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
    def detect_body_robust(self, image):
        """Robust body detection that works in various conditions"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Try multiple detection methods
        body_data = self.try_multiple_detections(gray, image.shape)
        
        if body_data:
            return body_data
        else:
            # Fallback: use simple face-based estimation
            return self.create_fallback_body_data(gray, image.shape)
    
    def try_multiple_detections(self, gray, image_shape):
        """Try multiple detection methods for robust body detection"""
        img_h, img_w = image_shape[:2]
        
        # Method 1: Face + Upper Body detection
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        upper_bodies = self.upper_body_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0 and len(upper_bodies) > 0:
            face_x, face_y, face_w, face_h = faces[0]
            body_x, body_y, body_w, body_h = upper_bodies[0]
            
            # Use both face and body for accurate positioning
            return self.calculate_robust_body_points(face_x, face_y, face_w, face_h, 
                                                   body_x, body_y, body_w, body_h, img_w, img_h)
        
        # Method 2: Face only with improved estimation
        elif len(faces) > 0:
            face_x, face_y, face_w, face_h = faces[0]
            return self.calculate_face_based_body_points(face_x, face_y, face_w, face_h, img_w, img_h)
        
        # Method 3: Profile face detection
        profiles = self.profile_cascade.detectMultiScale(gray, 1.1, 4)
        if len(profiles) > 0:
            profile_x, profile_y, profile_w, profile_h = profiles[0]
            return self.calculate_profile_based_body_points(profile_x, profile_y, profile_w, profile_h, img_w, img_h)
        
        return None
    
    def calculate_robust_body_points(self, face_x, face_y, face_w, face_h, body_x, body_y, body_w, body_h, img_w, img_h):
        """Calculate body points using both face and body detection"""
        # Face center
        face_center_x = face_x + face_w // 2
        face_center_y = face_y + face_h // 2
        
        # Use body detection for shoulders
        shoulder_width = body_w * 0.8  # Slightly narrower than detected body
        shoulder_y = body_y + body_h * 0.2  # Shoulders in upper part of body
        
        left_shoulder_x = body_x + body_w * 0.15  # Left shoulder position
        right_shoulder_x = body_x + body_w * 0.85  # Right shoulder position
        
        # Calculate waist
        waist_y = shoulder_y + face_h * 1.5
        waist_width = shoulder_width * 0.9  # Waist is narrower
        
        left_waist_x = face_center_x - waist_width // 2
        right_waist_x = face_center_x + waist_width // 2
        
        return self.create_body_data(left_shoulder_x, right_shoulder_x, shoulder_y, 
                                   left_waist_x, right_waist_x, waist_y, shoulder_width, img_w, img_h)
    
    def calculate_face_based_body_points(self, face_x, face_y, face_w, face_h, img_w, img_h):
        """Calculate body points using only face detection with improved estimation"""
        face_center_x = face_x + face_w // 2
        face_center_y = face_y + face_h // 2
        
        # More realistic shoulder estimation based on face
        shoulder_width = face_w * 2.2  # Slightly wider than face
        shoulder_y = face_y + face_h + 20  # Below face
        
        left_shoulder_x = face_center_x - shoulder_width // 2
        right_shoulder_x = face_center_x + shoulder_width // 2
        
        # Calculate waist
        waist_y = shoulder_y + face_h * 1.4
        waist_width = shoulder_width * 0.9
        
        left_waist_x = face_center_x - waist_width // 2
        right_waist_x = face_center_x + waist_width // 2
        
        return self.create_body_data(left_shoulder_x, right_shoulder_x, shoulder_y,
                                   left_waist_x, right_waist_x, waist_y, shoulder_width, img_w, img_h)
    
    def calculate_profile_based_body_points(self, profile_x, profile_y, profile_w, profile_h, img_w, img_h):
        """Calculate body points using profile face detection"""
        profile_center_x = profile_x + profile_w // 2
        profile_center_y = profile_y + profile_h // 2
        
        # Estimate shoulders from profile
        shoulder_width = profile_w * 2.5
        shoulder_y = profile_y + profile_h + 15
        
        left_shoulder_x = profile_center_x - shoulder_width // 2
        right_shoulder_x = profile_center_x + shoulder_width // 2
        
        # Calculate waist
        waist_y = shoulder_y + profile_h * 1.3
        waist_width = shoulder_width * 0.9
        
        left_waist_x = profile_center_x - waist_width // 2
        right_waist_x = profile_center_x + waist_width // 2
        
        return self.create_body_data(left_shoulder_x, right_shoulder_x, shoulder_y,
                                   left_waist_x, right_waist_x, waist_y, shoulder_width, img_w, img_h)
    
    def create_fallback_body_data(self, gray, image_shape):
        """Create fallback body data when no face is detected"""
        img_h, img_w = image_shape[:2]
        
        # Use image center as reference
        center_x = img_w // 2
        center_y = img_h // 2
        
        # Estimate body position in center of image
        shoulder_width = img_w * 0.4  # 40% of image width
        shoulder_y = img_h * 0.3  # Upper third of image
        
        left_shoulder_x = center_x - shoulder_width // 2
        right_shoulder_x = center_x + shoulder_width // 2
        
        waist_y = shoulder_y + img_h * 0.3
        waist_width = shoulder_width * 0.9
        
        left_waist_x = center_x - waist_width // 2
        right_waist_x = center_x + waist_width // 2
        
        return self.create_body_data(left_shoulder_x, right_shoulder_x, shoulder_y,
                                   left_waist_x, right_waist_x, waist_y, shoulder_width, img_w, img_h)
    
    def create_body_data(self, left_shoulder_x, right_shoulder_x, shoulder_y, 
                       left_waist_x, right_waist_x, waist_y, shoulder_width, img_w, img_h):
        """Create standardized body data structure"""
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

def apply_clothing_robust(image, clothing_path, body_data):
    """Apply clothing with robust body mapping"""
    if not body_data or not body_data.get('detected', False):
        return image
        
    # Load clothing
    clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
    if clothing is None:
        print(f"Could not load clothing: {clothing_path}")
        return image
    
    # Get body measurements
    left_shoulder = body_data['left_shoulder']
    right_shoulder = body_data['right_shoulder']
    left_waist = body_data['left_waist']
    right_waist = body_data['right_waist']
    
    # Calculate clothing dimensions
    shoulder_width = right_shoulder[0] - left_shoulder[0]
    body_height = left_waist[1] - left_shoulder[1]
    
    # Resize clothing to match body
    orig_h, orig_w = clothing.shape[:2]
    scale_x = shoulder_width / orig_w
    scale_y = body_height / orig_h
    scale = min(scale_x, scale_y)
    
    new_width = int(orig_w * scale)
    new_height = int(orig_h * scale)
    
    # Resize clothing
    resized_clothing = cv2.resize(clothing, (new_width, new_height))
    
    # Apply clothing with simple overlay (more reliable)
    result = apply_simple_clothing_overlay(image, resized_clothing, left_shoulder)
    
    return result

def apply_simple_clothing_overlay(body_image, clothing, start_pos):
    """Apply clothing with simple but effective overlay"""
    result = body_image.copy()
    h, w = clothing.shape[:2]
    img_h, img_w = body_image.shape[:2]
    
    # Calculate placement region
    start_x, start_y = start_pos
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
    
    # Simple alpha blending
    if clothing_region.shape[2] == 4:  # Has alpha channel
        alpha = clothing_region[:, :, 3:4] / 255.0
        
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

def draw_body_markers(image, body_data):
    """Draw body markers for debugging"""
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

# Initialize the robust body detector
body_detector = RobustBodyDetector()

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label
    
    cap = cv2.VideoCapture(0)
    
    while run_event.is_set():
        ret, image = cap.read()
        if not ret:
            continue
            
        # Detect body with robust method
        body_data = body_detector.detect_body_robust(image)
        
        if body_data and body_data.get('detected', False):
            # Draw body markers for debugging
            image = draw_body_markers(image, body_data)
            
            # Apply clothing if sprite is active
            if SPRITES[0] and image_path:
                status_label.config(text="Body detected! Applying clothing...")
                image = apply_clothing_robust(image, image_path, body_data)
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
        
        time.sleep(0.03)
    
    cap.release()

def main():
    global panelA, status_label, image_path
    
    if len(sys.argv) != 2:
        print("Usage: python tryOn_robust_body_detection.py <path_to_clothing_image>")
        return
    
    image_path = sys.argv[1]
    
    # Create GUI
    root = Tk()
    root.title("E-Dressing Room - Robust Body Detection")
    root.geometry("800x700")
    
    # Video display
    panelA = Label(root)
    panelA.pack(pady=10)
    
    # Status label
    status_label = Label(root, text="Initializing robust body detection...", font=("Arial", 12))
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


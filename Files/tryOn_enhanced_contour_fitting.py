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

class EnhancedContourFitter:
    """Enhanced contour fitting for realistic clothing appearance"""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.upper_body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        
    def detect_body_contour(self, image):
        """Detect body contour for precise clothing fitting"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect face
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        if len(faces) == 0:
            return None
            
        face_x, face_y, face_w, face_h = faces[0]
        
        # Detect upper body
        upper_bodies = self.upper_body_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Calculate body contour points
        contour_points = self.calculate_body_contour_points(face_x, face_y, face_w, face_h, upper_bodies, image.shape)
        
        return contour_points
    
    def calculate_body_contour_points(self, face_x, face_y, face_w, face_h, upper_bodies, image_shape):
        """Calculate detailed body contour points for realistic fitting"""
        img_h, img_w = image_shape[:2]
        
        # Face center
        face_center_x = face_x + face_w // 2
        face_center_y = face_y + face_h // 2
        
        # Improved shoulder detection
        if len(upper_bodies) > 0:
            body_x, body_y, body_w, body_h = upper_bodies[0]
            # Use actual body detection for shoulders
            shoulder_width = body_w * 0.85  # Slightly narrower than body
            shoulder_y = body_y + body_h * 0.15  # Shoulders in upper body
            left_shoulder_x = body_x + body_w * 0.1  # Left edge of body
            right_shoulder_x = body_x + body_w * 0.9  # Right edge of body
        else:
            # Fallback to face-based estimation
            shoulder_width = face_w * 2.0
            shoulder_y = face_y + face_h + 25
            left_shoulder_x = face_center_x - shoulder_width // 2
            right_shoulder_x = face_center_x + shoulder_width // 2
        
        # Calculate waist with slight inward curve (more realistic)
        waist_y = shoulder_y + face_h * 1.6
        waist_width = shoulder_width * 0.9  # Waist is narrower than shoulders
        
        left_waist_x = face_center_x - waist_width // 2
        right_waist_x = face_center_x + waist_width // 2
        
        # Calculate chest area (between shoulders and waist)
        chest_y = shoulder_y + (waist_y - shoulder_y) * 0.3
        chest_width = shoulder_width * 0.95
        
        left_chest_x = face_center_x - chest_width // 2
        right_chest_x = face_center_x + chest_width // 2
        
        # Create contour points for realistic body shape
        contour_points = {
            # Shoulder line
            'left_shoulder': (int(left_shoulder_x), int(shoulder_y)),
            'right_shoulder': (int(right_shoulder_x), int(shoulder_y)),
            
            # Chest line (slightly curved)
            'left_chest': (int(left_chest_x), int(chest_y)),
            'right_chest': (int(right_chest_x), int(chest_y)),
            
            # Waist line (narrower, more curved)
            'left_waist': (int(left_waist_x), int(waist_y)),
            'right_waist': (int(right_waist_x), int(waist_y)),
            
            # Side contours for 3D effect
            'left_side_top': (int(left_shoulder_x), int(chest_y)),
            'left_side_bottom': (int(left_waist_x), int(waist_y)),
            'right_side_top': (int(right_shoulder_x), int(chest_y)),
            'right_side_bottom': (int(right_waist_x), int(waist_y)),
            
            # Measurements
            'shoulder_width': shoulder_width,
            'waist_width': waist_width,
            'body_height': waist_y - shoulder_y,
            'face_center': (face_center_x, face_center_y)
        }
        
        return contour_points

def apply_contoured_clothing_enhanced(image, clothing_path, contour_points):
    """Apply clothing with enhanced contour fitting"""
    if not contour_points:
        return image
        
    # Load clothing
    clothing = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
    if clothing is None:
        return image
    
    # Get key points
    left_shoulder = contour_points['left_shoulder']
    right_shoulder = contour_points['right_shoulder']
    left_waist = contour_points['left_waist']
    right_waist = contour_points['right_waist']
    
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
    
    # Apply advanced perspective transformation
    transformed_clothing = apply_advanced_perspective(resized_clothing, contour_points)
    
    # Apply with body-aware blending
    result = apply_body_aware_blending(image, transformed_clothing, left_shoulder)
    
    return result

def apply_advanced_perspective(clothing, contour_points):
    """Apply advanced perspective transformation for realistic body fitting"""
    h, w = clothing.shape[:2]
    
    # Source points (clothing rectangle)
    src_points = np.float32([
        [0, 0],           # Top-left
        [w, 0],           # Top-right
        [w, h],           # Bottom-right
        [0, h]            # Bottom-left
    ])
    
    # Destination points based on body contour
    left_shoulder = contour_points['left_shoulder']
    right_shoulder = contour_points['right_shoulder']
    left_waist = contour_points['left_waist']
    right_waist = contour_points['right_waist']
    
    # Add realistic curves and perspective
    shoulder_curve = 8  # Shoulder curve
    waist_curve = 12    # Waist curve (more pronounced)
    
    dst_points = np.float32([
        [left_shoulder[0], left_shoulder[1] - shoulder_curve],      # Top-left
        [right_shoulder[0], right_shoulder[1] - shoulder_curve],   # Top-right
        [right_waist[0], right_waist[1] + waist_curve],           # Bottom-right
        [left_waist[0], left_waist[1] + waist_curve]              # Bottom-left
    ])
    
    # Calculate perspective matrix
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    
    # Apply transformation
    transformed = cv2.warpPerspective(clothing, matrix, (w, h))
    
    return transformed

def apply_body_aware_blending(body_image, clothing, start_pos):
    """Apply clothing with body-aware blending for natural appearance"""
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
    
    # Advanced blending with edge detection
    if clothing_region.shape[2] == 4:  # Has alpha channel
        alpha = clothing_region[:, :, 3:4] / 255.0
        
        # Create body-aware blending mask
        blend_mask = create_body_aware_mask(alpha.shape[:2], body_region)
        alpha = alpha * blend_mask
        
        # Blend with enhanced realism
        for c in range(3):
            body_region[:, :, c] = (
                clothing_region[:, :, c] * alpha[:, :, 0] + 
                body_region[:, :, c] * (1.0 - alpha[:, :, 0])
            ).astype(np.uint8)
    else:
        # Apply edge-aware blending even without alpha
        edge_mask = detect_clothing_edges(clothing_region)
        for c in range(3):
            body_region[:, :, c] = (
                clothing_region[:, :, c] * edge_mask + 
                body_region[:, :, c] * (1.0 - edge_mask)
            ).astype(np.uint8)
    
    return result

def create_body_aware_mask(shape, body_region):
    """Create a mask that considers body contours for natural blending"""
    h, w = shape
    mask = np.ones((h, w), dtype=np.float32)
    
    # Create gradient from center outward
    center_y, center_x = h // 2, w // 2
    
    for y in range(h):
        for x in range(w):
            # Distance from center
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            max_dist = np.sqrt(center_x**2 + center_y**2)
            
            # Create natural fade
            fade = max(0.3, 1.0 - (dist / max_dist) * 0.7)
            mask[y, x] = fade
    
    return mask

def detect_clothing_edges(clothing_region):
    """Detect clothing edges for better blending"""
    gray = cv2.cvtColor(clothing_region, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # Dilate edges slightly
    kernel = np.ones((3,3), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    # Convert to float and normalize
    edge_mask = edges.astype(np.float32) / 255.0
    
    # Invert so edges have lower values (more transparent)
    edge_mask = 1.0 - edge_mask
    
    return edge_mask

def draw_contour_debug_markers(image, contour_points):
    """Draw detailed contour markers for debugging"""
    if not contour_points:
        return image
    
    # Draw shoulder points (green)
    cv2.circle(image, contour_points['left_shoulder'], 8, (0, 255, 0), -1)
    cv2.circle(image, contour_points['right_shoulder'], 8, (0, 255, 0), -1)
    
    # Draw waist points (blue)
    cv2.circle(image, contour_points['left_waist'], 6, (255, 0, 0), -1)
    cv2.circle(image, contour_points['right_waist'], 6, (255, 0, 0), -1)
    
    # Draw chest points (yellow)
    cv2.circle(image, contour_points['left_chest'], 5, (0, 255, 255), -1)
    cv2.circle(image, contour_points['right_chest'], 5, (0, 255, 255), -1)
    
    # Draw connecting lines
    cv2.line(image, contour_points['left_shoulder'], contour_points['right_shoulder'], (0, 255, 0), 3)
    cv2.line(image, contour_points['left_waist'], contour_points['right_waist'], (255, 0, 0), 3)
    cv2.line(image, contour_points['left_chest'], contour_points['right_chest'], (0, 255, 255), 2)
    
    # Draw body outline
    cv2.line(image, contour_points['left_shoulder'], contour_points['left_waist'], (0, 255, 255), 2)
    cv2.line(image, contour_points['right_shoulder'], contour_points['right_waist'], (0, 255, 255), 2)
    
    return image

# Initialize the enhanced contour fitter
contour_fitter = EnhancedContourFitter()

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label
    
    cap = cv2.VideoCapture(0)
    
    while run_event.is_set():
        ret, image = cap.read()
        if not ret:
            continue
            
        # Detect body contour
        contour_points = contour_fitter.detect_body_contour(image)
        
        if contour_points:
            # Draw debug markers
            image = draw_contour_debug_markers(image, contour_points)
            
            # Apply enhanced clothing if active
            if SPRITES[0] and image_path:
                status_label.config(text="Body contour detected! Applying enhanced clothing...")
                image = apply_contoured_clothing_enhanced(image, image_path, contour_points)
            else:
                status_label.config(text="Body contour detected! Ready for clothing...")
        else:
            status_label.config(text="Looking for body contour...")
        
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
        print("Usage: python tryOn_enhanced_contour_fitting.py <path_to_clothing_image>")
        return
    
    image_path = sys.argv[1]
    
    # Create GUI
    root = Tk()
    root.title("E-Dressing Room - Enhanced Contour Fitting")
    root.geometry("800x700")
    
    # Video display
    panelA = Label(root)
    panelA.pack(pady=10)
    
    # Status label
    status_label = Label(root, text="Initializing enhanced contour detection...", font=("Arial", 12))
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

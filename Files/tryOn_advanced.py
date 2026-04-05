from tkinter import *
from PIL import Image, ImageTk
import cv2, threading, os, time, sys, math
import numpy as np
from threading import Thread
from pose_estimator import SimplePoseEstimator

# Globals
SPRITES = [0, 0, 0, 0, 0, 0]
image_path = ''
pose_estimator = SimplePoseEstimator()

def put_sprite(num):
    global SPRITES
    SPRITES = [0] * len(SPRITES)
    SPRITES[num] = 1

def create_realistic_clothing_mask(sprite, fit_params, clothing_type='shirt'):
    """Create a realistic clothing mask based on fit parameters"""
    h, w = sprite.shape[0], sprite.shape[1]
    mask = np.zeros((h, w), dtype=np.uint8)
    
    if clothing_type == 'shirt':
        # Create shirt shape with proper fit
        shoulder_width = int(w * fit_params['shoulder_fit'])
        waist_width = int(w * fit_params['waist_fit'])
        
        # Create trapezoid shape for shirt
        top_x = (w - shoulder_width) // 2
        bottom_x = (w - waist_width) // 2
        
        pts = np.array([
            [top_x, 0],
            [top_x + shoulder_width, 0],
            [bottom_x + waist_width, h],
            [bottom_x, h]
        ], np.int32)
        
        cv2.fillPoly(mask, [pts], 255)
        
    elif clothing_type == 'dress':
        # Create dress shape with proper fit
        shoulder_width = int(w * fit_params['shoulder_fit'])
        waist_width = int(w * fit_params['waist_fit'])
        
        # Create more fitted dress shape
        top_x = (w - shoulder_width) // 2
        waist_x = (w - waist_width) // 2
        bottom_x = (w - int(waist_width * 0.8)) // 2  # Even narrower at bottom
        
        # Create hourglass shape
        waist_y = int(h * 0.6)  # Waist at 60% of height
        
        pts = np.array([
            [top_x, 0],
            [top_x + shoulder_width, 0],
            [waist_x + waist_width, waist_y],
            [bottom_x + int(waist_width * 0.8), h],
            [bottom_x, h],
            [waist_x, waist_y]
        ], np.int32)
        
        cv2.fillPoly(mask, [pts], 255)
    
    return mask

def apply_advanced_clothing(image, path2sprite, key_points, measurements, clothing_type='shirt'):
    """Apply clothing with advanced fitting and realistic deformation"""
    sprite = cv2.imread(path2sprite, -1)
    if sprite is None:
        print(f"Could not load sprite: {path2sprite}")
        return image
    
    # Get fit parameters
    fit_params = pose_estimator.get_clothing_fit_parameters(measurements, clothing_type)
    if not fit_params:
        return image
    
    # Calculate target dimensions
    target_width = fit_params['width']
    target_height = fit_params['height']
    
    # Resize sprite
    sprite = cv2.resize(sprite, (target_width, target_height))
    
    # Create realistic mask
    mask = create_realistic_clothing_mask(sprite, fit_params, clothing_type)
    
    # Apply advanced perspective transformation
    h, w = sprite.shape[0], sprite.shape[1]
    
    # Create 3D perspective effect
    if clothing_type == 'shirt':
        # Shirt perspective - slight inward curve for realistic fit
        pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        pts2 = np.float32([
            [w*0.05, 0],           # Top left
            [w*0.95, 0],           # Top right
            [w*0.1, h],            # Bottom left
            [w*0.9, h]             # Bottom right
        ])
    else:  # dress
        # Dress perspective - more fitted silhouette
        pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        pts2 = np.float32([
            [w*0.1, 0],            # Top left
            [w*0.9, 0],            # Top right
            [w*0.15, h],           # Bottom left
            [w*0.85, h]            # Bottom right
        ])
    
    # Apply perspective transform
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    sprite = cv2.warpPerspective(sprite, matrix, (w, h))
    mask = cv2.warpPerspective(mask, matrix, (w, h))
    
    # Position the sprite
    position = fit_params['position']
    sprite_x = max(0, position[0] - target_width // 2)
    sprite_y = max(0, position[1] - target_height // 2)
    
    # Apply advanced blending
    draw_sprite_with_advanced_blending(image, sprite, mask, sprite_x, sprite_y, clothing_type)
    
    return image

def draw_sprite_with_advanced_blending(frame, sprite, mask, x_offset, y_offset, clothing_type='shirt'):
    """Advanced blending with realistic lighting and shadows"""
    h, w = sprite.shape[0], sprite.shape[1]
    imgH, imgW = frame.shape[0], frame.shape[1]

    # Ensure sprite has alpha channel
    if len(sprite.shape) == 2 or sprite.shape[2] != 4:
        if len(sprite.shape) == 2:
            # Convert grayscale to BGR first
            sprite = cv2.cvtColor(sprite, cv2.COLOR_GRAY2BGR)
        alpha = np.ones((h, w, 1), dtype=sprite.dtype) * 255
        sprite = np.concatenate([sprite, alpha], axis=2)

    # Clamp coordinates
    y_start = max(0, y_offset)
    y_end = min(imgH, y_offset + h)
    x_start = max(0, x_offset)
    x_end = min(imgW, x_offset + w)

    if y_start >= imgH or x_start >= imgW or y_end <= 0 or x_end <= 0:
        return frame

    # Calculate sprite regions
    sprite_y_start = max(0, -y_offset)
    sprite_y_end = sprite_y_start + (y_end - y_start)
    sprite_x_start = max(0, -x_offset)
    sprite_x_end = sprite_x_start + (x_end - x_start)

    if sprite_y_start >= h or sprite_x_start >= w or sprite_y_end <= 0 or sprite_x_end <= 0:
        return frame

    # Extract regions
    frame_region = frame[y_start:y_end, x_start:x_end]
    sprite_region = sprite[sprite_y_start:sprite_y_end, sprite_x_start:sprite_x_end]
    mask_region = mask[sprite_y_start:sprite_y_end, sprite_x_start:sprite_x_end]

    # Ensure all regions have the same shape
    if frame_region.shape != sprite_region.shape:
        sprite_region = cv2.resize(sprite_region, (frame_region.shape[1], frame_region.shape[0]))
        mask_region = cv2.resize(mask_region, (frame_region.shape[1], frame_region.shape[0]))

    # Create realistic lighting effect
    lighting_mask = create_lighting_effect(mask_region, clothing_type)
    
    # Apply advanced blending
    if len(sprite_region.shape) == 3 and sprite_region.shape[2] == 4:  # Has alpha channel
        # Combine alpha, mask, and lighting
        combined_alpha = (sprite_region[:, :, 3:4] / 255.0) * (mask_region[:, :, np.newaxis] / 255.0) * lighting_mask[:, :, np.newaxis]
        
        # Apply color blending with lighting
        for c in range(3):
            # Add subtle color variation based on lighting
            lit_sprite = sprite_region[:, :, c] * lighting_mask
            frame_region[:, :, c] = (lit_sprite * combined_alpha[:, :, 0] + 
                                   frame_region[:, :, c] * (1.0 - combined_alpha[:, :, 0])).astype(np.uint8)
    else:
        # No alpha channel, use mask and lighting
        mask_3d = mask_region[:, :, np.newaxis] / 255.0
        lighting_3d = lighting_mask[:, :, np.newaxis]
        
        for c in range(3):
            lit_sprite = sprite_region[:, :, c] * lighting_mask
            frame_region[:, :, c] = (lit_sprite * mask_3d[:, :, 0] + 
                                   frame_region[:, :, c] * (1.0 - mask_3d[:, :, 0])).astype(np.uint8)

    return frame

def create_lighting_effect(mask, clothing_type='shirt'):
    """Create realistic lighting effect for clothing"""
    h, w = mask.shape
    lighting = np.ones((h, w), dtype=np.float32)
    
    # Create gradient lighting effect
    if clothing_type == 'shirt':
        # Shirt lighting - lighter in center, darker at edges
        center_x, center_y = w // 2, h // 2
        y, x = np.ogrid[:h, :w]
        
        # Distance from center
        dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        
        # Create radial gradient
        lighting = 1.0 - (dist / max_dist) * 0.3  # 30% darker at edges
        
    else:  # dress
        # Dress lighting - vertical gradient
        y, x = np.ogrid[:h, :w]
        lighting = 1.0 - (y / h) * 0.2  # 20% darker at bottom
    
    # Apply mask
    lighting = lighting * (mask / 255.0)
    
    # Clamp values
    lighting = np.clip(lighting, 0.3, 1.0)
    
    # Ensure lighting is 2D
    if len(lighting.shape) == 3:
        lighting = lighting[:, :, 0]
    
    return lighting

def cvloop(run_event):
    global panelA, SPRITES, image_path, status_label

    try:
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            status_label.config(text="Error: Could not open camera")
            return
            
        status_label.config(text="Advanced camera ready - Detecting pose...")
        
        while run_event.is_set():
            ret, image = video_capture.read()
            if not ret:
                continue
            
            if SPRITES[0] and image_path:
                # Detect pose and body measurements
                key_points = pose_estimator.detect_body_pose(image)
                
                if key_points:
                    measurements = pose_estimator.calculate_body_measurements(key_points)
                    
                    if measurements:
                        status_label.config(text="Pose detected! Applying advanced clothing...")
                        
                        # Determine clothing type
                        clothing_type = 'shirt'
                        if 'dress' in image_path.lower():
                            clothing_type = 'dress'
                        elif 'top' in image_path.lower():
                            clothing_type = 'shirt'
                        
                        # Draw pose key points for debugging
                        for point_name, (px, py) in key_points.items():
                            cv2.circle(image, (px, py), 3, (0, 255, 0), -1)
                            cv2.putText(image, point_name, (px + 5, py - 5), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                        
                        # Apply advanced clothing
                        image = apply_advanced_clothing(image, image_path, key_points, measurements, clothing_type)
                    else:
                        status_label.config(text="Calculating body measurements...")
                else:
                    status_label.config(text="Looking for pose...")
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

# GUI Setup
root = Tk()
root.title("E-Dressing Room - Advanced Virtual Try-On")
root.geometry("1000x800")
root.configure(bg='black')

# Create a frame for the camera display
camera_frame = Frame(root, bg='black')
camera_frame.pack(expand=True, fill=BOTH, padx=10, pady=10)

panelA = Label(camera_frame, bg='black')
panelA.pack(expand=True, fill=BOTH)

# Add status label
status_label = Label(root, text="Loading advanced camera...", fg='white', bg='black')
status_label.pack(pady=5)

# Add info label
info_label = Label(root, text="Advanced pose detection with realistic clothing fitting", fg='yellow', bg='black')
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
    status_label.config(text="Advanced clothing activated! Pose detection active.")

def clear_clothing():
    global image_path
    image_path = ''
    put_sprite(0)  # Deactivate sprite
    status_label.config(text="Clothing cleared. Add new clothing to try on.")

# CLI argument must be the image path
if len(sys.argv) < 2:
    print("Usage: python tryOn_advanced.py <path_to_sprite_image>")
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


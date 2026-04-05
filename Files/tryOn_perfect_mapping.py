import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
import sys
import os
from PIL import Image, ImageTk

class PerfectShirtMapping:
    def __init__(self, image_path):
        self.image_path = image_path
        self.root = tk.Tk()
        self.root.title("E-Dressing Room - Perfect Shirt Mapping")
        self.root.geometry("800x600")
        
        # Load the image
        self.original_image = cv2.imread(image_path)
        if self.original_image is None:
            print(f"Error: Could not load image {image_path}")
            return
            
        self.current_image = self.original_image.copy()
        
        # Load clothing
        self.clothing_path = image_path
        self.clothing_image = cv2.imread(self.clothing_path, cv2.IMREAD_UNCHANGED)
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.setup_ui()
        self.detect_existing_shirt_and_map()
        
    def setup_ui(self):
        # Image display
        self.image_label = tk.Label(self.root)
        self.image_label.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(self.root, text="Detecting existing shirt...", font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.try_on_btn = tk.Button(button_frame, text="Try it ON", bg="green", fg="white", 
                                   command=self.apply_perfect_mapping, font=("Arial", 12))
        self.try_on_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(button_frame, text="Clear Clothing", bg="orange", fg="white", 
                                 command=self.clear_clothing, font=("Arial", 12))
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.close_btn = tk.Button(button_frame, text="Close", bg="red", fg="white", 
                                 command=self.root.quit, font=("Arial", 12))
        self.close_btn.pack(side=tk.LEFT, padx=5)
        
    def detect_existing_shirt_and_map(self):
        """Detect the existing shirt and map virtual clothing to match its edges"""
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        
        # Detect face
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            face_x, face_y, face_w, face_h = faces[0]
            
            # Detect existing shirt edges using color segmentation
            shirt_edges = self.detect_shirt_edges(face_x, face_y, face_w, face_h)
            
            if shirt_edges:
                # Map virtual clothing to match existing shirt
                self.map_virtual_to_existing_shirt(shirt_edges)
                
                # Draw detected shirt edges
                self.draw_shirt_edges(shirt_edges)
                
                self.status_label.config(text="Existing shirt detected! Perfect mapping ready.")
                self.shirt_edges = shirt_edges
            else:
                self.status_label.config(text="Could not detect existing shirt edges.")
        else:
            self.status_label.config(text="No face detected!")
            
        self.update_display()
        
    def detect_shirt_edges(self, face_x, face_y, face_w, face_h):
        """Detect the edges of the existing shirt"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2HSV)
        
        # Define shirt color range (adjust based on your shirt color)
        # For light purple shirt, we'll detect non-skin colors
        lower_shirt = np.array([0, 0, 50])  # Lower bound for shirt
        upper_shirt = np.array([180, 255, 200])  # Upper bound for shirt
        
        # Create mask for shirt area
        shirt_mask = cv2.inRange(hsv, lower_shirt, upper_shirt)
        
        # Focus on the chest area below the face
        chest_region = shirt_mask[face_y + face_h:face_y + face_h + face_h*2, 
                                 max(0, face_x - face_w//2):min(self.original_image.shape[1], face_x + face_w*2)]
        
        if chest_region.size == 0:
            return None
            
        # Find contours of the shirt
        contours, _ = cv2.findContours(chest_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        # Get the largest contour (should be the shirt)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get bounding rectangle of the shirt
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Adjust coordinates to full image
        shirt_x = max(0, face_x - face_w//2) + x
        shirt_y = face_y + face_h + y
        shirt_w = w
        shirt_h = h
        
        # Detect collar area (top edge of shirt)
        collar_y = shirt_y
        collar_x = shirt_x
        collar_w = shirt_w
        
        # Detect shoulder edges (left and right edges of shirt)
        left_shoulder_x = shirt_x
        right_shoulder_x = shirt_x + shirt_w
        shoulder_y = shirt_y + shirt_h // 4  # Shoulder line is about 1/4 down from collar
        
        # Detect waist (bottom edge of shirt)
        waist_y = shirt_y + shirt_h
        waist_x = shirt_x
        waist_w = shirt_w
        
        return {
            'collar': (collar_x, collar_y, collar_w),
            'left_shoulder': (left_shoulder_x, shoulder_y),
            'right_shoulder': (right_shoulder_x, shoulder_y),
            'waist': (waist_x, waist_y, waist_w),
            'shirt_rect': (shirt_x, shirt_y, shirt_w, shirt_h)
        }
        
    def map_virtual_to_existing_shirt(self, shirt_edges):
        """Map virtual clothing to match the existing shirt edges"""
        # Calculate scaling factors to match existing shirt
        existing_width = shirt_edges['right_shoulder'][0] - shirt_edges['left_shoulder'][0]
        existing_height = shirt_edges['waist'][1] - shirt_edges['collar'][1]
        
        # Store mapping parameters
        self.mapping_params = {
            'target_x': shirt_edges['left_shoulder'][0],
            'target_y': shirt_edges['collar'][1],
            'target_width': existing_width,
            'target_height': existing_height,
            'collar_y': shirt_edges['collar'][1],
            'waist_y': shirt_edges['waist'][1]
        }
        
    def draw_shirt_edges(self, shirt_edges):
        """Draw the detected shirt edges"""
        image = self.original_image.copy()
        
        # Draw collar line (green)
        cv2.line(image, 
                (shirt_edges['collar'][0], shirt_edges['collar'][1]),
                (shirt_edges['collar'][0] + shirt_edges['collar'][2], shirt_edges['collar'][1]),
                (0, 255, 0), 3)
        
        # Draw shoulder line (blue)
        cv2.line(image, 
                shirt_edges['left_shoulder'],
                shirt_edges['right_shoulder'],
                (255, 0, 0), 3)
        
        # Draw waist line (red)
        cv2.line(image, 
                (shirt_edges['waist'][0], shirt_edges['waist'][1]),
                (shirt_edges['waist'][0] + shirt_edges['waist'][2], shirt_edges['waist'][1]),
                (0, 0, 255), 3)
        
        # Draw corner markers
        cv2.circle(image, (shirt_edges['collar'][0], shirt_edges['collar'][1]), 8, (0, 255, 0), -1)  # Green - collar left
        cv2.circle(image, (shirt_edges['collar'][0] + shirt_edges['collar'][2], shirt_edges['collar'][1]), 8, (0, 255, 0), -1)  # Green - collar right
        cv2.circle(image, shirt_edges['left_shoulder'], 8, (255, 0, 0), -1)  # Blue - left shoulder
        cv2.circle(image, shirt_edges['right_shoulder'], 8, (255, 0, 0), -1)  # Blue - right shoulder
        cv2.circle(image, (shirt_edges['waist'][0], shirt_edges['waist'][1]), 8, (0, 0, 255), -1)  # Red - waist left
        cv2.circle(image, (shirt_edges['waist'][0] + shirt_edges['waist'][2], shirt_edges['waist'][1]), 8, (0, 0, 255), -1)  # Red - waist right
        
        # Draw shirt bounding rectangle
        cv2.rectangle(image, 
                     (shirt_edges['shirt_rect'][0], shirt_edges['shirt_rect'][1]),
                     (shirt_edges['shirt_rect'][0] + shirt_edges['shirt_rect'][2], 
                      shirt_edges['shirt_rect'][1] + shirt_edges['shirt_rect'][3]),
                     (255, 255, 0), 2)  # Yellow rectangle
        
        self.current_image = image
        
    def apply_perfect_mapping(self):
        """Apply virtual clothing with perfect edge matching"""
        if not hasattr(self, 'mapping_params'):
            self.status_label.config(text="No mapping parameters available!")
            return
            
        try:
            # Resize virtual clothing to match existing shirt dimensions
            resized_clothing = cv2.resize(self.clothing_image, 
                                        (self.mapping_params['target_width'], 
                                         self.mapping_params['target_height']))
            
            # Apply clothing with perfect edge alignment
            self.current_image = self.apply_clothing_with_perfect_alignment(
                self.original_image, resized_clothing, 
                self.mapping_params['target_x'], 
                self.mapping_params['target_y']
            )
            
            self.status_label.config(text="Perfect mapping applied! Collar to collar, shoulder to shoulder!")
            self.update_display()
            
        except Exception as e:
            self.status_label.config(text=f"Error applying perfect mapping: {str(e)}")
            
    def apply_clothing_with_perfect_alignment(self, background, clothing, x, y):
        """Apply clothing with perfect edge alignment"""
        result = background.copy()
        
        # Get clothing dimensions
        h, w = clothing.shape[:2]
        
        # Ensure coordinates are within bounds
        x = max(0, min(x, background.shape[1] - w))
        y = max(0, min(y, background.shape[0] - h))
        
        # Extract the region where clothing will be placed
        bg_region = result[y:y+h, x:x+w]
        
        if clothing.shape[2] == 4:  # Has alpha channel
            # Extract alpha channel
            alpha = clothing[:, :, 3] / 255.0
            alpha = np.stack([alpha] * 3, axis=2)
            
            # Blend clothing with background
            blended = clothing[:, :, :3] * alpha + bg_region * (1 - alpha)
            result[y:y+h, x:x+w] = blended.astype(np.uint8)
        else:
            # No alpha channel, simple overlay
            result[y:y+h, x:x+w] = clothing
            
        return result
        
    def clear_clothing(self):
        """Clear the clothing overlay"""
        self.current_image = self.original_image.copy()
        self.detect_existing_shirt_and_map()
        
    def update_display(self):
        """Update the image display"""
        # Convert BGR to RGB for tkinter
        rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        
        # Resize for display
        height, width = rgb_image.shape[:2]
        max_width = 600
        if width > max_width:
            scale = max_width / width
            new_width = max_width
            new_height = int(height * scale)
            rgb_image = cv2.resize(rgb_image, (new_width, new_height))
            
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_image)
        photo = ImageTk.PhotoImage(pil_image)
        
        # Update label
        self.image_label.config(image=photo)
        self.image_label.image = photo  # Keep a reference
        
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python tryOn_perfect_mapping.py <image_path>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    app = PerfectShirtMapping(image_path)
    app.run()



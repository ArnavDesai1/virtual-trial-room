import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
import sys
import os
from PIL import Image, ImageTk

class ProperBodyMappingTryOn:
    def __init__(self, image_path):
        self.image_path = image_path
        self.root = tk.Tk()
        self.root.title("E-Dressing Room - Proper Body Mapping")
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
        
        # Body detection (upper body)
        self.body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
        
        self.setup_ui()
        self.detect_and_map_body_parts()
        
    def setup_ui(self):
        # Image display
        self.image_label = tk.Label(self.root)
        self.image_label.pack(pady=10)
        
        # Status label
        self.status_label = tk.Label(self.root, text="Detecting body parts...", font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.try_on_btn = tk.Button(button_frame, text="Try it ON", bg="green", fg="white", 
                                   command=self.apply_clothing, font=("Arial", 12))
        self.try_on_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(button_frame, text="Clear Clothing", bg="orange", fg="white", 
                                 command=self.clear_clothing, font=("Arial", 12))
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.close_btn = tk.Button(button_frame, text="Close", bg="red", fg="white", 
                                 command=self.root.quit, font=("Arial", 12))
        self.close_btn.pack(side=tk.LEFT, padx=5)
        
    def detect_and_map_body_parts(self):
        """Detect face and body parts, then map clothing properly"""
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
        
        # Detect face
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            face_x, face_y, face_w, face_h = faces[0]
            
            # Calculate body part positions based on face
            body_parts = self.calculate_body_parts_from_face(face_x, face_y, face_w, face_h)
            
            # Draw body part markers
            self.draw_body_part_markers(body_parts)
            
            # Update status
            self.status_label.config(text="Body parts detected! Ready for clothing mapping.")
            
            # Store body parts for clothing application
            self.body_parts = body_parts
            
        else:
            self.status_label.config(text="No face detected!")
            
        self.update_display()
        
    def calculate_body_parts_from_face(self, face_x, face_y, face_w, face_h):
        """Calculate actual body part positions from face detection"""
        
        # Face center
        face_center_x = face_x + face_w // 2
        face_center_y = face_y + face_h // 2
        
        # Calculate shoulder positions
        # Shoulders are wider than face and positioned below the face
        shoulder_width = face_w * 2.2  # Realistic shoulder width
        shoulder_y = face_y + face_h + 20  # Just below the face/neck
        
        left_shoulder_x = face_center_x - shoulder_width // 2
        right_shoulder_x = face_center_x + shoulder_width // 2
        
        # Calculate waist positions
        waist_y = shoulder_y + face_w * 1.5  # Realistic waist position
        waist_width = face_w * 1.8  # Slightly narrower than shoulders
        
        left_waist_x = face_center_x - waist_width // 2
        right_waist_x = face_center_x + waist_width // 2
        
        return {
            'face': (face_x, face_y, face_w, face_h),
            'left_shoulder': (int(left_shoulder_x), int(shoulder_y)),
            'right_shoulder': (int(right_shoulder_x), int(shoulder_y)),
            'left_waist': (int(left_waist_x), int(waist_y)),
            'right_waist': (int(right_waist_x), int(waist_y)),
            'shoulder_width': int(shoulder_width),
            'waist_width': int(waist_width)
        }
        
    def draw_body_part_markers(self, body_parts):
        """Draw markers for detected body parts"""
        image = self.original_image.copy()
        
        # Draw face rectangle
        face_x, face_y, face_w, face_h = body_parts['face']
        cv2.rectangle(image, (face_x, face_y), (face_x + face_w, face_y + face_h), (0, 255, 0), 2)
        
        # Draw shoulder points
        cv2.circle(image, body_parts['left_shoulder'], 8, (255, 0, 0), -1)  # Blue for left shoulder
        cv2.circle(image, body_parts['right_shoulder'], 8, (0, 0, 255), -1)  # Red for right shoulder
        
        # Draw waist points
        cv2.circle(image, body_parts['left_waist'], 6, (255, 255, 0), -1)  # Yellow for left waist
        cv2.circle(image, body_parts['right_waist'], 6, (0, 255, 255), -1)  # Cyan for right waist
        
        # Draw shoulder line
        cv2.line(image, body_parts['left_shoulder'], body_parts['right_shoulder'], (255, 0, 0), 2)
        
        # Draw waist line
        cv2.line(image, body_parts['left_waist'], body_parts['right_waist'], (255, 255, 0), 2)
        
        # Draw clothing area rectangle
        clothing_x = body_parts['left_shoulder'][0]
        clothing_y = body_parts['left_shoulder'][1]
        clothing_w = body_parts['shoulder_width']
        clothing_h = body_parts['right_waist'][1] - body_parts['left_shoulder'][1]
        
        cv2.rectangle(image, (clothing_x, clothing_y), 
                     (clothing_x + clothing_w, clothing_y + clothing_h), (0, 255, 255), 2)
        
        self.current_image = image
        
    def apply_clothing(self):
        """Apply clothing with proper body part mapping"""
        if not hasattr(self, 'body_parts'):
            self.status_label.config(text="No body parts detected!")
            return
            
        try:
            # Get clothing dimensions
            clothing_w = self.body_parts['shoulder_width']
            clothing_h = self.body_parts['right_waist'][1] - self.body_parts['left_shoulder'][1]
            
            # Position clothing at shoulders
            clothing_x = self.body_parts['left_shoulder'][0]
            clothing_y = self.body_parts['left_shoulder'][1]
            
            # Resize clothing to match body
            resized_clothing = cv2.resize(self.clothing_image, (clothing_w, clothing_h))
            
            # Apply clothing with proper blending
            self.current_image = self.apply_clothing_with_blending(
                self.original_image, resized_clothing, clothing_x, clothing_y
            )
            
            self.status_label.config(text="Clothing applied with proper body mapping!")
            self.update_display()
            
        except Exception as e:
            self.status_label.config(text=f"Error applying clothing: {str(e)}")
            
    def apply_clothing_with_blending(self, background, clothing, x, y):
        """Apply clothing with proper alpha blending"""
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
        self.detect_and_map_body_parts()
        
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
        print("Usage: python tryOn_proper_body_mapping.py <image_path>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    app = ProperBodyMappingTryOn(image_path)
    app.run()



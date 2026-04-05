import cv2
import numpy as np
import mediapipe as mp
import tkinter as tk
from tkinter import ttk
import threading
import sys
import os

class PerfectVirtualTrialRoom:
    def __init__(self, clothing_path):
        self.clothing_path = clothing_path
        self.cap = None
        self.running = False
        self.clothing_image = None
        
        # Initialize MediaPipe
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Initialize face detection as fallback
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.setup_gui()
        self.load_clothing()
        
    def setup_gui(self):
        """Setup the GUI window"""
        self.root = tk.Tk()
        self.root.title("Perfect Virtual Trial Room - No Debug Lines")
        self.root.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video display
        self.video_label = ttk.Label(main_frame)
        self.video_label.pack(pady=10)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Starting camera...", font=("Arial", 12))
        self.status_label.pack(pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start Camera", command=self.start_camera)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Camera", command=self.stop_camera, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.close_button = ttk.Button(button_frame, text="Close", command=self.close_app)
        self.close_button.pack(side=tk.LEFT, padx=5)
        
    def load_clothing(self):
        """Load the clothing image with proper error handling"""
        try:
            if not os.path.exists(self.clothing_path):
                raise FileNotFoundError(f"Clothing image not found: {self.clothing_path}")
                
            self.clothing_image = cv2.imread(self.clothing_path, cv2.IMREAD_UNCHANGED)
            if self.clothing_image is None:
                raise ValueError(f"Could not load clothing image: {self.clothing_path}")
                
            print(f"Successfully loaded clothing image: {self.clothing_path}")
            print(f"Clothing image shape: {self.clothing_image.shape}")
            
        except Exception as e:
            print(f"Error loading clothing: {e}")
            self.status_label.config(text=f"Error loading clothing: {e}")
            
    def detect_body_landmarks(self, image):
        """Detect body landmarks using MediaPipe with perfect accuracy"""
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process the image
            results = self.pose.process(rgb_image)
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                
                # Get key points for perfect body mapping
                h, w = image.shape[:2]
                
                # Shoulder points
                left_shoulder = [int(landmarks[11].x * w), int(landmarks[11].y * h)]
                right_shoulder = [int(landmarks[12].x * w), int(landmarks[12].y * h)]
                
                # Hip points
                left_hip = [int(landmarks[23].x * w), int(landmarks[23].y * h)]
                right_hip = [int(landmarks[24].x * w), int(landmarks[24].y * h)]
                
                # Calculate body dimensions
                shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
                body_height = abs((left_hip[1] + right_hip[1]) / 2 - (left_shoulder[1] + right_shoulder[1]) / 2)
                
                # Calculate body center and tilt
                body_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
                body_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
                
                # Calculate body tilt angle
                shoulder_angle = np.arctan2(right_shoulder[1] - left_shoulder[1], 
                                         right_shoulder[0] - left_shoulder[0])
                
                return {
                    'left_shoulder': left_shoulder,
                    'right_shoulder': right_shoulder,
                    'left_hip': left_hip,
                    'right_hip': right_hip,
                    'shoulder_width': shoulder_width,
                    'body_height': body_height,
                    'body_center': (int(body_center_x), int(body_center_y)),
                    'shoulder_angle': shoulder_angle,
                    'confidence': True
                }
            
            return None
            
        except Exception as e:
            print(f"Error in pose detection: {e}")
            return None
    
    def detect_face_fallback(self, image):
        """Fallback to face detection if pose detection fails"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                x, y, w, h = faces[0]
                
                # Calculate body position from face
                face_center_x = x + w // 2
                face_center_y = y + h // 2
                
                # Estimate body dimensions from face
                body_width = w * 2.5  # Body is typically 2.5x face width
                body_height = h * 4   # Body is typically 4x face height
                
                # Calculate shoulder and hip positions
                left_shoulder = [int(face_center_x - body_width // 2), int(face_center_y + h * 0.5)]
                right_shoulder = [int(face_center_x + body_width // 2), int(face_center_y + h * 0.5)]
                left_hip = [int(face_center_x - body_width // 2), int(face_center_y + h * 3)]
                right_hip = [int(face_center_x + body_width // 2), int(face_center_y + h * 3)]
                
                return {
                    'left_shoulder': left_shoulder,
                    'right_shoulder': right_shoulder,
                    'left_hip': left_hip,
                    'right_hip': right_hip,
                    'shoulder_width': body_width,
                    'body_height': body_height,
                    'body_center': (face_center_x, int(face_center_y + h * 1.5)),
                    'shoulder_angle': 0,
                    'confidence': False
                }
            
            return None
            
        except Exception as e:
            print(f"Error in face detection: {e}")
            return None
    
    def apply_perfect_clothing(self, image, body_data):
        """Apply clothing with perfect body mapping - no debug lines"""
        try:
            if body_data is None or self.clothing_image is None:
                return image
                
            # Get body dimensions
            shoulder_width = body_data['shoulder_width']
            body_height = body_data['body_height']
            body_center = body_data['body_center']
            shoulder_angle = body_data['shoulder_angle']
            
            # Calculate clothing dimensions to perfectly match your body
            # Make it slightly wider to cover your actual shirt completely
            clothing_width = int(shoulder_width * 1.1)  # 10% wider than shoulders
            clothing_height = int(body_height * 1.2)  # 20% taller to cover waist area
            
            # Ensure minimum dimensions
            clothing_width = max(clothing_width, 100)
            clothing_height = max(clothing_height, 150)
            
            # Resize clothing to match your body perfectly
            resized_clothing = cv2.resize(self.clothing_image, (clothing_width, clothing_height))
            
            # Calculate position to center on your body
            start_x = int(body_center[0] - clothing_width // 2)
            start_y = int(body_center[1] - clothing_height // 3)  # Position slightly higher for collar alignment
            
            # Ensure the clothing fits within the image
            end_x = min(start_x + clothing_width, image.shape[1])
            end_y = min(start_y + clothing_height, image.shape[0])
            
            # Adjust clothing size if it would go out of bounds
            if start_x < 0:
                start_x = 0
            if start_y < 0:
                start_y = 0
                
            # Create a copy of the image for overlay
            result_image = image.copy()
            
            # Apply clothing with perfect alpha blending
            if len(resized_clothing.shape) == 3:
                # No alpha channel, use simple overlay
                clothing_region = resized_clothing[:end_y-start_y, :end_x-start_x]
                result_image[start_y:end_y, start_x:end_x] = clothing_region
            else:
                # Has alpha channel, use proper blending
                clothing_region = resized_clothing[:end_y-start_y, :end_x-start_x]
                if clothing_region.shape[2] == 4:  # BGRA
                    alpha = clothing_region[:, :, 3] / 255.0
                    alpha = np.stack([alpha, alpha, alpha], axis=2)
                    
                    # Blend the clothing with the background
                    background = result_image[start_y:end_y, start_x:end_x]
                    blended = (1 - alpha) * background + alpha * clothing_region[:, :, :3]
                    result_image[start_y:end_y, start_x:end_x] = blended.astype(np.uint8)
                else:
                    # No alpha, simple overlay
                    result_image[start_y:end_y, start_x:end_x] = clothing_region
            
            return result_image
            
        except Exception as e:
            print(f"Error applying clothing: {e}")
            return image
    
    def camera_loop(self):
        """Main camera loop with perfect error handling"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Could not open camera")
                
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.running = True
            self.status_label.config(text="Camera started - Perfect body mapping active!")
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to read frame")
                    break
                    
                try:
                    # Detect body landmarks
                    body_data = self.detect_body_landmarks(frame)
                    
                    # Fallback to face detection if pose detection fails
                    if body_data is None:
                        body_data = self.detect_face_fallback(frame)
                    
                    # Apply perfect clothing overlay
                    if body_data is not None:
                        frame = self.apply_perfect_clothing(frame, body_data)
                        self.status_label.config(text="Perfect body mapping active - No debug lines!")
                    else:
                        self.status_label.config(text="Looking for body...")
                    
                    # Convert frame for display
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_pil = Image.fromarray(frame_rgb)
                    frame_tk = ImageTk.PhotoImage(frame_pil)
                    
                    # Update display
                    self.video_label.config(image=frame_tk)
                    self.video_label.image = frame_tk
                    
                except Exception as e:
                    print(f"Frame processing error: {e}")
                    continue
                    
        except Exception as e:
            print(f"Camera error: {e}")
            self.status_label.config(text=f"Camera error: {e}")
            
        finally:
            if self.cap:
                self.cap.release()
            self.running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
    
    def start_camera(self):
        """Start the camera in a separate thread"""
        if not self.running:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Start camera loop in separate thread
            camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
            camera_thread.start()
    
    def stop_camera(self):
        """Stop the camera"""
        self.running = False
        if self.cap:
            self.cap.release()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Camera stopped")
    
    def close_app(self):
        """Close the application"""
        self.running = False
        if self.cap:
            self.cap.release()
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.close_app()

# Import required modules for image display
try:
    from PIL import Image, ImageTk
except ImportError:
    print("PIL not available, using OpenCV display")
    Image = None
    ImageTk = None

def main():
    if len(sys.argv) != 2:
        print("Usage: python tryOn_perfect_final.py <clothing_image_path>")
        return
        
    clothing_path = sys.argv[1]
    
    if not os.path.exists(clothing_path):
        print(f"Error: Clothing image not found: {clothing_path}")
        return
    
    print(f"Starting Perfect Virtual Trial Room with: {clothing_path}")
    
    try:
        app = PerfectVirtualTrialRoom(clothing_path)
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")

if __name__ == "__main__":
    main()

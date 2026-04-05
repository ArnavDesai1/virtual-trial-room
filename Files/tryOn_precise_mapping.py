import cv2
import numpy as np
import mediapipe as mp
import tkinter as tk
from tkinter import ttk
import threading
import sys
import os

class PreciseMappingVirtualTrialRoom:
    def __init__(self, clothing_path):
        self.clothing_path = clothing_path
        self.cap = None
        self.running = False
        self.clothing_image = None
        
        # Initialize MediaPipe
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # Higher complexity for better accuracy
            enable_segmentation=False,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )
        
        # Initialize face detection as fallback
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.setup_gui()
        self.load_clothing()
        
    def setup_gui(self):
        """Setup the GUI window"""
        self.root = tk.Tk()
        self.root.title("Precise Body Mapping Virtual Trial Room")
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
            
    def detect_precise_body_landmarks(self, image):
        """Detect precise body landmarks for perfect mapping"""
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process the image
            results = self.pose.process(rgb_image)
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                h, w = image.shape[:2]
                
                # Get ALL relevant body points for precise mapping
                # Shoulders
                left_shoulder = [int(landmarks[11].x * w), int(landmarks[11].y * h)]
                right_shoulder = [int(landmarks[12].x * w), int(landmarks[12].y * h)]
                
                # Elbows (for sleeve positioning)
                left_elbow = [int(landmarks[13].x * w), int(landmarks[13].y * h)]
                right_elbow = [int(landmarks[14].x * w), int(landmarks[14].y * h)]
                
                # Hips (for waist positioning)
                left_hip = [int(landmarks[23].x * w), int(landmarks[23].y * h)]
                right_hip = [int(landmarks[24].x * w), int(landmarks[24].y * h)]
                
                # Waist (midpoint between shoulders and hips)
                left_waist = [int((left_shoulder[0] + left_hip[0]) / 2), int((left_shoulder[1] + left_hip[1]) / 2)]
                right_waist = [int((right_shoulder[0] + right_hip[0]) / 2), int((right_shoulder[1] + right_hip[1]) / 2)]
                
                # Neck (for collar positioning)
                left_ear = [int(landmarks[7].x * w), int(landmarks[7].y * h)]
                right_ear = [int(landmarks[8].x * w), int(landmarks[8].y * h)]
                neck_center = [int((left_ear[0] + right_ear[0]) / 2), int((left_ear[1] + right_ear[1]) / 2)]
                
                # Calculate precise dimensions
                shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
                body_height = abs((left_hip[1] + right_hip[1]) / 2 - (left_shoulder[1] + right_shoulder[1]) / 2)
                
                # Calculate body center
                body_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
                body_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
                
                # Calculate body tilt
                shoulder_angle = np.arctan2(right_shoulder[1] - left_shoulder[1], 
                                         right_shoulder[0] - left_shoulder[0])
                
                return {
                    # Precise body points
                    'left_shoulder': left_shoulder,
                    'right_shoulder': right_shoulder,
                    'left_elbow': left_elbow,
                    'right_elbow': right_elbow,
                    'left_hip': left_hip,
                    'right_hip': right_hip,
                    'left_waist': left_waist,
                    'right_waist': right_waist,
                    'neck_center': neck_center,
                    
                    # Dimensions
                    'shoulder_width': shoulder_width,
                    'body_height': body_height,
                    'body_center': (int(body_center_x), int(body_center_y)),
                    'shoulder_angle': shoulder_angle,
                    'confidence': True
                }
            
            return None
            
        except Exception as e:
            print(f"Error in precise pose detection: {e}")
            return None
    
    def detect_face_fallback(self, image):
        """Fallback to face detection with precise body estimation"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                x, y, w, h = faces[0]
                
                # Calculate precise body position from face
                face_center_x = x + w // 2
                face_center_y = y + h // 2
                
                # Estimate precise body dimensions
                body_width = w * 3.0  # Precise body width
                body_height = h * 4.5  # Precise body height
                
                # Calculate precise body points
                left_shoulder = [int(face_center_x - body_width // 2), int(face_center_y + h * 0.2)]
                right_shoulder = [int(face_center_x + body_width // 2), int(face_center_y + h * 0.2)]
                left_elbow = [int(face_center_x - body_width // 2), int(face_center_y + h * 1.5)]
                right_elbow = [int(face_center_x + body_width // 2), int(face_center_y + h * 1.5)]
                left_hip = [int(face_center_x - body_width // 2), int(face_center_y + h * 3.5)]
                right_hip = [int(face_center_x + body_width // 2), int(face_center_y + h * 3.5)]
                left_waist = [int(face_center_x - body_width // 2), int(face_center_y + h * 1.8)]
                right_waist = [int(face_center_x + body_width // 2), int(face_center_y + h * 1.8)]
                neck_center = [face_center_x, int(face_center_y + h * 0.1)]
                
                return {
                    'left_shoulder': left_shoulder,
                    'right_shoulder': right_shoulder,
                    'left_elbow': left_elbow,
                    'right_elbow': right_elbow,
                    'left_hip': left_hip,
                    'right_hip': right_hip,
                    'left_waist': left_waist,
                    'right_waist': right_waist,
                    'neck_center': neck_center,
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
    
    def apply_precise_clothing_mapping(self, image, body_data):
        """Apply clothing with PRECISE body part mapping"""
        try:
            if body_data is None or self.clothing_image is None:
                return image
                
            # Get precise body points
            left_shoulder = body_data['left_shoulder']
            right_shoulder = body_data['right_shoulder']
            left_waist = body_data['left_waist']
            right_waist = body_data['right_waist']
            neck_center = body_data['neck_center']
            
            # Calculate precise clothing dimensions
            # Width: from left shoulder to right shoulder
            clothing_width = abs(right_shoulder[0] - left_shoulder[0])
            
            # Height: from neck to waist
            clothing_height = abs((left_waist[1] + right_waist[1]) / 2 - neck_center[1])
            
            # Add some padding for better coverage
            clothing_width = int(clothing_width * 1.1)  # 10% wider
            clothing_height = int(clothing_height * 1.2)  # 20% taller
            
            # Ensure minimum dimensions
            clothing_width = max(clothing_width, 150)
            clothing_height = max(clothing_height, 200)
            
            # Resize clothing to precise dimensions
            resized_clothing = cv2.resize(self.clothing_image, (clothing_width, clothing_height))
            
            # Calculate precise positioning
            # Left edge aligns with left shoulder
            start_x = left_shoulder[0] - int(clothing_width * 0.05)  # Slight offset for better alignment
            
            # Top edge aligns with neck (with small gap)
            start_y = neck_center[1] + int(clothing_height * 0.1)  # Small gap for neck
            
            # Ensure the clothing fits within the image
            end_x = min(start_x + clothing_width, image.shape[1])
            end_y = min(start_y + clothing_height, image.shape[0])
            
            # Adjust if out of bounds
            if start_x < 0:
                start_x = 0
            if start_y < 0:
                start_y = 0
                
            # Create result image
            result_image = image.copy()
            
            # Apply precise clothing overlay
            try:
                # Get the region to overlay
                clothing_region = resized_clothing[:end_y-start_y, :end_x-start_x]
                
                # Simple overlay for precise mapping
                if len(clothing_region.shape) == 3:
                    # RGB image - direct overlay
                    result_image[start_y:end_y, start_x:end_x] = clothing_region
                else:
                    # Has alpha channel - convert to RGB first
                    if clothing_region.shape[2] == 4:
                        # BGRA to BGR
                        clothing_rgb = clothing_region[:, :, :3]
                        result_image[start_y:end_y, start_x:end_x] = clothing_rgb
                    else:
                        # Direct overlay
                        result_image[start_y:end_y, start_x:end_x] = clothing_region
                        
            except Exception as e:
                print(f"Precise overlay error: {e}")
                return image
            
            return result_image
            
        except Exception as e:
            print(f"Error in precise clothing mapping: {e}")
            return image
    
    def camera_loop(self):
        """Main camera loop with precise mapping"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Could not open camera")
                
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.running = True
            self.status_label.config(text="Camera started - Precise body mapping active!")
            
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to read frame")
                    break
                    
                try:
                    # Detect precise body landmarks
                    body_data = self.detect_precise_body_landmarks(frame)
                    
                    # Fallback to face detection if pose detection fails
                    if body_data is None:
                        body_data = self.detect_face_fallback(frame)
                    
                    # Apply precise clothing mapping
                    if body_data is not None:
                        frame = self.apply_precise_clothing_mapping(frame, body_data)
                        if body_data['confidence']:
                            self.status_label.config(text="Precise body mapping - Perfect edge alignment!")
                        else:
                            self.status_label.config(text="Face detection mode - Applying clothing overlay!")
                    else:
                        self.status_label.config(text="Looking for body... Move closer to camera")
                    
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
            self.status_label.config(text="Starting camera and loading clothing overlay...")
            
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
        print("Usage: python tryOn_precise_mapping.py <clothing_image_path>")
        return
        
    clothing_path = sys.argv[1]
    
    if not os.path.exists(clothing_path):
        print(f"Error: Clothing image not found: {clothing_path}")
        return
    
    print(f"Starting Precise Body Mapping Virtual Trial Room with: {clothing_path}")
    
    try:
        app = PreciseMappingVirtualTrialRoom(clothing_path)
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")

if __name__ == "__main__":
    main()

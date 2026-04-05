import cv2
import numpy as np
import mediapipe as mp
import tkinter as tk
from tkinter import ttk
import threading
import sys
import os

# Import PIL for image display
try:
    from PIL import Image, ImageTk
except ImportError:
    print("Warning: PIL not available, using OpenCV display instead")
    Image = None
    ImageTk = None

class ProperOverlayVirtualTrialRoom:
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
        self.root.title("Proper Overlay Virtual Trial Room - Superimposed Clothing")
        self.root.geometry("800x600")
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video display - SINGLE display for overlaid video
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
                
                # Estimate precise body dimensions - MUCH LARGER for full coverage
                body_width = w * 3.5  # Precise body width for full coverage
                body_height = h * 5.0  # Precise body height for full coverage
                
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
    
    def apply_proper_overlay(self, image, body_data):
        """Apply clothing as PROPER OVERLAY - superimposed on your body with transparent background"""
        try:
            if body_data is None or self.clothing_image is None:
                return image
                
            # Get precise body points
            left_shoulder = body_data['left_shoulder']
            right_shoulder = body_data['right_shoulder']
            left_waist = body_data['left_waist']
            right_waist = body_data['right_waist']
            neck_center = body_data['neck_center']
            
            # Calculate precise clothing dimensions with adaptive body shape mapping
            # Width: from left shoulder to right shoulder with full coverage
            shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
            
            # Height: from neck to waist with better torso mapping
            torso_height = abs((left_waist[1] + right_waist[1]) / 2 - neck_center[1])
            
            # Adaptive sizing based on body parts with proper shoulder coverage
            # Reasonable width coverage with focus on shoulder alignment
            clothing_width = int(shoulder_width * 1.4)  # 40% wider for proper shoulder coverage
            
            # Reasonable height coverage
            clothing_height = int(torso_height * 1.6)  # 60% taller for torso coverage
            
            # Make lower torso wider to cover the actual shirt behind
            # Calculate waist width (should be wider than shoulders for natural fit)
            waist_width = abs(right_waist[0] - left_waist[0])
            if waist_width > shoulder_width:
                # If waist is wider, use waist width as base
                clothing_width = max(clothing_width, int(waist_width * 1.3))
            
            # Ensure reasonable minimum dimensions
            clothing_width = max(clothing_width, 280)  # Minimum 280px width for shoulder coverage
            clothing_height = max(clothing_height, 400)  # Minimum 400px height for torso coverage
            
            # Resize clothing to precise dimensions
            resized_clothing = cv2.resize(self.clothing_image, (clothing_width, clothing_height))
            
            # Calculate precise positioning with fine-tuning
            # Center the shirt properly on your body
            body_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
            start_x = int(body_center_x - clothing_width / 2)  # Center on body
            
            # Shift down to match collars better
            start_y = neck_center[1] + int(clothing_height * 0.08)  # Down offset to match collar position
            
            # Add distance-based scaling control to prevent gigantic sizing when far away
            # Calculate distance factor based on shoulder width (smaller when far, larger when close)
            distance_factor = max(0.8, min(1.2, shoulder_width / 150))  # Scale between 0.8 and 1.2
            clothing_width = int(clothing_width * distance_factor)
            clothing_height = int(clothing_height * distance_factor)
            
            # Recalculate positioning after scaling - keep it centered
            body_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
            start_x = int(body_center_x - clothing_width / 2)
            resized_clothing = cv2.resize(self.clothing_image, (clothing_width, clothing_height))
            
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
            
            # Apply PROPER OVERLAY - handle alpha channel for transparent background
            try:
                # Get the region to overlay
                clothing_region = resized_clothing[:end_y-start_y, :end_x-start_x]
                
                # PROPER OVERLAY with alpha channel handling
                if len(clothing_region.shape) == 3:
                    if clothing_region.shape[2] == 4:  # BGRA - has alpha channel
                        # Extract alpha channel
                        alpha = clothing_region[:, :, 3] / 255.0
                        
                        # Extract BGR channels
                        clothing_bgr = clothing_region[:, :, :3]
                        
                        # Create alpha mask for proper blending
                        alpha_3d = np.stack([alpha, alpha, alpha], axis=2)
                        
                        # Blend the clothing with the background
                        background = result_image[start_y:end_y, start_x:end_x]
                        blended = (1 - alpha_3d) * background + alpha_3d * clothing_bgr
                        result_image[start_y:end_y, start_x:end_x] = blended.astype(np.uint8)
                        
                    else:  # BGR - no alpha channel
                        # Direct overlay for BGR
                        result_image[start_y:end_y, start_x:end_x] = clothing_region
                else:
                    # Grayscale - convert to BGR
                    clothing_bgr = cv2.cvtColor(clothing_region, cv2.COLOR_GRAY2BGR)
                    result_image[start_y:end_y, start_x:end_x] = clothing_bgr
                        
            except Exception as e:
                print(f"Proper overlay error: {e}")
                return image
            
            return result_image
            
        except Exception as e:
            print(f"Error in proper overlay: {e}")
            return image
    
    def camera_loop(self):
        """Main camera loop with proper overlay"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Could not open camera")
                
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.running = True
            self.status_label.config(text="Camera started - Proper overlay active!")
            
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
                    
                    # Apply proper overlay
                    if body_data is not None:
                        frame = self.apply_proper_overlay(frame, body_data)
                        if body_data['confidence']:
                            self.status_label.config(text="Perfect body mapping - Clothing superimposed!")
                        else:
                            self.status_label.config(text="Face detection mode - Clothing superimposed!")
                    else:
                        self.status_label.config(text="Looking for body... Move closer to camera")
                    
                    # Convert frame for display
                    if Image is not None and ImageTk is not None:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame_pil = Image.fromarray(frame_rgb)
                        frame_tk = ImageTk.PhotoImage(frame_pil)
                        
                        # Update display
                        self.video_label.config(image=frame_tk)
                        self.video_label.image = frame_tk
                    else:
                        # Fallback: display text on label
                        self.status_label.config(text="PIL unavailable - please install Pillow")
                    
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



def main():
    if len(sys.argv) != 2:
        print("Usage: python tryOn_proper_overlay.py <clothing_image_path>")
        return
        
    clothing_path = sys.argv[1]
    
    if not os.path.exists(clothing_path):
        print(f"Error: Clothing image not found: {clothing_path}")
        return
    
    print(f"Starting Proper Overlay Virtual Trial Room with: {clothing_path}")
    
    try:
        app = ProperOverlayVirtualTrialRoom(clothing_path)
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")

if __name__ == "__main__":
    main()

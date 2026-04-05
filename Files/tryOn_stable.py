import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import sys
import os

# Logging to file
LOG_FILE = "tryon_debug.log"

def log(msg):
    """Log to both console and file"""
    print(msg)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(msg + '\n')
    except:
        pass

class TryOnApp:
    def __init__(self, clothing_path):
        self.clothing_path = clothing_path
        self.running = False
        self.cap = None
        self.clothing_image = None
        self.frame_count = 0
        
        # Create window
        self.root = tk.Tk()
        self.root.title("Virtual Try-On - Press Q or Close to Exit")
        self.root.geometry("800x600")
        
        # Label for video
        self.video_label = ttk.Label(self.root, background="black")
        self.video_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status label
        self.status_label = ttk.Label(self.root, text="Loading...", foreground="green")
        self.status_label.pack()
        
        # Close button
        self.close_btn = ttk.Button(self.root, text="Close Try-On", command=self.close_app)
        self.close_btn.pack(pady=5)
        
        # Load resources
        self.load_resources()
        
        # Start camera thread
        if self.cap and self.clothing_image is not None:
            self.running = True
            self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
            self.camera_thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        
    def load_resources(self):
        try:
            log(f"Loading clothing: {self.clothing_path}")
            self.clothing_image = cv2.imread(self.clothing_path, cv2.IMREAD_UNCHANGED)
            if self.clothing_image is None:
                self.status_label.config(text=f"ERROR: Could not load image", foreground="red")
                log(f"ERROR: Could not load image: {self.clothing_path}")
                return
            
            log(f"✓ Clothing loaded: {self.clothing_image.shape}")
            
            # Open camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(1)
            
            if not self.cap.isOpened():
                self.status_label.config(text="ERROR: No camera found", foreground="red")
                log("ERROR: No camera found")
                return
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            log("✓ Camera opened successfully")
            self.status_label.config(text="Camera started - Try on your clothes!", foreground="green")
            
        except Exception as e:
            self.status_label.config(text=f"ERROR: {e}", foreground="red")
            log(f"ERROR loading resources: {e}")
    
    def overlay_clothing(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                x, y, w, h = faces[0]
                body_width = int(w * 3.0)
                body_height = int(h * 4.5)
                
                start_x = max(0, int(x + w/2 - body_width/2))
                start_y = max(0, int(y - h * 0.2))
                end_x = min(frame.shape[1], start_x + body_width)
                end_y = min(frame.shape[0], start_y + body_height)
                
                resize_w = end_x - start_x
                resize_h = end_y - start_y
                
                if resize_w > 0 and resize_h > 0:
                    resized_clothing = cv2.resize(self.clothing_image, (resize_w, resize_h))
                    
                    if len(resized_clothing.shape) == 3 and resized_clothing.shape[2] == 4:
                        alpha = resized_clothing[:, :, 3] / 255.0
                        bgr = resized_clothing[:, :, :3]
                        alpha = np.stack([alpha, alpha, alpha], axis=2)
                        
                        try:
                            bg = frame[start_y:end_y, start_x:end_x]
                            overlay = (1 - alpha) * bg + alpha * bgr
                            frame[start_y:end_y, start_x:end_x] = overlay.astype(np.uint8)
                        except:
                            pass
                    else:
                        try:
                            frame[start_y:end_y, start_x:end_x] = resized_clothing[:, :, :3]
                        except:
                            pass
        except:
            pass
        
        return frame
    
    def camera_loop(self):
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    log("Frame read failed")
                    break
                
                self.frame_count += 1
                
                # Flip for mirror effect
                frame = cv2.flip(frame, 1)
                
                # Overlay clothing
                frame = self.overlay_clothing(frame)
                
                # Add text
                cv2.putText(frame, 'Virtual Try-On', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           1, (0, 255, 0), 2)
                cv2.putText(frame, f'Frames: {self.frame_count}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (255, 255, 255), 2)
                cv2.putText(frame, 'Press Q to quit', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (255, 255, 255), 2)
                
                # Convert for display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                tk_image = ImageTk.PhotoImage(pil_image)
                
                # Update label
                self.video_label.config(image=tk_image)
                self.video_label.image = tk_image
                
                # Update status
                if self.frame_count % 30 == 0:
                    self.status_label.config(text=f"Running - Frame {self.frame_count}")
                
                self.root.update()
                
                # Check for quit
                if not self.running:
                    break
                    
        except Exception as e:
            log(f"Camera loop error: {e}")
            self.status_label.config(text=f"ERROR: {e}", foreground="red")
    
    def close_app(self):
        log(f"Closing - Processed {self.frame_count} frames")
        self.running = False
        if self.cap:
            self.cap.release()
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

def main():
    try:
        # Clear old log
        if os.path.exists(LOG_FILE):
            open(LOG_FILE, 'w').close()
        
        log("=== Virtual Try-On Started ===")
        
        if len(sys.argv) != 2:
            log("Usage: python tryOn_simple_working.py <clothing_image_path>")
            return
        
        clothing_path = sys.argv[1]
        log(f"Clothing path: {clothing_path}")
        
        if not os.path.exists(clothing_path):
            log(f"ERROR: Image not found: {clothing_path}")
            return
        
        app = TryOnApp(clothing_path)
        app.run()
        log("✓ App closed gracefully")
        
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())

if __name__ == "__main__":
    main()

import cv2
import numpy as np
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

def overlay_clothing(frame, clothing_image, face_cascade):
    """Simple clothing overlay using face detection"""
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            x, y, w, h = faces[0]
            
            # Calculate body position based on face
            body_width = int(w * 3.0)
            body_height = int(h * 4.5)
            
            # Position clothing starting from top of face and extending down
            start_x = max(0, int(x + w/2 - body_width/2))
            start_y = max(0, int(y - h * 0.2))
            
            end_x = min(frame.shape[1], start_x + body_width)
            end_y = min(frame.shape[0], start_y + body_height)
            
            # Resize clothing to fit
            resize_w = end_x - start_x
            resize_h = end_y - start_y
            
            if resize_w > 0 and resize_h > 0:
                resized_clothing = cv2.resize(clothing_image, (resize_w, resize_h))
                
                # Handle alpha channel
                if len(resized_clothing.shape) == 3 and resized_clothing.shape[2] == 4:
                    alpha = resized_clothing[:, :, 3] / 255.0
                    bgr = resized_clothing[:, :, :3]
                    alpha = np.stack([alpha, alpha, alpha], axis=2)
                    
                    bg = frame[start_y:end_y, start_x:end_x]
                    overlay = (1 - alpha) * bg + alpha * bgr
                    frame[start_y:end_y, start_x:end_x] = overlay.astype(np.uint8)
                else:
                    frame[start_y:end_y, start_x:end_x] = resized_clothing[:, :, :3]
    except Exception as e:
        log(f"Overlay error: {e}")
    
    return frame

def main():
    try:
        # Clear old log
        open(LOG_FILE, 'w').close()
        
        log("=== Virtual Try-On Started ===")
        
        if len(sys.argv) != 2:
            log("Usage: python tryOn_simple_working.py <clothing_image_path>")
            return
        
        clothing_path = sys.argv[1]
        log(f"Clothing path: {clothing_path}")
        
        if not os.path.exists(clothing_path):
            log(f"Error: Image not found: {clothing_path}")
            return
        
        # Load clothing image
        clothing_image = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
        if clothing_image is None:
            log(f"Error: Could not load image: {clothing_path}")
            return
        
        log(f"✓ Loaded clothing image: {clothing_image.shape}")
        
        # Load face detector
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        log("✓ Face detector loaded")
        
        # Open camera
        log("Opening camera...")
        cap = cv2.VideoCapture(0)
        
        # Try alternative camera if 0 doesn't work
        if not cap.isOpened():
            log("Camera 0 failed, trying camera 1...")
            cap = cv2.VideoCapture(1)
        
        if not cap.isOpened():
            log("ERROR: Could not open any camera")
            return
        
        log("✓ Camera opened successfully")
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to get latest frames
        
        log("Starting main loop. Press 'q' to quit")
        
        frame_count = 0
        while True:
            try:
                ret, frame = cap.read()
                if not ret:
                    log(f"Frame read failed at {frame_count}")
                    break
                
                frame_count += 1
                
                # Apply clothing overlay
                frame = overlay_clothing(frame, clothing_image, face_cascade)
                
                # Add text
                cv2.putText(frame, 'Virtual Try-On', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           1, (0, 255, 0), 2)
                cv2.putText(frame, f'Frames: {frame_count}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (255, 255, 255), 2)
                cv2.putText(frame, 'Press Q to quit    S to save', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (255, 255, 255), 2)
                
                # Display
                cv2.imshow('Virtual Try-On - Press Q to Close', frame)
                
                # Log every 30 frames
                if frame_count % 30 == 0:
                    log(f"Frame {frame_count} processed")
                
                # Handle keyboard with longer wait time
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    log("Quit command received")
                    break
                elif key == ord('s') or key == ord('S'):
                    filename = f'screenshot_{frame_count}.png'
                    cv2.imwrite(filename, frame)
                    log(f"Saved: {filename}")
                    
            except Exception as e:
                log(f"Error in main loop: {e}")
                break
        
        log(f"Loop ended after {frame_count} frames")
        cap.release()
        cv2.destroyAllWindows()
        log("✓ Try-On session ended gracefully")
        
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())

if __name__ == "__main__":
    main()

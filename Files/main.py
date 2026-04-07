

from flask import Flask, render_template, Response,redirect,request, jsonify, url_for
import os
import sys
import subprocess
from dotenv import load_dotenv
import cv2
import numpy as np
import base64
from io import BytesIO

# Try relative import first (for gunicorn), fallback to absolute (for local)
try:
    from .camera import VideoCamera
except ImportError:
    from camera import VideoCamera

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

CART=[]

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/checkOut')
def checkOut():
    return render_template('checkout.html')

@app.route('/tryon/<path:file_path>',methods = ['POST', 'GET'])
def tryon(file_path):
    print(f"DEBUG: Received tryon request for: {file_path}")
    file_path = file_path.replace(',','/')
    print("File path="+file_path)
    
    # Get the directory of the main.py file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct full path to clothing image
    full_path = os.path.join(script_dir, 'static', 'images', file_path)
    print("Full path="+full_path)
    
    # Check if file exists
    if not os.path.exists(full_path):
        return f"Error: Clothing image not found: {full_path}", 404
    
    # Construct clothing path relative to static folder
    clothing_path = f"static/images/{file_path}"
    
    # Redirect to web-based try-on with the clothing image as parameter
    return redirect(url_for('tryon_web') + f'?clothing={clothing_path}')

@app.route('/tryall',methods = ['POST', 'GET'])
def tryall():
        CART = request.form['mydata'].replace(',', '/')
        print("Cart=="+CART)
        os.system('python test.py ' + CART)
        render_template('checkout.html', message='')


@app.route('/')
def indexx():
    return render_template('index.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/product')
def product():
    return render_template('product.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route("/cart/<file_path>",methods = ['POST', 'GET'])
def cart(file_path):
    global CART
    file_path = file_path.replace(',','/')
    print("ADDED", file_path)
    CART.append(file_path)
    return render_template("checkout.html")

@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/firebase-config')
def firebase_config():
    """Serve Firebase config from environment variables (not exposed in frontend)"""
    config = {
        "apiKey": os.environ.get("FIREBASE_API_KEY", ""),
        "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN", "virtual-trial-room-3cff3.firebaseapp.com"),
        "projectId": os.environ.get("FIREBASE_PROJECT_ID", "virtual-trial-room-3cff3"),
        "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET", "virtual-trial-room-3cff3.firebasestorage.app"),
        "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID", "678744292818"),
        "appId": os.environ.get("FIREBASE_APP_ID", "1:678744292818:web:a31747dd608d86b21f1c0b"),
        "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID", "G-10TCLDZE4X")
    }
    return jsonify(config)

@app.route('/tryon-web')
def tryon_web():
    """Web-based try-on with live camera feed"""
    return render_template('tryon-web.html')

@app.route('/api/tryon-process', methods=['POST'])
def tryon_process():
    """Process video frame with clothing overlay using face detection"""
    try:
        data = request.get_json()
        if not data or 'frame' not in data:
            return jsonify({'error': 'Missing frame data'}), 400
        
        # Decode frame from base64
        frame_data = data['frame'].split(',')[1] if ',' in data['frame'] else data['frame']
        img_array = np.frombuffer(base64.b64decode(frame_data), np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid frame data'}), 400
        
        # Decode clothing image
        clothing_data = data.get('clothing', '')
        if clothing_data.startswith('data:'):
            clothing_data = clothing_data.split(',')[1]
        
        clothing_array = np.frombuffer(base64.b64decode(clothing_data), np.uint8)
        clothing = cv2.imdecode(clothing_array, cv2.IMREAD_UNCHANGED)
        
        if clothing is None:
            return jsonify({'error': 'Invalid clothing image'}), 400
        
        # Detect face for proper clothing positioning
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # Use first detected face
                x, y, w, h = faces[0]
                
                # Calculate body dimensions based on face size
                # Body width = 3x face width, body height = 4.5x face height
                body_width = int(w * 3.0)
                body_height = int(h * 4.5)
                
                # Position clothing centered on face, slightly above
                start_x = max(0, int(x + w/2 - body_width/2))
                start_y = max(0, int(y - h * 0.2))
                end_x = min(frame.shape[1], start_x + body_width)
                end_y = min(frame.shape[0], start_y + body_height)
                
                resize_w = end_x - start_x
                resize_h = end_y - start_y
                
                if resize_w > 0 and resize_h > 0:
                    # Resize clothing to fit calculated body area
                    resized_clothing = cv2.resize(clothing, (resize_w, resize_h))
                    
                    # Apply with alpha blending if available
                    if resized_clothing.shape[2] == 4:
                        alpha = resized_clothing[:, :, 3] / 255.0
                        alpha_3d = np.stack([alpha, alpha, alpha], axis=2)
                        
                        try:
                            bg = frame[start_y:end_y, start_x:end_x].astype(float)
                            fg = resized_clothing[:, :, :3].astype(float)
                            blended = (1 - alpha_3d) * bg + alpha_3d * fg
                            frame[start_y:end_y, start_x:end_x] = blended.astype(np.uint8)
                        except Exception as e:
                            print(f"Alpha blending error: {e}")
                    else:
                        try:
                            frame[start_y:end_y, start_x:end_x] = resized_clothing[:, :, :3]
                        except Exception as e:
                            print(f"Overlay error: {e}")
            else:
                # No face detected, fallback to center positioning
                frame_h, frame_w = frame.shape[:2]
                clothing_h, clothing_w = clothing.shape[:2]
                
                target_h = frame_h // 3
                scale = target_h / clothing_h if clothing_h > 0 else 1
                new_w = int(clothing_w * scale)
                new_h = int(clothing_h * scale)
                
                resized_clothing = cv2.resize(clothing, (new_w, new_h))
                
                x = (frame_w - new_w) // 2
                y = frame_h // 4
                
                if resized_clothing.shape[2] == 4:
                    alpha = resized_clothing[:, :, 3] / 255.0
                    alpha_3d = np.stack([alpha, alpha, alpha], axis=2)
                    try:
                        frame[y:y+new_h, x:x+new_w] = ((1 - alpha_3d) * frame[y:y+new_h, x:x+new_w] + alpha_3d * resized_clothing[:, :, :3]).astype(np.uint8)
                    except:
                        pass
                else:
                    try:
                        frame[y:y+new_h, x:x+new_w] = resized_clothing[:, :, :3]
                    except:
                        pass
                        
        except Exception as e:
            print(f"Face detection error: {e}")
        
        # Encode result to base64
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        encoded = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({'processed_frame': encoded})
    
    except Exception as e:
        print(f'Try-on processing error: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Get PORT from environment variable or use 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode, use_reloader=False)
    

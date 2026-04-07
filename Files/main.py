

from flask import Flask, render_template, Response,redirect,request, jsonify
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
    
    # Use proper overlay version - SUPERIMPOSED clothing on your body
    try:
        py_exec = os.path.join(script_dir, '..', '.venv', 'Scripts', 'python.exe')
        if not os.path.exists(py_exec):
            py_exec = sys.executable or 'python'

        tryon_script = os.path.join(script_dir, 'tryOn_stable.py')
        if not os.path.exists(tryon_script):
            return f"Error: Try-on launcher not found: {tryon_script}", 500
        
        print("Launching Proper Overlay Virtual Trial Room...")
        print(f"Python executable: {py_exec}")
        print(f"Try-on script: {tryon_script}")
        print(f"Clothing image: {full_path}")
        
        # Launch from the Files directory so relative imports and logs work reliably.
        subprocess.Popen(
            [py_exec, tryon_script, full_path],
            cwd=script_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
    except Exception as e:
        print(f"Error launching proper overlay version: {e}")
        return f"Error launching virtual try-on: {e}", 500

    return "Virtual try-on started. Check the application window.", 200

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
    """Process video frame with clothing overlay"""
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
        
        # Simple overlay processing (can be enhanced with pose detection)
        # For now, just overlay the clothing image at center
        frame_h, frame_w = frame.shape[:2]
        clothing_h, clothing_w = clothing.shape[:2]
        
        # Resize clothing to fit frame proportionally
        # Make it about 1/3 of frame height
        target_h = frame_h // 3
        scale = target_h / clothing_h
        new_w = int(clothing_w * scale)
        new_h = int(clothing_h * scale)
        
        resized_clothing = cv2.resize(clothing, (new_w, new_h))
        
        # Position at center-top of frame
        x = (frame_w - new_w) // 2
        y = frame_h // 4
        
        # Handle alpha channel if exists
        if resized_clothing.shape[2] == 4:
            # Has alpha channel
            alpha = resized_clothing[:, :, 3] / 255.0
            for c in range(3):
                frame[y:y+new_h, x:x+new_w, c] = (
                    frame[y:y+new_h, x:x+new_w, c] * (1 - alpha) +
                    resized_clothing[:, :, c] * alpha
                )
        else:
            # No alpha, direct overlay
            frame[y:y+new_h, x:x+new_w] = resized_clothing[:, :, :3]
        
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
    

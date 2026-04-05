

from flask import Flask, render_template, Response,redirect,request
from camera import VideoCamera
import os
import sys
import subprocess
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

if __name__ == '__main__':
    # Get PORT from environment variable or use 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode, use_reloader=False)
    

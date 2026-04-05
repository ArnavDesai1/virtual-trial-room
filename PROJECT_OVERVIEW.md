# Virtual Trial Room - Project Overview

## 🎯 Project Summary

**Virtual Trial Room** is a Flask-based web application that enables users to virtually try on clothing items using their webcam. The system uses computer vision (OpenCV, MediaPipe) to detect body features and overlay clothing images onto the user's live video feed.

## 📁 Project Structure

```
Virtual-Trial-Room/
├── Files/                          # Main application directory
│   ├── main.py                     # Flask application entry point
│   ├── camera.py                   # Video camera handler
│   ├── pose_estimator.py           # Pose detection utilities
│   ├── tryOn_proper_overlay.py     # Main virtual try-on implementation
│   ├── tryOn_*.py                  # Multiple try-on algorithm variants
│   ├── templates/                  # HTML templates
│   │   ├── index.html              # Home page
│   │   ├── product.html            # Product listing page
│   │   ├── checkout.html           # Shopping cart/checkout
│   │   └── *.html                  # Other pages
│   ├── static/                     # Static assets
│   │   ├── css/                    # Stylesheets
│   │   ├── js/                     # JavaScript files
│   │   ├── images/                 # Product images
│   │   └── vendor/                 # Third-party libraries
│   └── data/                       # Haar cascade classifiers
├── venv/                           # Python virtual environment
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

## 🚀 Application Status

✅ **Application is RUNNING**

- **Flask Server**: Running on `http://127.0.0.1:5000` (port 5000)
- **Python Version**: 3.12.7
- **Dependencies**: All required packages installed

## 🔧 Key Features

### 1. Web Application (Flask)
- **Home Page** (`/` or `/index`): Landing page with product showcase
- **Product Page** (`/product`): Browse and select clothing items
- **Virtual Try-On** (`/tryon/<file_path>`): Launch virtual try-on window
- **Shopping Cart** (`/cart/<file_path>`): Add items to cart
- **Checkout** (`/checkout`): Complete purchase
- **Video Feed** (`/video_feed`): Live camera stream

### 2. Virtual Try-On System
- **Body Detection**: Uses MediaPipe Pose for body landmark detection
- **Face Detection**: Fallback to Haar Cascade for face detection
- **Clothing Overlay**: Superimposes clothing images onto detected body
- **Real-time Processing**: Live video feed with real-time overlay
- **GUI Interface**: Tkinter-based window for try-on experience

### 3. Technology Stack
- **Backend**: Flask (Python web framework)
- **Computer Vision**: OpenCV, MediaPipe
- **Image Processing**: Pillow (PIL), NumPy
- **Frontend**: HTML, CSS, JavaScript
- **GUI**: Tkinter (for try-on window)

## 📦 Installed Dependencies

- ✅ Flask 3.0.3
- ✅ opencv-python 4.12.0.88
- ✅ opencv-contrib-python 4.11.0.86
- ✅ Pillow 10.4.0
- ✅ NumPy 2.2.6
- ✅ MediaPipe 0.10.14

## 🌐 How to Access

1. **Web Application**: Open your browser and navigate to:
   ```
   http://localhost:5000
   or
   http://127.0.0.1:5000
   ```

2. **Available Routes**:
   - `/` - Home page
   - `/index` - Home page (alternative)
   - `/product` - Product listing
   - `/about` - About page
   - `/contact` - Contact page
   - `/features` - Features page
   - `/checkout` - Shopping cart/checkout
   - `/tryon/<image_path>` - Virtual try-on (requires product image path)
   - `/video_feed` - Live camera stream

## 🎮 How It Works

1. **User browses products** on the web interface
2. **Selects a clothing item** to try on
3. **Clicks "Try On"** button
4. **System launches** a separate Tkinter window (`tryOn_proper_overlay.py`)
5. **Camera activates** and captures live video
6. **Body detection** identifies user's pose/body features
7. **Clothing overlay** is applied in real-time
8. **User sees** themselves wearing the selected clothing

## 🔍 Key Files Explained

### `Files/main.py`
- Flask application with all routes
- Handles product selection, cart management
- Launches virtual try-on subprocess
- Serves HTML templates

### `Files/camera.py`
- `VideoCamera` class for webcam access
- Provides video frames for streaming
- Used by `/video_feed` route

### `Files/tryOn_proper_overlay.py`
- Main virtual try-on implementation
- Uses MediaPipe for pose detection
- Tkinter GUI for user interface
- Real-time clothing overlay algorithm

### `Files/templates/`
- HTML templates for web pages
- Includes modern design variants (`*-modern.html`)
- Responsive layouts

## ⚠️ Important Notes

1. **Camera Access**: The application requires camera access. Make sure:
   - Camera is connected and working
   - Browser/OS permissions allow camera access
   - No other application is using the camera

2. **Try-On Window**: When clicking "Try On", a separate Tkinter window opens
   - This is a desktop application (not in browser)
   - Requires the clothing image path to be valid
   - Uses MediaPipe for body detection

3. **Image Paths**: Product images should be in:
   ```
   Files/static/images/
   ```

4. **Virtual Environment**: The project uses a virtual environment (`venv/`)
   - Dependencies are installed in the venv
   - Make sure to activate it if running manually

## 🐛 Troubleshooting

### If the app doesn't start:
1. Check Python version: `python --version` (should be 3.6+)
2. Verify dependencies: `pip list`
3. Check for port conflicts: Port 5000 should be available

### If try-on doesn't work:
1. Ensure camera is connected
2. Check camera permissions
3. Verify clothing image path exists
4. Check console for error messages

### If dependencies are missing:
```bash
pip install -r requirements.txt
```

## 📝 Next Steps

1. **Test the application**:
   - Open `http://localhost:5000` in your browser
   - Browse products
   - Try the virtual try-on feature

2. **Verify functionality**:
   - Test product browsing
   - Test cart functionality
   - Test virtual try-on with camera
   - Test checkout process

3. **Customize**:
   - Add more products to `static/images/`
   - Modify templates for branding
   - Adjust try-on algorithm parameters

## ✅ Current Status

- ✅ Flask server running on port 5000
- ✅ All dependencies installed
- ✅ Project structure verified
- ✅ Ready for testing

---

**Last Updated**: $(Get-Date)
**Status**: ✅ RUNNING
**Access URL**: http://localhost:5000



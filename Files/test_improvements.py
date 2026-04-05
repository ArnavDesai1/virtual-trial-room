#!/usr/bin/env python3
"""
Test script to verify the improvements in the virtual trial room
"""
import cv2
import numpy as np
import os
import sys

def test_camera_initialization():
    """Test camera initialization and stability"""
    print("Testing camera initialization...")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera initialization failed")
        return False
    
    # Test camera settings
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # Test frame reading
    for i in range(5):
        ret, frame = cap.read()
        if not ret:
            print(f"❌ Frame {i} read failed")
            cap.release()
            return False
        print(f"✓ Frame {i} read successfully: {frame.shape}")
    
    cap.release()
    print("✅ Camera test passed")
    return True

def test_face_detection():
    """Test face detection functionality"""
    print("\nTesting face detection...")
    
    # Create a test image with a simple pattern
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    test_image[:] = (100, 100, 100)  # Gray background
    
    # Add a simple face-like rectangle
    cv2.rectangle(test_image, (200, 150), (400, 350), (255, 255, 255), -1)
    cv2.rectangle(test_image, (250, 200), (300, 250), (0, 0, 0), -1)  # Left eye
    cv2.rectangle(test_image, (350, 200), (400, 250), (0, 0, 0), -1)  # Right eye
    cv2.rectangle(test_image, (300, 300), (350, 320), (0, 0, 0), -1)  # Mouth
    
    # Test face detection
    gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) > 0:
        print("✅ Face detection test passed")
        return True
    else:
        print("❌ Face detection test failed")
        return False

def test_clothing_overlay():
    """Test clothing overlay functionality"""
    print("\nTesting clothing overlay...")
    
    # Create a test body image
    body_image = np.zeros((480, 640, 3), dtype=np.uint8)
    body_image[:] = (200, 200, 200)  # Light gray background
    
    # Create a simple clothing image
    clothing = np.zeros((100, 80, 4), dtype=np.uint8)
    clothing[:, :, 0] = 255  # Red
    clothing[:, :, 3] = 128  # Semi-transparent
    
    # Test overlay function
    try:
        # Simple overlay test
        start_x, start_y = 200, 150
        end_x = min(start_x + 80, 640)
        end_y = min(start_y + 100, 480)
        
        if end_x > start_x and end_y > start_y:
            body_region = body_image[start_y:end_y, start_x:end_x]
            clothing_region = clothing[:end_y-start_y, :end_x-start_x]
            
            if body_region.shape == clothing_region.shape:
                print("✅ Clothing overlay test passed")
                return True
    
    except Exception as e:
        print(f"❌ Clothing overlay test failed: {e}")
        return False
    
    print("❌ Clothing overlay test failed")
    return False

def test_mediapipe_availability():
    """Test if mediapipe is available"""
    print("\nTesting MediaPipe availability...")
    
    try:
        import mediapipe as mp
        print("✅ MediaPipe is available")
        return True
    except ImportError:
        print("⚠️ MediaPipe not available - will use face detection fallback")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Virtual Trial Room Improvements")
    print("=" * 50)
    
    tests = [
        test_camera_initialization,
        test_face_detection,
        test_clothing_overlay,
        test_mediapipe_availability
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The improvements should work correctly.")
    else:
        print("⚠️ Some tests failed. Check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3

import sys

def check_mediapipe():
    """Check MediaPipe installation"""
    try:
        import mediapipe as mp
        print("✓ MediaPipe installed and working")
        return True
    except ImportError as e:
        print(f"✗ MediaPipe not available: {e}")
        return False

def check_opencv():
    """Check OpenCV installation"""
    try:
        import cv2
        print(f"✓ OpenCV installed: {cv2.__version__}")
        return True
    except ImportError as e:
        print(f"✗ OpenCV not available: {e}")
        return False

def check_sklearn():
    """Check scikit-learn installation"""
    try:
        import sklearn
        print(f"✓ scikit-learn installed: {sklearn.__version__}")
        return True
    except ImportError as e:
        print(f"✗ scikit-learn not available: {e}")
        return False

def main():
    """Check all required AI models and libraries"""
    
    print("Checking AI models and dependencies...")
    
    checks = [
        check_mediapipe(),
        check_opencv(),
        check_sklearn()
    ]
    
    if all(checks):
        print("✓ All AI dependencies are ready!")
        return True
    else:
        print("✗ Some dependencies are missing")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
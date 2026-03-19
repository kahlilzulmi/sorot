"""
Tobii Ghost Detector
====================

Detects and interfaces with Tobii Ghost eye tracking hardware.

🔒 PRIVATE REPOSITORY - Restricted Access
This code should NOT be included in public repository.
"""

def is_tobii_overlay_running():
    """Check if Tobii Ghost overlay (SSOverlay.exe) is running."""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == 'ssoverlay.exe':
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except ImportError:
        # psutil not installed, try Windows tasklist command
        try:
            import subprocess
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq SSOverlay.exe'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return 'SSOverlay.exe' in result.stdout
        except:
            # Cannot check, assume it might be running
            print("Warning: Cannot check if Tobii Ghost overlay is running (install psutil for better detection)")
            return None  # Unknown state


class TobiiGazeCapture:
    """
    Captures gaze data from Tobii Ghost via OBS virtual camera
    
    🔒 This class contains proprietary Tobii integration code
    """
    
    def __init__(self, camera_index=0):
        """
        Initialize Tobii gaze capture
        
        Args:
            camera_index: OBS virtual camera index (default: 0)
        """
        import cv2
        self.camera_index = camera_index
        self.cap = None
        self.gaze_data = []
        
    def start_capture(self):
        """Start capturing from OBS virtual camera"""
        import cv2
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open virtual camera at index {self.camera_index}")
        return True
    
    def get_gaze_position(self, frame_number):
        """
        Extract gaze position from current frame
        
        🔒 Proprietary algorithm for Tobii Ghost gaze extraction
        
        Returns:
            (x, y, confidence) or (None, None, 0) if no gaze detected
        """
        if self.cap is None or not self.cap.isOpened():
            return (None, None, 0)
        
        ret, frame = self.cap.read()
        if not ret:
            return (None, None, 0)
        
        # 🔒 Proprietary Tobii Ghost gaze extraction algorithm
        # This is where the advanced detection happens
        # Replace with actual Tobii SDK or computer vision detection
        
        # Placeholder implementation
        # In real version, this would use Tobii-specific detection
        import cv2
        import numpy as np
        
        # Example: detect bright spot (gaze cursor) in frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        
        moments = cv2.moments(thresh)
        if moments["m00"] > 0:
            cx = int(moments["m10"] / moments["m00"])
            cy = int(moments["m01"] / moments["m00"])
            confidence = min(moments["m00"] / 1000.0, 1.0)
            return (cx, cy, confidence)
        
        return (None, None, 0)
    
    def stop_capture(self):
        """Stop capturing and release camera"""
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def __del__(self):
        self.stop_capture()


# Additional Tobii-specific utilities

def check_tobii_hardware():
    """
    Check if Tobii Ghost hardware is connected and accessible
    
    Returns:
        dict with status information
    """
    status = {
        'overlay_running': is_tobii_overlay_running(),
        'hardware_detected': False,
        'sdk_available': False
    }
    
    # Check for Tobii SDK (if using official SDK)
    try:
        # Example: import tobii_research
        # status['sdk_available'] = True
        pass
    except ImportError:
        pass
    
    return status


def calibrate_tobii(display_size=(1920, 1080)):
    """
    Run Tobii calibration routine
    
    🔒 Proprietary calibration procedure
    """
    # Placeholder for actual calibration
    print("To calibrate Tobii Ghost, please use the Tobii Ghost Control application")
    return False

def is_tobii_overlay_running():
    """Check if Tobii Ghost overlay (SSOverlay.exe) is running."""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == 'ssoverlay.exe':
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except ImportError:
        # psutil not installed, try Windows tasklist command
        try:
            import subprocess
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq SSOverlay.exe'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return 'SSOverlay.exe' in result.stdout
        except:
            # Cannot check, assume it might be running
            print("Warning: Cannot check if Tobii Ghost overlay is running (install psutil for better detection)")
            return None  # Unknown state
        
def check_recording_devices():
    """Check if OBS, Tobii Ghost overlay, and eye tracking devices are available."""
    use_mouse_fallback = True
    device_status = {
        'obs_available': False,
        'obs_connected': False,
        'tobii_overlay_running': False,
        'eye_tracker_detected': False,
        'use_mouse_fallback': True,
        'warnings': []
    }
    
    # Check if Tobii Ghost overlay is running
    tobii_status = is_tobii_overlay_running()
    if tobii_status is True:
        device_status['tobii_overlay_running'] = True
    elif tobii_status is False:
        device_status['warnings'].append('Tobii Ghost overlay (SSOverlay.exe) is not running')
    elif tobii_status is None:
        device_status['warnings'].append('Cannot verify if Tobii Ghost overlay is running')
    
    # Check if OBS is available and connectable
    if OBS_AVAILABLE:
        try:
            test_controller = OBSController()
            if test_controller.connect():
                device_status['obs_available'] = True
                device_status['obs_connected'] = True
                test_controller.disconnect()
                
                # Only disable mouse fallback if BOTH OBS and Tobii are ready
                if device_status['tobii_overlay_running']:
                    use_mouse_fallback = False
                    device_status['use_mouse_fallback'] = False
                else:
                    device_status['warnings'].append('OBS is ready but Tobii Ghost overlay is not running')
        except Exception as e:
            print(f"OBS check failed: {e}")
            device_status['warnings'].append(f'OBS connection failed: {str(e)}')
    
    # Check if virtual camera/eye tracker is accessible
    try:
        test_cap = cv2.VideoCapture(VIRTUAL_CAMERA_INDEX)
        if test_cap.isOpened():
            device_status['eye_tracker_detected'] = True
            test_cap.release()
    except:
        pass
    
    # Determine message based on status
    if not use_mouse_fallback:
        message = 'OBS and Tobii Ghost overlay are ready for eye tracking'
    elif device_status['obs_connected'] and not device_status['tobii_overlay_running']:
        message = 'Tobii Ghost overlay not detected. Mouse tracking will be used.'
    elif device_status['tobii_overlay_running'] and not device_status['obs_connected']:
        message = 'OBS not connected. Mouse tracking will be used.'
    else:
        message = 'Mouse tracking fallback will be used'
    
    return jsonify({
        'success': True,
        'use_mouse_fallback': use_mouse_fallback,
        'device_status': device_status,
        'message': message
    })

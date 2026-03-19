"""
OBS Integration Module
======================

OBS WebSocket control for virtual camera and recording.

🔒 PRIVATE REPOSITORY - Restricted Access
"""

def is_obs_running():
    """Check if OBS Studio is running"""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name'].lower()
                if 'obs' in proc_name or 'obs64.exe' in proc_name or 'obs32.exe' in proc_name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except ImportError:
        # Try connecting to OBS WebSocket as fallback
        try:
            from obswebsocket import obsws
            ws = obsws("localhost", 4455, "")
            ws.connect()
            ws.disconnect()
            return True
        except:
            return False


class OBSController:
    """
    Controls OBS Studio via WebSocket
    
    🔒 This class provides OBS automation for eye tracking sessions
    """
    
    def __init__(self, host="localhost", port=4455, password=""):
        """
        Initialize OBS WebSocket connection
        
        Args:
            host: OBS WebSocket host
            port: OBS WebSocket port (default: 4455)
            password: OBS WebSocket password
        """
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        self.connected = False
    
    def connect(self):
        """Connect to OBS WebSocket"""
        try:
            from obswebsocket import obsws, requests as obs_requests
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            self.connected = True
            print(f"✅ Connected to OBS at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to OBS: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from OBS"""
        if self.ws and self.connected:
            try:
                self.ws.disconnect()
                self.connected = False
                print("Disconnected from OBS")
            except:
                pass
    
    def start_virtual_camera(self):
        """Start OBS virtual camera"""
        if not self.connected:
            raise RuntimeError("Not connected to OBS")
        
        try:
            from obswebsocket import requests as obs_requests
            self.ws.call(obs_requests.StartVirtualCam())
            print("✅ OBS Virtual Camera started")
            return True
        except Exception as e:
            print(f"❌ Failed to start virtual camera: {e}")
            return False
    
    def stop_virtual_camera(self):
        """Stop OBS virtual camera"""
        if not self.connected:
            return False
        
        try:
            from obswebsocket import requests as obs_requests
            self.ws.call(obs_requests.StopVirtualCam())
            print("Virtual camera stopped")
            return True
        except Exception as e:
            print(f"Failed to stop virtual camera: {e}")
            return False
    
    def is_virtual_camera_active(self):
        """Check if virtual camera is active"""
        if not self.connected:
            return False
        
        try:
            from obswebsocket import requests as obs_requests
            response = self.ws.call(obs_requests.GetVirtualCamStatus())
            return response.getOutputActive()
        except:
            return False
    
    def start_recording(self, output_path=None):
        """Start OBS recording"""
        if not self.connected:
            raise RuntimeError("Not connected to OBS")
        
        try:
            from obswebsocket import requests as obs_requests
            self.ws.call(obs_requests.StartRecord())
            print("✅ OBS recording started")
            return True
        except Exception as e:
            print(f"❌ Failed to start recording: {e}")
            return False
    
    def stop_recording(self):
        """Stop OBS recording"""
        if not self.connected:
            return False
        
        try:
            from obswebsocket import requests as obs_requests
            response = self.ws.call(obs_requests.StopRecord())
            output_path = response.getOutputPath() if hasattr(response, 'getOutputPath') else None
            print(f"Recording stopped. Saved to: {output_path}")
            return output_path
        except Exception as e:
            print(f"Failed to stop recording: {e}")
            return None
    
    def get_recording_status(self):
        """Get current recording status"""
        if not self.connected:
            return {'active': False, 'paused': False}
        
        try:
            from obswebsocket import requests as obs_requests
            response = self.ws.call(obs_requests.GetRecordStatus())
            return {
                'active': response.getOutputActive(),
                'paused': response.getOutputPaused() if hasattr(response, 'getOutputPaused') else False
            }
        except:
            return {'active': False, 'paused': False}
    
    def get_output_path(self):
        """Get OBS recording output path"""
        if not self.connected:
            return None
        
        try:
            from obswebsocket import requests as obs_requests
            response = self.ws.call(obs_requests.GetRecordDirectory())
            return response.getRecordDirectory() if hasattr(response, 'getRecordDirectory') else None
        except:
            return None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()


# Utility functions

def check_obs_virtual_camera(camera_index=0):
    """
    Check if OBS virtual camera is available at given index
    
    Returns:
        (available, resolution) or (False, None)
    """
    import cv2
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        return (False, None)
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    cap.release()
    
    return (True, (width, height))


def auto_connect_obs():
    """
    Automatically connect to OBS with common settings
    
    Returns:
        OBSController instance or None
    """
    # Try common configurations
    configs = [
        ("localhost", 4455, ""),
        ("127.0.0.1", 4455, ""),
        ("localhost", 4444, ""),  # Old default port
    ]
    
    for host, port, password in configs:
        controller = OBSController(host, port, password)
        if controller.connect():
            return controller
    
    return None

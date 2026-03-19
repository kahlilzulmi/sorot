"""
Tobii Pro Plugin - Advanced Eye Tracking Features
==================================================

This plugin provides Tobii Ghost hardware integration and advanced
eye tracking algorithms for verified research use.

PRIVATE REPOSITORY - Restricted Access
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# Plugin availability flag
PLUGIN_LOADED = True

# Import main components
try:
    from .tobii_detector import is_tobii_overlay_running, TobiiGazeCapture
    from .obs_integration import OBSController, is_obs_running
    from .advanced_algorithms import AdvancedGazeProcessor
    
    __all__ = [
        'is_tobii_overlay_running',
        'TobiiGazeCapture',
        'OBSController',
        'is_obs_running',
        'AdvancedGazeProcessor',
        'PLUGIN_LOADED'
    ]
    
except ImportError as e:
    print(f"Warning: Tobii Pro Plugin components not fully loaded: {e}")
    PLUGIN_LOADED = False
    __all__ = ['PLUGIN_LOADED']


def get_plugin_info():
    """Return plugin information"""
    return {
        'name': 'Tobii Pro Plugin',
        'version': __version__,
        'loaded': PLUGIN_LOADED,
        'features': [
            'Tobii Ghost overlay detection',
            'OBS virtual camera integration',
            'Advanced gaze processing algorithms',
            'Hardware-optimized tracking'
        ]
    }


def check_requirements():
    """Check if all plugin dependencies are installed"""
    requirements = {
        'psutil': False,
        'obswebsocket': False,
        'cv2': False
    }
    
    try:
        import psutil
        requirements['psutil'] = True
    except ImportError:
        pass
    
    try:
        from obswebsocket import obsws
        requirements['obswebsocket'] = True
    except ImportError:
        pass
    
    try:
        import cv2
        requirements['cv2'] = True
    except ImportError:
        pass
    
    return requirements

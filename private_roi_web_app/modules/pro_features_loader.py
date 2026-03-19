"""
Pro Features Loader
===================

Detects and loads the Tobii Pro Plugin if available.
Falls back to open-source features if plugin not installed.

This file goes in PUBLIC REPO - safe to share
"""

import sys

# Try to import Tobii Pro Plugin
try:
    import tobii_pro_plugin
    from tobii_pro_plugin import (
        is_tobii_overlay_running,
        TobiiGazeCapture,
        OBSController,
        is_obs_running,
        AdvancedGazeProcessor
    )
    TOBII_PRO_AVAILABLE = True
    print("=" * 60)
    print("✅ Tobii Pro Plugin detected")
    print(f"   Version: {tobii_pro_plugin.__version__}")
    plugin_info = tobii_pro_plugin.get_plugin_info()
    print(f"   Features enabled:")
    for feature in plugin_info['features']:
        print(f"     • {feature}")
    print("=" * 60)
    
except ImportError:
    TOBII_PRO_AVAILABLE = False
    print("=" * 60)
    print("ℹ️  Running in Open Source Mode")
    print("   Features available:")
    print("     • Mouse gaze tracking")
    print("     • Generic webcam eye tracking")
    print("     • ROI editing & scene management")
    print("     • CSV import/export")
    print("     • Report generation")
    print("")
    print("   Advanced features (Tobii Pro Plugin) not detected.")
    print("   For verified researchers: install tobii-pro-plugin")
    print("=" * 60)
    
    # Provide fallback implementations
    def is_tobii_overlay_running():
        """Fallback: always returns None (unknown)"""
        return None
    
    def is_obs_running():
        """Fallback: always returns False"""
        return False
    
    class OBSController:
        """Fallback: dummy OBS controller"""
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("OBS integration requires Tobii Pro Plugin")
    
    class TobiiGazeCapture:
        """Fallback: dummy Tobii capture"""
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("Tobii Ghost integration requires Tobii Pro Plugin")
    
    class AdvancedGazeProcessor:
        """Fallback: dummy advanced processor"""
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("Advanced algorithms require Tobii Pro Plugin")


def get_available_features():
    """
    Returns dictionary of available features based on plugin status
    """
    base_features = {
        'mouse_tracking': True,
        'generic_webcam': True,
        'roi_editing': True,
        'scene_management': True,
        'csv_import_export': True,
        'basic_reports': True,
        'video_playback': True,
        'basic_heatmaps': True,
    }
    
    pro_features = {
        'tobii_ghost': TOBII_PRO_AVAILABLE,
        'obs_integration': TOBII_PRO_AVAILABLE,
        'advanced_tracking': TOBII_PRO_AVAILABLE,
        'hardware_optimized': TOBII_PRO_AVAILABLE,
    }
    
    return {**base_features, **pro_features}


def check_tobii_requirements():
    """
    Check if Tobii features can be used
    Returns: (available, message)
    """
    if not TOBII_PRO_AVAILABLE:
        return (False, "Tobii Pro Plugin not installed. Contact administrator for access.")
    
    # Check if plugin is fully functional
    requirements = tobii_pro_plugin.check_requirements()
    
    missing = [name for name, installed in requirements.items() if not installed]
    
    if missing:
        return (False, f"Missing dependencies: {', '.join(missing)}")
    
    return (True, "Tobii features available")


# Export everything
__all__ = [
    'TOBII_PRO_AVAILABLE',
    'is_tobii_overlay_running',
    'is_obs_running',
    'OBSController',
    'TobiiGazeCapture',
    'AdvancedGazeProcessor',
    'get_available_features',
    'check_tobii_requirements'
]

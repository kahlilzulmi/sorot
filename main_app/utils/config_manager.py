"""
Configuration Manager Module

Handles loading, saving, and validating configuration settings.
Supports JSON format for easy readability and editing.

Author: Kahlil Gibran Al Zulmi
NRP: 5049221015
Medical Technology Study Program - ITS
"""

import json
import os
from datetime import datetime


def get_default_config():
    """
    Get default configuration settings.
    
    Returns:
        dict: Default configuration dictionary
    """
    return {
        "version": "1.0.0",
        "language": "en",
        "first_run": True,
        "system_check": {
            "completed": False,
            "last_check": None,
            "windows_version": None,
            "tobii_connected": False,
            "obs_configured": False,
            "ram_available_gb": 0
        },
        "detection": {
            "default_method": "hough",
            "processing_mode": "auto",
            "chunk_size_frames": 1000,
            "kalman_process_noise": 0.1,
            "kalman_measurement_noise": 2.0,
            "hough_param1": 50,
            "hough_param2": 13,
            "hough_min_radius": 73,
            "hough_max_radius": 75,
            "contour_threshold": 200,
            "color_lower_hsv": [0, 0, 200],
            "color_upper_hsv": [180, 30, 255],
            "blob_min_area": 100,
            "blob_max_area": 1000
        },
        "game": {
            "camera_id": 0,
            "dwell_time_seconds": 2.0,
            "exit_hover_seconds": 3.0,
            "debug_mode_key": "F12",
            "question_bank": "assets/templates/questions_template.xlsx",
            "dark_mode": True,
            "fullscreen": True,
            "adaptive_params": True,
            "adaptation_rate": 0.1
        },
        "stimulus": {
            "default_protocol": "standard",
            "quality_threshold": 0.7,
            "adaptation_enabled": True,
            "target_size_range": [15, 40],
            "fixation_duration": 5,
            "smooth_pursuit_duration": 10,
            "saccade_duration_per_point": 3,
            "preparation_duration": 3
        },
        "ui": {
            "theme": "light",
            "window_width": 1024,
            "window_height": 768,
            "font_family": "Arial",
            "font_size": 12
        },
        "paths": {
            "database_dir": "Database",
            "sessions_dir": "Sessions",
            "logs_dir": "Logs",
            "assets_dir": "assets"
        },
        "obs": {
            "virtual_camera_name": "OBS Virtual Camera",
            "scene_template_path": "assets/templates/obs_scene.json",
            "auto_start": False
        },
        "report": {
            "include_branding": True,
            "header_image": "assets/icons/logo.png",
            "footer_text": "Medical Technology Study Program - ITS",
            "author_name": "Kahlil Gibran Al Zulmi",
            "supervisor": "Prof. Dr. Ir. Adhi Dharma Wibawa, S.T., M.T.",
            "co_advisor": "dr. Zain Budi Syulthoni, Sp.KJ."
        }
    }


def load_config(config_path="config.json"):
    """
    Load configuration from JSON file.
    If file doesn't exist, creates default config.
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    if not os.path.exists(config_path):
        # Create default config
        config = get_default_config()
        save_config(config, config_path)
        return config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate and merge with defaults (in case new fields were added)
        config = validate_config(config)
        return config
        
    except Exception as e:
        print(f"Error loading config: {e}")
        print("Using default configuration.")
        return get_default_config()


def save_config(config_dict, config_path="config.json"):
    """
    Save configuration to JSON file.
    
    Args:
        config_dict (dict): Configuration dictionary
        config_path (str): Path to configuration file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def validate_config(config_dict):
    """
    Validate configuration and merge with defaults for missing fields.
    
    Args:
        config_dict (dict): Configuration dictionary to validate
        
    Returns:
        dict: Validated and completed configuration
    """
    default_config = get_default_config()
    
    # Merge configurations (add missing keys from default)
    validated_config = _merge_dicts(default_config, config_dict)
    
    return validated_config


def _merge_dicts(default, custom):
    """
    Recursively merge two dictionaries.
    Custom values override defaults.
    
    Args:
        default (dict): Default dictionary
        custom (dict): Custom dictionary with overrides
        
    Returns:
        dict: Merged dictionary
    """
    result = default.copy()
    
    for key, value in custom.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def update_config_value(config_path, section, key, value):
    """
    Update a specific configuration value.
    
    Args:
        config_path (str): Path to configuration file
        section (str): Configuration section (e.g., 'game', 'detection')
        key (str): Configuration key within section
        value: New value
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        config = load_config(config_path)
        
        if section in config:
            config[section][key] = value
        else:
            config[section] = {key: value}
        
        return save_config(config, config_path)
    except Exception as e:
        print(f"Error updating config: {e}")
        return False


def get_config_value(config_path, section, key, default=None):
    """
    Get a specific configuration value.
    
    Args:
        config_path (str): Path to configuration file
        section (str): Configuration section
        key (str): Configuration key
        default: Default value if not found
        
    Returns:
        Value from configuration or default
    """
    try:
        config = load_config(config_path)
        return config.get(section, {}).get(key, default)
    except Exception:
        return default


def mark_system_check_complete(config_path, check_results):
    """
    Mark system check as complete and save results.
    
    Args:
        config_path (str): Path to configuration file
        check_results (dict): System check results
        
    Returns:
        bool: True if successful
    """
    config = load_config(config_path)
    config["first_run"] = False
    config["system_check"]["completed"] = True
    config["system_check"]["last_check"] = datetime.now().isoformat()
    config["system_check"].update(check_results)
    
    return save_config(config, config_path)


def reset_to_defaults(config_path):
    """
    Reset configuration to default values.
    
    Args:
        config_path (str): Path to configuration file
        
    Returns:
        bool: True if successful
    """
    config = get_default_config()
    return save_config(config, config_path)


if __name__ == "__main__":
    # Test configuration management
    test_config_path = "test_config.json"
    
    print("Testing configuration manager...")
    
    # Test 1: Create default config
    print("\n1. Creating default configuration...")
    config = load_config(test_config_path)
    print(f"   Language: {config['language']}")
    print(f"   Dwell time: {config['game']['dwell_time_seconds']}s")
    
    # Test 2: Update value
    print("\n2. Updating dwell time to 3.0 seconds...")
    update_config_value(test_config_path, "game", "dwell_time_seconds", 3.0)
    new_value = get_config_value(test_config_path, "game", "dwell_time_seconds")
    print(f"   New dwell time: {new_value}s")
    
    # Test 3: Mark system check complete
    print("\n3. Marking system check as complete...")
    mark_system_check_complete(test_config_path, {
        "windows_version": "Windows 11",
        "tobii_connected": True,
        "obs_configured": True,
        "ram_available_gb": 16
    })
    config = load_config(test_config_path)
    print(f"   System check completed: {config['system_check']['completed']}")
    print(f"   Windows: {config['system_check']['windows_version']}")
    
    # Test 4: Reset to defaults
    print("\n4. Resetting to defaults...")
    reset_to_defaults(test_config_path)
    config = load_config(test_config_path)
    print(f"   Dwell time back to: {config['game']['dwell_time_seconds']}s")
    
    # Cleanup
    if os.path.exists(test_config_path):
        os.remove(test_config_path)
    
    print("\nConfiguration manager test complete!")

"""
System Check Module

Verifies system requirements for Eye Tracker Research Software:
- Windows 10/11
- Tobii Eye Tracker (process/service + USB device)
- OBS Studio installation
- Available RAM (minimum 8 GB)

Author: Kahlil Gibran Al Zulmi
NRP: 5049221015
Medical Technology Study Program - ITS
"""

import os
import platform
import subprocess
import psutil
import re
from pathlib import Path


def check_windows_version():
    """
    Check if running on Windows 10 or 11.
    
    Returns:
        dict: {
            'success': bool,
            'version': str,
            'message': str
        }
    """
    try:
        system = platform.system()
        if system != "Windows":
            return {
                'success': False,
                'version': system,
                'message': f"Not running on Windows (detected: {system})"
            }
        
        # Get Windows version
        version = platform.version()
        release = platform.release()
        
        # Windows 10 is version 10.0, Windows 11 is also 10.0 but build >= 22000
        if release == "10":
            build = int(platform.version().split('.')[2])
            if build >= 22000:
                win_version = "Windows 11"
            else:
                win_version = "Windows 10"
        else:
            win_version = f"Windows {release}"
        
        # Check if it's Windows 10 or 11
        if "Windows 10" in win_version or "Windows 11" in win_version:
            return {
                'success': True,
                'version': win_version,
                'message': f"{win_version} detected"
            }
        else:
            return {
                'success': False,
                'version': win_version,
                'message': f"{win_version} detected. Windows 10 or 11 required."
            }
            
    except Exception as e:
        return {
            'success': False,
            'version': 'Unknown',
            'message': f"Error checking Windows version: {str(e)}"
        }


def check_tobii_processes():
    """
    Check if Tobii-related processes or services are running.
    
    Returns:
        dict: {
            'success': bool,
            'processes': list,
            'message': str
        }
    """
    try:
        tobii_processes = []
        tobii_keywords = [
            'tobii', 'eyetracker', 'ghost', 'experience',
            'TobiiService', 'TobiiGhost', 'SSOverlay'
        ]
        
        # Check running processes
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                proc_name = proc.info['name'] or ''
                proc_exe = proc.info['exe'] or ''
                
                # Check if any Tobii keyword is in process name or executable path
                for keyword in tobii_keywords:
                    if keyword.lower() in proc_name.lower() or keyword.lower() in proc_exe.lower():
                        tobii_processes.append({
                            'name': proc_name,
                            'exe': proc_exe
                        })
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if tobii_processes:
            return {
                'success': True,
                'processes': tobii_processes,
                'message': f"Found {len(tobii_processes)} Tobii process(es) running"
            }
        else:
            return {
                'success': False,
                'processes': [],
                'message': "No Tobii processes detected. Please start Tobii Experience/Ghost."
            }
            
    except Exception as e:
        return {
            'success': False,
            'processes': [],
            'message': f"Error checking Tobii processes: {str(e)}"
        }


def check_tobii_usb():
    """
    Check if Tobii Eye Tracker is connected via USB.
    Uses Windows Device Manager query.
    
    Returns:
        dict: {
            'success': bool,
            'devices': list,
            'message': str
        }
    """
    try:
        # Use WMIC to query USB devices
        result = subprocess.run(
            ['wmic', 'path', 'Win32_PnPEntity', 'where', 
             '"DeviceID like \'%USB%\'"', 'get', 'Name,DeviceID'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {
                'success': False,
                'devices': [],
                'message': "Could not query USB devices"
            }
        
        # Look for Tobii in device list
        tobii_devices = []
        lines = result.stdout.split('\n')
        
        for line in lines:
            if 'tobii' in line.lower() or 'eye' in line.lower():
                tobii_devices.append(line.strip())
        
        if tobii_devices:
            return {
                'success': True,
                'devices': tobii_devices,
                'message': f"Found {len(tobii_devices)} Tobii device(s) connected"
            }
        else:
            return {
                'success': False,
                'devices': [],
                'message': "No Tobii USB devices detected. Please connect your eye tracker."
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'devices': [],
            'message': "USB device check timed out"
        }
    except Exception as e:
        return {
            'success': False,
            'devices': [],
            'message': f"Error checking USB devices: {str(e)}"
        }


def check_tobii_installed():
    """
    Combined Tobii check: processes and USB connection.
    
    Returns:
        dict: {
            'success': bool,
            'process_check': dict,
            'usb_check': dict,
            'message': str
        }
    """
    process_check = check_tobii_processes()
    usb_check = check_tobii_usb()
    
    # Consider success if either process is running OR device is connected
    overall_success = process_check['success'] or usb_check['success']
    
    if overall_success:
        if process_check['success'] and usb_check['success']:
            message = "Tobii software running and device connected"
        elif process_check['success']:
            message = "Tobii software running (device check inconclusive)"
        else:
            message = "Tobii device detected (software may need to be started)"
    else:
        message = "Tobii not detected. Please install Tobii Experience/Ghost and connect device."
    
    return {
        'success': overall_success,
        'process_check': process_check,
        'usb_check': usb_check,
        'message': message
    }


def check_obs_installed():
    """
    Check if OBS Studio is installed and running.
    
    Returns:
        dict: {
            'success': bool,
            'installed': bool,
            'running': bool,
            'path': str,
            'message': str
        }
    """
    try:
        # Common OBS installation paths
        common_paths = [
            r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
            r"C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe",
            r"C:\Program Files\obs-studio\bin\obs64.exe",
        ]
        
        # Check if OBS is installed
        obs_path = None
        for path in common_paths:
            if os.path.exists(path):
                obs_path = path
                break
        
        # Also check registry for installation path
        if not obs_path:
            try:
                result = subprocess.run(
                    ['reg', 'query', r'HKEY_LOCAL_MACHINE\SOFTWARE\OBS Studio'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # Parse registry output for installation path
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'InstallPath' in line or 'Path' in line:
                            # Extract path from registry output
                            match = re.search(r'REG_SZ\s+(.+)', line)
                            if match:
                                potential_path = match.group(1).strip()
                                obs_exe = os.path.join(potential_path, 'bin', '64bit', 'obs64.exe')
                                if os.path.exists(obs_exe):
                                    obs_path = obs_exe
                                    break
            except:
                pass
        
        installed = obs_path is not None
        
        # Check if OBS is running
        running = False
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'obs' in proc.info['name'].lower():
                    running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if installed and running:
            return {
                'success': True,
                'installed': True,
                'running': True,
                'path': obs_path,
                'message': "OBS Studio installed and running"
            }
        elif installed:
            return {
                'success': True,
                'installed': True,
                'running': False,
                'path': obs_path,
                'message': "OBS Studio installed (not currently running)"
            }
        else:
            return {
                'success': False,
                'installed': False,
                'running': False,
                'path': None,
                'message': "OBS Studio not found. Please install from obsproject.com"
            }
            
    except Exception as e:
        return {
            'success': False,
            'installed': False,
            'running': False,
            'path': None,
            'message': f"Error checking OBS: {str(e)}"
        }


def check_ram_available():
    """
    Check available RAM in the system.
    
    Returns:
        dict: {
            'success': bool,
            'total_gb': float,
            'available_gb': float,
            'percent_used': float,
            'message': str
        }
    """
    try:
        # Get memory info
        mem = psutil.virtual_memory()
        
        total_gb = mem.total / (1024 ** 3)  # Convert to GB
        available_gb = mem.available / (1024 ** 3)
        percent_used = mem.percent
        
        # Check if meets minimum requirement (8 GB)
        min_required_gb = 8
        success = total_gb >= min_required_gb
        
        if success:
            message = f"{total_gb:.1f} GB total RAM ({available_gb:.1f} GB available)"
        else:
            message = f"Only {total_gb:.1f} GB RAM. Minimum {min_required_gb} GB recommended."
        
        return {
            'success': success,
            'total_gb': round(total_gb, 2),
            'available_gb': round(available_gb, 2),
            'percent_used': round(percent_used, 1),
            'message': message
        }
        
    except Exception as e:
        return {
            'success': False,
            'total_gb': 0,
            'available_gb': 0,
            'percent_used': 0,
            'message': f"Error checking RAM: {str(e)}"
        }


def run_full_system_check():
    """
    Run all system checks and return comprehensive results.
    
    Returns:
        dict: {
            'windows': dict,
            'tobii': dict,
            'obs': dict,
            'ram': dict,
            'overall_success': bool,
            'summary': str
        }
    """
    print("Running system check...")
    print("=" * 60)
    
    # Run all checks
    windows_check = check_windows_version()
    print(f"✓ Windows: {windows_check['message']}")
    
    tobii_check = check_tobii_installed()
    print(f"{'✓' if tobii_check['success'] else '✗'} Tobii: {tobii_check['message']}")
    
    obs_check = check_obs_installed()
    print(f"{'✓' if obs_check['success'] else '✗'} OBS: {obs_check['message']}")
    
    ram_check = check_ram_available()
    print(f"{'✓' if ram_check['success'] else '✗'} RAM: {ram_check['message']}")
    
    print("=" * 60)
    
    # Determine overall success
    critical_checks = [windows_check['success'], ram_check['success']]
    optional_checks = [tobii_check['success'], obs_check['success']]
    
    # All critical checks must pass
    overall_success = all(critical_checks)
    
    # Generate summary
    if overall_success:
        if all(optional_checks):
            summary = "All system requirements met. Ready to use!"
        else:
            missing = []
            if not tobii_check['success']:
                missing.append("Tobii Eye Tracker")
            if not obs_check['success']:
                missing.append("OBS Studio")
            summary = f"Core requirements met. Optional: {', '.join(missing)}"
    else:
        failed = []
        if not windows_check['success']:
            failed.append("Windows 10/11")
        if not ram_check['success']:
            failed.append("8 GB RAM")
        summary = f"Requirements not met: {', '.join(failed)}"
    
    print(f"\nSummary: {summary}\n")
    
    return {
        'windows': windows_check,
        'tobii': tobii_check,
        'obs': obs_check,
        'ram': ram_check,
        'overall_success': overall_success,
        'summary': summary
    }


def get_system_check_for_config():
    """
    Get system check results in format suitable for config file.
    
    Returns:
        dict: Simplified check results for config
    """
    results = run_full_system_check()
    
    return {
        'windows_version': results['windows'].get('version', 'Unknown'),
        'tobii_connected': results['tobii']['success'],
        'obs_configured': results['obs']['success'] and results['obs'].get('running', False),
        'ram_available_gb': results['ram'].get('total_gb', 0)
    }


if __name__ == "__main__":
    # Test system check
    print("Eye Tracker System Check")
    print("=" * 60)
    print()
    
    results = run_full_system_check()
    
    print("\nDetailed Results:")
    print("-" * 60)
    print(f"Windows: {results['windows']['version']}")
    print(f"Tobii Process Check: {results['tobii']['process_check']['message']}")
    print(f"Tobii USB Check: {results['tobii']['usb_check']['message']}")
    print(f"OBS Installed: {results['obs']['installed']}")
    print(f"OBS Running: {results['obs']['running']}")
    print(f"RAM Total: {results['ram']['total_gb']} GB")
    print(f"RAM Available: {results['ram']['available_gb']} GB")
    print(f"RAM Usage: {results['ram']['percent_used']}%")
    print("-" * 60)
    
    if results['overall_success']:
        print("\n✓ System check passed!")
    else:
        print("\n✗ System check failed. Please address the issues above.")

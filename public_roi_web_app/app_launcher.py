"""
Standalone launcher for the Advertisement Eye Tracking application.
This wraps the Flask app and auto-opens the browser.
"""

import os
import sys
import webbrowser
import threading
import time

def open_browser():
    """Open browser after a short delay."""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://localhost:5000')

def main():
    """Main launcher function."""
    # Set up working directory
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        application_path = sys._MEIPASS
        # Also set the working directory to where exe is located for sessions folder
        exe_dir = os.path.dirname(sys.executable)
        os.chdir(exe_dir)
    else:
        # Running as script
        application_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(application_path)
    
    # Add application path to sys.path so imports work
    if application_path not in sys.path:
        sys.path.insert(0, application_path)
    
    # Create necessary folders in exe directory (not temp)
    folders = ['uploaded_videos', 'downloaded_videos', 'sessions', 'projects']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    # Start browser opener thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Import and run Flask app
    print("="*80)
    print("Advertisement Eye Tracking - Neuromarketing Tool")
    print("="*80)
    print()
    print("Starting server...")
    print("Browser will open automatically at: http://localhost:5000")
    print()
    print("To stop: Close this window or press Ctrl+C")
    print("="*80)
    print()
    
    # Import the main app
    try:
        from video_roi_webapp import app, socketio
    except ImportError as e:
        print(f"Error importing application: {e}")
        print("\nTrying alternative import...")
        # Try importing from current directory
        import importlib.util
        spec = importlib.util.spec_from_file_location("video_roi_webapp", 
                                                       os.path.join(application_path, "video_roi_webapp.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app = module.app
        socketio = module.socketio
    
    # Run Flask server
    try:
        socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        # Don't use input() in frozen exe without console
        if not getattr(sys, 'frozen', False):
            input("Press Enter to exit...")
        else:
            import time
            time.sleep(5)  # Wait 5 seconds before closing

if __name__ == '__main__':
    main()

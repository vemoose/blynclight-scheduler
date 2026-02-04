import sys
import logging
import subprocess
import socket
from pathlib import Path
from config_store import ConfigStore
from device_controller import DeviceManager
from tray_app import TrayApp

# Port used to ensure only one background engine runs
LOCK_PORT = 8988

def is_already_running():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', LOCK_PORT)) == 0

def main():
    # Warm-up delay: Give Windows a moment to settle on boot
    import time
    if "--settings" not in sys.argv:
        time.sleep(5)

    # 1. Initialize Config and Logging
    config_store = ConfigStore()
    config_store.setup_logging()
    
    # Check if we just want to open settings
    if "--settings" in sys.argv:
        logging.info("Opening Rules Dashboard...")
        import settings_server
        settings_server.start_settings_ui()
        return

    # 2. Single Instance Check
    if is_already_running():
        logging.info("Application already running. Opening settings instead...")
        # Cross-instance communication: just launch a settings-only process
        import settings_server
        settings_server.start_settings_ui()
        sys.exit(0)

    # 3. Hold the lock port
    # We keep this socket open for the duration of the process
    try:
        lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        lock_socket.bind(('localhost', LOCK_PORT))
        lock_socket.listen(1)
    except Exception as e:
        logging.error(f"Could not bind to lock port {LOCK_PORT}: {e}")
        sys.exit(1)

    logging.info("Blynclight Scheduler Starting...")
    
    # 4. Initialize Device Manager
    device_manager = DeviceManager(config_store)
    
    # 5. Create and Run Tray App
    app = TrayApp(config_store, device_manager)
    
    try:
        app.run()
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt, exiting...")
        app.on_exit()
    except Exception as e:
        logging.critical(f"Application crashed: {e}")
        sys.exit(1)
    finally:
        lock_socket.close()

if __name__ == "__main__":
    main()

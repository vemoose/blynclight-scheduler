import sys
import logging
import subprocess
from pathlib import Path
from config_store import ConfigStore
from device_controller import DeviceManager
from tray_app import TrayApp

def main():
    # 1. Initialize Config and Logging
    config_store = ConfigStore()
    config_store.setup_logging()
    
    # Check if we just want to open settings
    if "--settings" in sys.argv:
        logging.info("Opening Rules Dashboard...")
        import settings_server
        settings_server.start_settings_ui()
        return

    logging.info("Blynclight Scheduler Starting...")
    
    # 2. Initialize Device Manager
    device_manager = DeviceManager(config_store)
    
    # 3. Create and Run Tray App
    app = TrayApp(config_store, device_manager)
    
    try:
        app.run()
    except KeyboardInterrupt:
        logging.info("Received KeyboardInterrupt, exiting...")
        app.on_exit()
    except Exception as e:
        logging.critical(f"Application crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

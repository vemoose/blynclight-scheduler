import json
import logging
import os
from pathlib import Path

class ConfigStore:
    DEFAULT_CONFIG = {
        "default_state": "away",
        "rules": [
            { 
                "days": ["Mon", "Tue", "Wed", "Thu", "Fri"], 
                "start": "09:00", 
                "end": "17:00", 
                "state": "focused", 
                "enabled": True 
            }
        ],
        "manual_override": None,
        "poll_seconds": 2,
        "turn_off_on_exit": True,
        "start_on_login": False
    }

    def __init__(self, config_name="config.json"):
        self.config_dir = Path.home() / ".blynclight_scheduler"
        self.config_dir.mkdir(exist_ok=True)
        self.config_path = self.config_dir / config_name
        self.log_path = self.config_dir / "app.log"
        self.last_mtime = 0
        self.runtime_status = {} # In-memory only!
        self.config = self.load_config()

    def load_config(self):
        if self.config_path.exists():
            try:
                self.last_mtime = os.path.getmtime(self.config_path)
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    
                    # Migrate legacy colors
                    ov = content.get("manual_override")
                    cmap = {"red": "focused", "green": "open", "blue": "away"}
                    if ov in cmap:
                        content["manual_override"] = cmap[ov]
                    
                    # Migrate old polling interval for better reactivity
                    if content.get("poll_seconds") == 30:
                        content["poll_seconds"] = 2
                        
                    # Simple validation/merge
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(content)
                    logging.debug(f"Config reloaded from {self.config_path}")
                    return config
            except Exception as e:
                logging.error(f"Failed to load config: {e}")
        return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            # Update mtime after saving to prevent immediate reload
            self.last_mtime = os.path.getmtime(self.config_path)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def get(self, key, default=None):
        # Check runtime-only memory first (for device status)
        if key in self.runtime_status:
            return self.runtime_status[key]
            
        self.reload()
        return self.config.get(key, default)

    def set(self, key, value):
        # Don't save transient device status to disk!
        # This prevents the 'sharing violation' file-lock on startup
        if key in ["device_status", "last_polling_time"]:
            self.runtime_status[key] = value
            return

        self.reload() # Get latest before applying
        if self.config.get(key) != value:
            self.config[key] = value
            self.save_config()

    def reload(self):
        if not self.config_path.exists():
            return
            
        try:
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self.last_mtime:
                self.config = self.load_config()
        except Exception:
            pass

    def setup_logging(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )

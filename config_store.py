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
        self.status_path = self.config_dir / "status.json"
        self.log_path = self.config_dir / "app.log"
        self.last_mtime = 0
        self.last_status_mtime = 0
        self.runtime_status = {} 
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
        # 1. Check current runtime memory
        if key in self.runtime_status:
            return self.runtime_status[key]
            
        # 2. Check the dedicated status file (cross-process sync)
        if key == "device_status":
            self._reload_status_file()
            return self.runtime_status.get("device_status", "searching")

        self.reload()
        return self.config.get(key, default)

    def set(self, key, value):
        # 1. Device status goes to dedicated status file to avoid locking config.json
        if key == "device_status":
            if self.runtime_status.get(key) != value:
                self.runtime_status[key] = value
                self._save_status_file()
            return

        # 2. Regular settings
        self.reload()
        if self.config.get(key) != value:
            self.config[key] = value
            self.save_config()

    def _reload_status_file(self):
        if not self.status_path.exists(): return
        try:
            mtime = os.path.getmtime(self.status_path)
            if mtime > self.last_status_mtime:
                with open(self.status_path, 'r') as f:
                    self.runtime_status.update(json.load(f))
                self.last_status_mtime = mtime
        except: pass

    def _save_status_file(self):
        try:
            with open(self.status_path, 'w') as f:
                json.dump(self.runtime_status, f)
            self.last_status_mtime = os.path.getmtime(self.status_path)
        except: pass

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

import threading
import time
import logging
import platform
import subprocess
import os
import sys
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
from schedule_engine import ScheduleEngine

class TrayApp:
    def __init__(self, config_store, device_manager):
        self.config_store = config_store
        self.device_manager = device_manager
        self.schedule_engine = ScheduleEngine(config_store)
        self.last_status = None
        self.last_override = "none" # Cache to detect changes
        self.running = True
        self.icon = None
        self.is_mac = platform.system() == "Darwin"

    def create_image(self, color="gray"):
        # Super-sampled size for high-fidelity rendering
        canvas_size = 256
        target_size = 32 if self.is_mac else 64
        
        # Base colors (modern SaaS palette)
        colors = {
            "open": (16, 185, 129),    # Emerald
            "focused": (239, 68, 68),  # Rose
            "away": (59, 130, 246),    # Azure
            "off": (148, 163, 184),    # Slate
            "gray": (148, 163, 184)
        }
        
        base_rgb = colors.get(color.lower(), colors["gray"])
        
        # Create 1.5x brighter center for the "glow"
        center_rgb = tuple(min(255, int(c * 1.5)) for c in base_rgb)
        
        # Create high-res canvas with transparency
        image = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        center_xy = canvas_size // 2
        max_radius = (canvas_size // 2) - 8
        
        # DRAW RADIAL GRADIENT
        # We iterate from outer to inner to create a smooth transition
        # working at 256px resolution ensures no visible banding
        for r in range(max_radius, 0, -2):
            # Calculate interpolation factor (0 at center, 1 at edge)
            # Use quadratic curve for a "stronger in middle" appearance
            t = (r / max_radius) ** 1.8
            
            curr_color = tuple(
                int(center_rgb[i] + (base_rgb[i] - center_rgb[i]) * t)
                for i in range(3)
            )
            
            bbox = [center_xy - r, center_xy - r, center_xy + r, center_xy + r]
            dc.ellipse(bbox, fill=curr_color)

        # Subtle translucent border for depth
        dc.ellipse([center_xy - max_radius, center_xy - max_radius, 
                   center_xy + max_radius, center_xy + max_radius], 
                   outline=(0, 0, 0, 40), width=4)

        # Downscale using high-quality Lanczos filter
        # Handle different PIL versions for Resampling constant
        resampling_filter = getattr(Image, 'Resampling', Image).LANCZOS if hasattr(Image, 'Resampling') else getattr(Image, 'ANTIALIAS', 1)
        
        return image.resize((target_size, target_size), resample=resampling_filter)

    def is_override_active(self, item):
        """Callback for pystray to determine if 'Resume Schedule' should be shown."""
        ov = self.config_store.config.get("manual_override")
        active = ov is not None and str(ov).lower() != "none"
        return active

    def setup_tray(self):
        self.icon = pystray.Icon("blynclight_scheduler", self.create_image(), "Blynclight Scheduler", menu=self.get_menu())

    def get_menu(self):
        return pystray.Menu(
            item('Blynclight Settings', self.show_settings, default=True),
            item('Resume Schedule', self.resume_schedule, visible=self.is_override_active),
            pystray.Menu.SEPARATOR,
            item('● Force Open', lambda: self.set_override('open')),
            item('● Force Focused', lambda: self.set_override('focused')),
            item('● Force Away', lambda: self.set_override('away')),
            item('○ Force Off', lambda: self.set_override('off')),
            pystray.Menu.SEPARATOR,
            item('Exit', self.on_exit),
        )

    def show_settings(self, icon=None, item=None):
        """Launches the settings UI in a separate process."""
        try:
            # Determine the command to run
            if getattr(sys, 'frozen', False):
                # If running as the built EXE
                cmd = [sys.executable, "--settings"]
            else:
                # If running from source
                cmd = [sys.executable, "main.py", "--settings"]
            
            logging.info(f"Launching settings process: {cmd}")
            subprocess.Popen(cmd)
        except Exception as e:
            logging.error(f"Failed to launch settings UI: {e}")

    def set_override(self, status):
        self.config_store.set("manual_override", status)
        self.update_light()

    def resume_schedule(self):
        self.config_store.set("manual_override", None)
        self.update_light()

    def on_exit(self, icon=None, item=None):
        self.running = False
        if self.config_store.get("turn_off_on_exit"):
            self.device_manager.turn_off()
        if self.icon:
            self.icon.stop()

    def update_light(self):
        # 0. Ensure we have latest (smart reload handles efficiency)
        self.config_store.reload()
        cfg = self.config_store.config
        
        # 1. Sync device connection status primarily for Dashboard
        dev_status = self.device_manager.get_connection_status()
        if cfg.get("device_status") != dev_status:
            cfg["device_status"] = dev_status
            self.config_store.save_config()

        # 2. Determine desired state
        current_override = str(cfg.get("manual_override", "none")).lower()
        desired_status = self.schedule_engine.get_desired_status()
        
        # 3. Update hardware and icons ONLY on actual transition
        if desired_status != self.last_status:
            logging.info(f"Transition: {self.last_status} -> {desired_status}")
            self.device_manager.set_status_color(desired_status)
            self.last_status = desired_status
            if self.icon:
                self.icon.icon = self.create_image(desired_status)
        
        # 4. Refresh menu context ONLY if override mode switched
        if current_override != self.last_override:
            logging.debug(f"Override Mode -> {current_override}. Refreshing menu.")
            self.last_override = current_override
            if self.icon:
                self.icon.menu = self.get_menu()

    def main_loop(self):
        logging.info("Starting optimized schedule main loop")
        self.device_manager.connect()
        
        while self.running:
            try:
                self.update_light()
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                
            # Efficient polling: Read once per loop
            poll_time = self.config_store.config.get("poll_seconds", 2)
            time.sleep(max(1, poll_time))

    def run(self):
        self.setup_tray()
        
        # Run main loop in a background thread
        thread = threading.Thread(target=self.main_loop, daemon=True)
        thread.start()
        
        # Run the tray icon (this is blocking)
        self.icon.run()

import logging
import time
from abc import ABC, abstractmethod

try:
    from blynclight import Blynclight as BlynclightLib
except ImportError:
    BlynclightLib = None

try:
    import hid
except ImportError:
    hid = None

class LightController(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def set_color(self, r, g, b):
        pass

    @abstractmethod
    def turn_off(self):
        pass

class BlynclightController(LightController):
    def __init__(self):
        self.device = None

    def connect(self):
        if not BlynclightLib:
            logging.error("blynclight library not installed.")
            return False
        try:
            # The blynclight package usually detects devices automatically
            self.device = BlynclightLib.get_light()
            return self.device is not None
        except Exception as e:
            logging.error(f"BlynclightController connection failed: {e}")
            return False

    def disconnect(self):
        self.device = None

    def set_color(self, r, g, b):
        if self.device:
            try:
                self.device.color = (r, g, b)
                return True
            except Exception as e:
                logging.error(f"Failed to set color via Blynclight: {e}")
                self.device = None
        return False

    def turn_off(self):
        if self.device:
            try:
                self.device.on = False
                return True
            except Exception as e:
                logging.error(f"Failed to turn off via Blynclight: {e}")
                self.device = None
        return False

class HIDFallbackController(LightController):
    # Standard Embrava Blynclight VIDs/PIDs
    VID = 0x2C0D
    PID_8 = 0x0001 # Blynclight Standard
    PID_16 = 0x0002 # Blynclight Lync
    
    def __init__(self):
        self.device = None

    def connect(self):
        if not hid:
            logging.error("hidapi (hid) library not installed.")
            return False
        try:
            for d in hid.enumerate(self.VID):
                self.device = hid.device()
                self.device.open_path(d['path'])
                logging.info(f"Connected to HID device: {d['product_string']}")
                return True
        except Exception as e:
            logging.error(f"HIDFallbackController connection failed: {e}")
        return False

    def disconnect(self):
        if self.device:
            self.device.close()
            self.device = None

    def set_color(self, r, g, b):
        if not self.device: return False
        try:
            # Embrava HID protocol: 
            # Report ID 0, R, B, G, Intensity, Command, ...
            # Usually: 0x00, r, b, g, 0xFF, 0x00, 0x00, 0x00, 0x00
            # Note: Blue/Green are sometimes swapped in HID report
            data = [0x00, r, b, g, 0xFF, 0x00, 0x00, 0x00, 0x00]
            self.device.write(data)
            return True
        except Exception as e:
            logging.error(f"HID set_color error: {e}")
            self.device = None
            return False

    def turn_off(self):
        return self.set_color(0, 0, 0)

class SimulatedController(LightController):
    def __init__(self, on_color_change=None):
        self.on_color_change = on_color_change
        self.connected = False
        self.current_color = (0, 0, 0)

    def connect(self):
        self.connected = True
        logging.info("Connected to Simulated Blynclight")
        return True

    def disconnect(self):
        self.connected = False

    def set_color(self, r, g, b):
        self.current_color = (r, g, b)
        color_name = self._get_color_name(r, g, b)
        logging.info(f"SIMULATOR: Light color set to {color_name} ({r}, {g}, {b})")
        if self.on_color_change:
            self.on_color_change(color_name)
        return True

    def turn_off(self):
        self.current_color = (0, 0, 0)
        logging.info("SIMULATOR: Light turned OFF")
        if self.on_color_change:
            self.on_color_change("off")
        return True

    def _get_color_name(self, r, g, b):
        if r > 200 and g < 50 and b < 50: return "red"
        if g > 200 and r < 50 and b < 50: return "green"
        if b > 200 and r < 50 and g < 50: return "blue"
        if r == 0 and g == 0 and b == 0: return "off"
        return f"rgb({r},{g},{b})"

class DeviceManager:
    def __init__(self, config):
        self.config = config
        self.controller = None
        self.simulated_mode = False
        self.on_sim_color_change = None # Callback for UI update
        self.connection_status = "searching"
        
        self.available_controllers = [
            BlynclightController(),
            HIDFallbackController()
        ]

    def connect(self):
        # Try real controllers first
        for ctrl in self.available_controllers:
            if ctrl.connect():
                self.controller = ctrl
                self.simulated_mode = False
                self.connection_status = "connected"
                logging.info(f"Successfully connected using {ctrl.__class__.__name__}")
                return True
        
        # Fallback to Simulator
        logging.info("No physical Blynclight found. Starting Simulator Mode.")
        self.controller = SimulatedController(on_color_change=self.on_sim_color_change)
        self.controller.connect()
        self.simulated_mode = True
        self.connection_status = "not_detected"
        return True

    def get_connection_status(self):
        return self.connection_status

    def is_connected(self):
        return self.controller is not None

    def set_color(self, r, g, b):
        success = False
        if self.controller:
            success = self.controller.set_color(r, g, b)
            
        if not success:
            # Persistent retry if hardware fails (common on Windows boot)
            logging.warning("Light update failed, attempting reconnect and retry...")
            time.sleep(1) # Grace period
            if self.connect():
                if self.controller:
                    self.controller.set_color(r, g, b)

    def turn_off(self):
        if self.controller:
            self.controller.turn_off()

    def set_status_color(self, status):
        status = status.lower()
        if status in ["open", "green"]:
            self.set_color(0, 255, 0)
        elif status in ["focused", "red"]:
            self.set_color(255, 0, 0)
        elif status in ["away", "blue"]:
            self.set_color(0, 0, 255)
        elif status in ["off"]:
            self.turn_off()

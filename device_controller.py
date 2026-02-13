import logging
import time
from abc import ABC, abstractmethod

try:
    from blynclight import BlyncLight as BlynclightLib
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
    def is_alive(self):
        pass

    @abstractmethod
    def set_color(self, r, g, b):
        pass

    @abstractmethod
    def turn_off(self):
        pass

class BlynclightController(LightController):
    """Wrapper for the official blynclight library."""
    def __init__(self):
        self.device = None

    def is_alive(self):
        if not self.device: return False
        try:
            # We check available lights to see if it's still there
            # This is more reliable than checking properties on the handle
            if not BlynclightLib: return False
            return len(BlynclightLib.available_lights()) > 0
        except Exception:
            self.device = None
            return False

    def connect(self):
        if not BlynclightLib:
            return False, "Library 'blynclight' not installed."
        try:
            self.device = BlynclightLib.get_light()
            if self.device:
                return True, "Connected via Blynclight Library"
            return False, "No Blynclight hardware detected."
        except Exception as e:
            return False, f"Blynclight Error: {str(e)}"

    def disconnect(self):
        self.device = None

    def set_color(self, r, g, b):
        if not self.device: return False
        try:
            # Ensure the device is 'on' (clears the off bit)
            self.device.on = True
            # Set the color tuple (Swapping B and G because library internal order is R, B, G)
            self.device.color = (r, b, g)
            # FORCE update because library's .color setter doesn't flush automatically
            self.device.update(force=True)
            return True
        except Exception as e:
            logging.error(f"Blynclight library set_color failed: {e}")
            self.disconnect()
            return False

    def turn_off(self):
        if self.device:
            try:
                self.device.on = False
                return True
            except Exception:
                self.disconnect()
        return False

class HIDFallbackController(LightController):
    """Direct HID implementation for maximum reliability."""
    VID = 0x2C0D
    
    def __init__(self):
        self.device = None
        self.device_path = None

    def is_alive(self):
        if not self.device: return False
        try:
            if not hid: return False
            devices = hid.enumerate(self.VID)
            return any(d['path'] == self.device_path for d in devices)
        except Exception:
            self.device = None
            return False

    def connect(self):
        if not hid:
            return False, "Library 'hidapi' not installed."
        try:
            devices = hid.enumerate(self.VID)
            if not devices:
                return False, "No Blynclight hardware found on USB."
            
            # Use the first one found
            d = devices[0]
            self.device = hid.device()
            self.device.open_path(d['path'])
            self.device_path = d['path']
            product = d.get('product_string', 'Blynclight')
            return True, f"Connected to {product} (Direct HID)"
        except Exception as e:
            return False, f"HID Connection Error: {str(e)}"

    def disconnect(self):
        if self.device:
            try:
                self.device.close()
            except: pass
            self.device = None
        self.device_path = None

    def set_color(self, r, g, b):
        if not self.device: return False
        try:
            # Control Byte (Byte 4):
            # Bit 0: Off
            # Bit 1: Dim
            # Bit 2: Flash
            # Bits 3-5: Speed (1, 2, 4)
            # Default "On" with Speed 1: 0x08
            
            patterns = [
                [0x00, r, b, g, 0x08, 0x00, 0x00, 0x00, 0x00], # Standard RBG
                [0x00, r, b, g, 0x00, 0x00, 0x00, 0x00, 0x05], # Plus Variant RBG
                [0x00, r, b, g, 0xFF, 0x00, 0x00, 0x00, 0x09]  # Extended Plus RBG
            ]
            for p in patterns:
                self.device.write(p)
            return True
        except Exception as e:
            logging.error(f"HID write failed: {e}")
            self.disconnect()
            return False

    def turn_off(self):
        return self.set_color(0, 0, 0)

class SimulatedController(LightController):
    def __init__(self, on_color_change=None):
        self.on_color_change = on_color_change
        self.connected = False

    def is_alive(self):
        return True

    def connect(self):
        self.connected = True
        return True, "Simulated Mode Active"

    def disconnect(self):
        self.connected = False

    def set_color(self, r, g, b):
        if self.on_color_change:
            self.on_color_change(f"rgb({r},{g},{b})")
        return True

    def turn_off(self):
        if self.on_color_change:
            self.on_color_change("off")
        return True

class DeviceManager:
    def __init__(self, config):
        self.config = config
        self.controller = None
        self.simulated_mode = False
        self.on_sim_color_change = None
        
        # Internal status state
        self.connection_status = {
            "code": "searching",
            "message": "Initializing...",
            "timestamp": time.time()
        }
        
        self.available_controllers = [
            BlynclightController(), # Try library first
            HIDFallbackController()  # Fallback to direct HID
        ]

    def connect(self):
        """Force a full hardware re-scan and update internal status."""
        for ctrl in self.available_controllers:
            success, message = ctrl.connect()
            if success:
                self.controller = ctrl
                self.simulated_mode = False
                self._update_status("connected", message)
                return True
        
        # Fallback to simulation
        self.controller = SimulatedController(on_color_change=self.on_sim_color_change)
        self.controller.connect()
        self.simulated_mode = True
        self._update_status("not_detected", "No physical light found. Virtual Mode active.")
        return True

    def _update_status(self, code, message):
        """Internal helper to update status only when it actually changes."""
        if self.connection_status.get("code") != code or self.connection_status.get("message") != message:
            self.connection_status = {
                "code": code,
                "message": message,
                "timestamp": time.time()
            }
            logging.info(f"Connection Status Change: {code} - {message}")

    def get_connection_status(self):
        """Check hardware health and return the current status."""
        # 1. If we are supposed to be on hardware, check if it's still alive
        if self.controller and not self.simulated_mode:
            if not self.controller.is_alive():
                logging.info("Hardware disconnected detected.")
                self.connect()
        
        # 2. If we are in virtual mode, try to find hardware occasionally
        elif self.simulated_mode:
            # Poll every 2 seconds for new hardware
            if time.time() - self.connection_status.get("timestamp", 0) > 2:
                self.connect()

        return self.connection_status

    def is_connected(self):
        return self.controller is not None and not self.simulated_mode

    def set_color(self, r, g, b):
        if not self.controller:
            self.connect()
        
        if self.controller:
            if not self.controller.set_color(r, g, b):
                # If command failed, re-connect and retry once
                if self.connect():
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

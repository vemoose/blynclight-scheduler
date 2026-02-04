import os
import sys
import platform
import logging

def set_autostart(enabled=True):
    """
    Enable or disable autostart on login.
    Currently supports Windows and macOS.
    """
    if platform.system() == "Windows":
        _set_windows_autostart(enabled)
    elif platform.system() == "Darwin":
        _set_mac_autostart(enabled)
    else:
        logging.warning("Autostart not supported on this platform.")

def _set_windows_autostart(enabled):
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "BlynclightScheduler"
    
    # Get path to the executable
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        # If running from source, this might not work well unless we point to the python interpreter + main.py
        # But for the built EXE it's perfect.
        exe_path = os.path.abspath(sys.argv[0])

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
            logging.info(f"Enabled Windows autostart: {exe_path}")
        else:
            try:
                winreg.DeleteValue(key, app_name)
                logging.info("Disabled Windows autostart")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        logging.error(f"Failed to set Windows autostart: {e}")

def _set_mac_autostart(enabled):
    """
    On macOS, we use a LaunchAgent plist.
    """
    label = "com.user.blynclight_scheduler"
    plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{label}.plist")
    
    if not enabled:
        if os.path.exists(plist_path):
            os.remove(plist_path)
            logging.info("Disabled macOS autostart (removed LaunchAgent)")
        return

    # Get path to the executable
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        exe_path = os.path.abspath(sys.argv[0])

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
    try:
        os.makedirs(os.path.dirname(plist_path), exist_ok=True)
        with open(plist_path, "w") as f:
            f.write(plist_content)
        logging.info(f"Enabled macOS autostart: {plist_path}")
    except Exception as e:
        logging.error(f"Failed to set macOS autostart: {e}")

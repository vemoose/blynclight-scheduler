# Blynclight Scheduler

A native Windows system-tray application to automatically control your Embrava Blynclight based on user-configurable schedules.

## Features
- **Automatic Color Transitions**:
  - `Green`: "Open Window" for focus or meetings (configurable intervals).
  - `Red`: "Closed Window" (default during work hours).
  - `Blue`: "Away" (outside work hours or weekends).
  - `Off`: Light off.
- **Manual Overrides**: Quickly force a color from the system tray.
- **Persistent Settings**: Stores configuration in `%APPDATA%/BlynclightScheduler`.
- **Minimal Footprint**: Runs in the background with low CPU usage.

## Setup & Installation

### Prerequisites
- Windows 10/11
- Python 3.11+
- Embrava Blynclight USB device

### Development Setup
1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
```bash
python main.py
```

## Building as a Single EXE
To package the application into a single executable for Windows:
1. Install PyInstaller: `pip install pyinstaller`
2. Run the following command:
   ```bash
   pyinstaller --noconsole --onefile --name "BlynclightScheduler" --add-data "design_system.py;." --add-data "config_store.py;." --add-data "device_controller.py;." --add-data "schedule_engine.py;." --add-data "settings_ui.py;." --add-data "tray_app.py;." main.py
   ```
   *Note: On Windows, use `;` as path separator in `--add-data`. The `--noconsole` flag prevents a black terminal window from appearing.*

## Configuration
All data is stored in:
- **Config**: `%APPDATA%/BlynclightScheduler/config.json`
- **Logs**: `%APPDATA%/BlynclightScheduler/blynclight_log.txt`

### Autostart on Login
Toggle the "Start on Windows login" in the Settings UI. 
*Implementation Note: If the toggle doesn't create the registry key automatically, you can manually add a shortcut to `BlynclightScheduler.exe` in your Startup folder (`shell:startup`).*

## Troubleshooting
- **Device Not Detected**: 
  - Ensure the official Embrava software is closed, as it may lock the USB device.
  - Try unplugging and re-plugging the light.
  - Check `blynclight_log.txt` for specific HID/Library errors.
- **Permissions**:
  - HID access on Windows sometimes requires no special permissions, but ensure no other app is controlling the light.
- **Finding Device in Device Manager**:
  - Look under "Human Interface Devices". The Hardware ID should contain `VID_2C0D`.

## Testing
Run tests using pytest:
```bash
pytest tests/
```

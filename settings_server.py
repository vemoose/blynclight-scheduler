import http.server
import socketserver
import json
import os
import sys
import webbrowser
from pathlib import Path
from config_store import ConfigStore

PORT = 8989
config_store = ConfigStore()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class SettingsHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args): return

    def do_GET(self):
        # Redirect root to our UI file
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.end_headers()
            ui_path = resource_path(os.path.join("web_ui", "index.html"))
            with open(ui_path, 'rb') as f:
                self.wfile.write(f.read())
            return
            
        if self.path == "/config":
            config_store.reload()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(json.dumps(config_store.config).encode())
        else:
            return super().do_GET()

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(length).decode())

        if self.path == "/save":
            # 1. Reload existing config to get current manual_override
            config_store.reload()
            current_override = config_store.config.get("manual_override")
            
            # 2. Update with new dashboard settings
            config_store.config["default_state"] = data.get("default_state", "away")
            config_store.config["rules"] = data.get("rules", [])
            
            # 3. Explicitly preserve the override state (don't let dashboard wipe it)
            config_store.config["manual_override"] = current_override
            config_store.save_config()
            
        elif self.path == "/force":
            state = data.get("state")
            config_store.reload()
            config_store.config["manual_override"] = state
            config_store.save_config()

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

def is_server_running():
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', PORT)) == 0

def run_server():
    os.chdir(Path(__file__).parent)
    try:
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", PORT), SettingsHandler) as httpd:
            print(f"Rules Dashboard started at http://localhost:{PORT}")
            httpd.serve_forever()
    except OSError:
        # Port might be busy or already running
        pass

def start_settings_ui():
    url = f"http://localhost:{PORT}"
    
    # 1. Start Server in background
    if not is_server_running():
        import threading
        t = threading.Thread(target=run_server, daemon=True)
        t.start()
        # Wait a moment for server to bind
        import time
        time.sleep(1)

    # 2. Try to open as a standalone Desktop Window
    try:
        import webview
        window = webview.create_window(
            'Blynclight Dashboard', 
            url, 
            width=700, 
            height=850,
            resizable=True,
            min_size=(600, 700)
        )
        webview.start()
    except Exception as e:
        # 3. Fallback to System Browser
        import logging
        logging.warning(f"Standalone window failed: {e}. Falling back to browser.")
        webbrowser.open(url)

if __name__ == "__main__":
    start_settings_ui()

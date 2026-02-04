import os
import sys
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

def create_ico():
    """Generates a professional .ico file from our dynamic icon logic."""
    print("Generating application icon...")
    canvas_size = 256
    colors = {
        "primary": (99, 102, 241), # Indigo
        "glow": (165, 180, 252)    # Lighter Indigo
    }
    
    image = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    
    center_xy = canvas_size // 2
    max_radius = (canvas_size // 2) - 10
    
    # Draw radial gradient
    for r in range(max_radius, 0, -2):
        t = (r / max_radius) ** 1.8
        curr_color = tuple(
            int(colors["glow"][i] + (colors["primary"][i] - colors["glow"][i]) * t)
            for i in range(3)
        )
        bbox = [center_xy - r, center_xy - r, center_xy + r, center_xy + r]
        dc.ellipse(bbox, fill=curr_color)

    dc.ellipse([center_xy - max_radius, center_xy - max_radius, 
               center_xy + max_radius, center_xy + max_radius], 
               outline=(0, 0, 0, 40), width=4)

    image.save('app_icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    image.save('app_icon.png')
    print("Icon generated: app_icon.ico")

def build():
    # 1. Ensure icon exists
    if not os.path.exists('app_icon.ico'):
        create_ico()
        
    # 2. Prepare PyInstaller command
    # --noconsole: Hide terminal
    # --onefile: Single EXE
    # --add-data: Include web_ui
    # --icon: App icon
    # --name: App name
    
    sep = ';' if os.name == 'nt' else ':'
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconsole',
        '--onefile',
        f'--add-data=web_ui{sep}web_ui',
        '--icon=app_icon.ico',
        '--name=BlynclightScheduler',
        '--clean',
        'main.py'
    ]
    
    print(f"Running build command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("\n" + "="*40)
        print("BUILD SUCCESSFUL!")
        print("Your executable is in the 'dist' folder.")
        print("="*40)
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
    except FileNotFoundError:
        print("Error: PyInstaller not found. Please install it with: pip install pyinstaller")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--icon-only":
        create_ico()
    else:
        build()

@echo off
echo ========================================
echo Blynclight Scheduler: Windows Build Tool
echo ========================================
echo.

echo 1. Checking for Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b
)

echo 2. Installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo 3. Building EXE...
python build_exe.py

echo.
echo ========================================
echo BUILD COMPLETE!
echo Check the "dist" folder for BlynclightScheduler.exe
echo ========================================
pause

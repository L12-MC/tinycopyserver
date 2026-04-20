@echo off
REM TinyCopyServer Quick Start for Windows

echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Dependency installation failed. See README.md for setup and troubleshooting.
    exit /b %errorlevel%
)

echo.
echo Starting TinyCopyServer...
echo.
echo Server will be available at: http://localhost:8000
echo Admin Panel: http://localhost:8000 (lock icon)
echo Username: admin
echo Password: tcs2024secure
echo.

python main.py

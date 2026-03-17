@echo off
call scripts\start_service.bat

if errorlevel 1 (
    echo Service failed to start. Exiting.
    exit /b %errorlevel%
)

python main.py
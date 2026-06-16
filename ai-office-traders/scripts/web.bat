@echo off
cd /d "%~dp0"
echo AI Office - Web Dashboard

set PYTHON_PATH=
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('where python') do (
        if not defined PYTHON_PATH set "PYTHON_PATH=%%i"
    )
)
if not defined PYTHON_PATH (
    where py >nul 2>&1
    if %errorlevel% equ 0 set "PYTHON_PATH=py"
)
if not defined PYTHON_PATH (
    for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
        if exist "%%d\python.exe" if not defined PYTHON_PATH set "PYTHON_PATH=%%d\python.exe"
    )
)

if not defined PYTHON_PATH (
    echo Python не найден! Запустите install.bat
    pause
    exit /b 1
)

start /b cmd /c "timeout /t 3 >nul && start http://localhost:5000"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py --web
) else (
    "%PYTHON_PATH%" main.py --web
)
pause

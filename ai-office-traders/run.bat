@echo off
cd /d "%~dp0"

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
    for /d %%d in ("C:\Python*") do (
        if exist "%%d\python.exe" if not defined PYTHON_PATH set "PYTHON_PATH=%%d\python.exe"
    )
)

if not defined PYTHON_PATH (
    echo Python не найден! Запустите install.bat
    pause
    exit /b 1
)

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py %*
) else (
    "%PYTHON_PATH%" main.py %*
)
pause

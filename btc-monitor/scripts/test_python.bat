@echo off
echo === Тест Python ===

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
    echo Python НЕ НАЙДЕН!
    echo Попробуйте: py --version
    pause
    exit /b 1
)

echo Python: %PYTHON_PATH%
"%PYTHON_PATH%" --version
echo.
echo pip:
"%PYTHON_PATH%" -m pip --version
echo.
echo Все работает!
pause

@echo off
cd /d "%~dp0"

REM === Автопоиск Python ===
set PYTHON_PATH=

REM 1. Проверяем PATH
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('where python') do (
        if not defined PYTHON_PATH set "PYTHON_PATH=%%i"
    )
)

REM 2. Проверяем py.exe лаунчер
if not defined PYTHON_PATH (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_PATH=py"
    )
)

REM 3. Ищем в AppData\Local\Programs\Python
if not defined PYTHON_PATH (
    for /d %%d in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
        if exist "%%d\python.exe" (
            if not defined PYTHON_PATH set "PYTHON_PATH=%%d\python.exe"
        )
    )
)

REM 4. Ищем в C:\Python*
if not defined PYTHON_PATH (
    for /d %%d in ("C:\Python*") do (
        if exist "%%d\python.exe" (
            if not defined PYTHON_PATH set "PYTHON_PATH=%%d\python.exe"
        )
    )
)

REM 5. Ищем в Program Files
if not defined PYTHON_PATH (
    for /d %%d in ("C:\Program Files\Python*") do (
        if exist "%%d\python.exe" (
            if not defined PYTHON_PATH set "PYTHON_PATH=%%d\python.exe"
        )
    )
)

REM 6. Ищем в Program Files (x86)
if not defined PYTHON_PATH (
    for /d %%d in ("C:\Program Files (x86)\Python*") do (
        if exist "%%d\python.exe" (
            if not defined PYTHON_PATH set "PYTHON_PATH=%%d\python.exe"
        )
    )
)

REM 7. Ищем в CommonAppData
if not defined PYTHON_PATH (
    for /d %%d in ("C:\ProgramData\*python*") do (
        if exist "%%d\python.exe" (
            if not defined PYTHON_PATH set "PYTHON_PATH=%%d\python.exe"
        )
    )
)

REM === Результат ===
if not defined PYTHON_PATH (
    echo.
    echo ============================================
    echo   Python НЕ НАЙДЕН на компьютере!
    echo ============================================
    echo.
    echo Варианты решения:
    echo   1. Скачайте Python: https://www.python.org/downloads/
    echo   2. При установке поставьте галочку "Add Python to PATH"
    echo   3. Или вручную добавьте путь к Python в PATH:
    echo      ПКМ на "Этот компьютер" - Свойства - Доп. параметры
    echo      - Переменные среды - Path - Изменить - Добавить
    echo.
    pause
    exit /b 1
)

echo Python найден: %PYTHON_PATH%
echo.

REM === Проверка версии Python ===
"%PYTHON_PATH%" -c "import sys; v=sys.version_info; exit(0 if v.major>=3 and v.minor>=9 else 1)" 2>nul
if %errorlevel% neq 0 (
    echo ОШИБКА: Требуется Python 3.9 или выше!
    "%PYTHON_PATH%" --version
    pause
    exit /b 1
)

REM === Создание виртуального окружения ===
if not exist "venv" (
    echo Создание виртуального окружения...
    "%PYTHON_PATH%" -m venv venv
)

REM === Активация venv и установка пакетов ===
echo Установка пакетов...
call venv\Scripts\activate.bat
pip install --upgrade pip 2>nul
pip install -r requirements.txt
echo.

REM === Запуск ===
echo Запуск AI Office...
echo.
python main.py --staff
echo.
pause

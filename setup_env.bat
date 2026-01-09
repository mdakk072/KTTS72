@echo off
setlocal EnableExtensions EnableDelayedExpansion

echo ============================================================
echo Environment Setup for Windows
echo ============================================================
echo.

rem ------------------------------------------------------------
rem 1) Find Python 3.10+ (check multiple locations)
rem ------------------------------------------------------------
set "PYTHON_CMD="

rem Try py launcher first
py -3.10 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.10"
    goto :found_python
)

rem Try py launcher with any 3.x
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    goto :found_python
)

rem Try python in PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :found_python
)

rem Try Python Install Manager locations (new Windows approach)
set "PYTHON_MANAGER=%LOCALAPPDATA%\Python"
if exist "%PYTHON_MANAGER%" (
    rem Find any pythoncore-3.x folder
    for /d %%D in ("%PYTHON_MANAGER%\pythoncore-3*") do (
        if exist "%%D\python.exe" (
            set "PYTHON_CMD=%%D\python.exe"
            goto :found_python
        )
    )
)

rem Try traditional Windows install locations
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%P (
        set "PYTHON_CMD=%%~P"
        goto :found_python
    )
)

rem Try Microsoft Store Python
for %%P in (
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.exe"
    "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
) do (
    if exist %%P (
        set "PYTHON_CMD=%%~P"
        goto :found_python
    )
)

echo [ERROR] No suitable Python found.
echo.
echo Please install Python 3.10+ from one of:
echo   - https://www.python.org/downloads/
echo   - Microsoft Store (search "Python 3.10")
echo   - winget install Python.Python.3.10
echo.
goto :EOF

:found_python
echo [OK] Found Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

rem ------------------------------------------------------------
rem 2) Create virtual environment if needed
rem ------------------------------------------------------------
if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual environment found
) else (
    echo [SETUP] Creating virtual environment...
    "%PYTHON_CMD%" -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        goto :EOF
    )
    echo [OK] Virtual environment created
)
echo.

rem ------------------------------------------------------------
rem 3) Activate venv
rem ------------------------------------------------------------
echo [SETUP] Activating virtual environment...
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    goto :EOF
)

rem From here on, "python" is the venv python.

rem ------------------------------------------------------------
rem 4) Install dependencies
rem ------------------------------------------------------------
echo.
echo [SETUP] Installing dependencies...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip.
    goto :EOF
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    goto :EOF
)
echo [OK] Dependencies installed

rem ------------------------------------------------------------
rem 5) Download Kokoro models if needed
rem ------------------------------------------------------------
echo.
echo [SETUP] Checking for local models...

if exist "models\kokoro-82m\kokoro-v1_0.pth" (
    echo [OK] Local models found
) else (
    echo [SETUP] Models not found, downloading...
    echo This will download base model + 32 voices ^(~1.2 GB total^)...
    echo This may take several minutes...
    echo.

    python download_models.py
    if errorlevel 1 (
        echo [ERROR] Failed to download models.
        goto :EOF
    )
)


rem ------------------------------------------------------------
rem 6) Setup complete
rem ------------------------------------------------------------
echo.
echo ============================================================
echo [SUCCESS] Environment setup complete!
echo ============================================================
echo.
echo You can now:
echo   1. Build: build.bat
echo   2. Test: python app.py --text "Hello" --out test.wav
echo.

endlocal
goto :EOF

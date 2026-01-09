@echo off
setlocal EnableExtensions

echo ============================================================
echo Environment Setup for Windows
echo ============================================================
echo.

rem ------------------------------------------------------------
rem 1) Choose a Python (3.10+ recommended)
rem ------------------------------------------------------------
set "PYTHON_CMD=py -3.10"

%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    rem Fallback to "python"
    set "PYTHON_CMD=python"
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No suitable Python found. Install Python 3.10+ and retry.
        goto :EOF
    )
)

echo [OK] Using Python interpreter: %PYTHON_CMD%
echo.

rem ------------------------------------------------------------
rem 2) Create virtual environment if needed
rem ------------------------------------------------------------
if exist "venv\Scripts\activate.bat" (
    echo [OK] Virtual environment found
) else (
    echo [SETUP] Creating virtual environment...
    %PYTHON_CMD% -m venv venv
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
rem 5) Install PyInstaller
rem ------------------------------------------------------------
echo.
echo [SETUP] Installing PyInstaller...
python -m pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller.
    goto :EOF
)
echo [OK] PyInstaller installed

rem ------------------------------------------------------------
rem 6) Download Kokoro models if needed
rem ------------------------------------------------------------
echo.
echo [SETUP] Checking for local models...

if exist "models\kokoro-82m\kokoro-v1_0.pth" (
    echo [OK] Local models found
) else (
    echo [SETUP] Models not found, downloading...
    echo This will download base model + 41 voices ^(~1.5 GB total^)... 
    echo This may take several minutes...
    echo.

    python download_models.py
    if errorlevel 1 (
        echo [ERROR] Failed to download models.
        goto :EOF
    )
)


rem ------------------------------------------------------------
rem 7) Setup complete
rem ------------------------------------------------------------
echo.
echo ============================================================
echo [SUCCESS] Environment setup complete!
echo ============================================================
echo.
echo You can now:
echo   1. Build: build.bat   (or your Windows build command)
echo   2. Test: python -m kokoro_announce --text "Hello" --out test.wav
echo.

endlocal
goto :EOF

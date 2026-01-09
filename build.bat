@echo off
setlocal EnableExtensions

REM Build script for Windows
REM Creates standalone executable with PyInstaller

echo ============================================================
echo Building Kokoro Announce (Windows)
echo ============================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo Please run setup_env.bat first.
    exit /b 1
)

REM Activate virtual environment
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat

REM Verify Python works
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not working in venv.
    echo Please run setup_env.bat again.
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller not installed.
    echo Please run setup_env.bat first.
    exit /b 1
)

REM Check if models exist
if not exist "models\kokoro-82m\kokoro-v1_0.pth" (
    echo [ERROR] Models not found.
    echo Please run setup_env.bat first.
    exit /b 1
)

REM Clean previous build
echo [CLEAN] Removing old build files...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo [OK] Clean complete

REM Build with PyInstaller
echo.
echo [BUILD] Running PyInstaller...
echo This may take several minutes...
echo.
python -m PyInstaller app.spec
if errorlevel 1 (
    echo [ERROR] Build failed
    exit /b 1
)

REM Test the build
echo.
echo ============================================================
echo Testing Build
echo ============================================================
echo.
dist\Kokoro72CLI\Kokoro72CLI.exe --text "Build test successful" --out dist_test.wav
if errorlevel 1 (
    echo [ERROR] Build test failed
    exit /b 1
)

REM Show build info
echo.
echo ============================================================
echo [SUCCESS] Build Complete!
echo ============================================================
echo.
echo Build location: dist\Kokoro72CLI\
echo Executable: dist\Kokoro72CLI\Kokoro72CLI.exe
echo.

REM Calculate size
for /f %%A in ('powershell -Command "(Get-ChildItem -Path dist\Kokoro72CLI -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"') do set SIZE=%%A
echo Build size: %SIZE% MB
echo.

echo Test it:
echo   dist\Kokoro72CLI\Kokoro72CLI.exe --text "Hello" --out hello.wav
echo.

endlocal

@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo JSON Game Translator - Windows Build
echo ========================================

where py >nul 2>nul
if errorlevel 1 (
    echo Python launcher was not found.
    echo Install Python 3.12+ from https://www.python.org/downloads/windows/
    pause
    exit /b 1
)

py -3.12 -m pip install --upgrade pip
if errorlevel 1 exit /b 1
py -3.12 -m pip install -r requirements-build.txt
if errorlevel 1 exit /b 1

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist JSON_Game_Translator.spec del /q JSON_Game_Translator.spec

py -3.12 -m PyInstaller --noconfirm --clean --onefile --windowed --name JSON_Game_Translator json_translator_windows.py
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Build complete:
echo %CD%\dist\JSON_Game_Translator.exe
pause

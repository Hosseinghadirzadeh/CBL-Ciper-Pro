@echo off
setlocal
cd /d "%~dp0\.."
set "PYEXE=python"
if exist ".venv\Scripts\python.exe" set "PYEXE=.venv\Scripts\python.exe"
"%PYEXE%" -m PyInstaller --noconfirm --clean build\CBL_Ciper_Pro.spec
if errorlevel 1 exit /b %errorlevel%
if not exist "dist\CBL_Ciper_Pro\CBL_Ciper_Pro.exe" exit /b 2
echo Built: %CD%\dist\CBL_Ciper_Pro\CBL_Ciper_Pro.exe

@echo off
setlocal
cd /d "%~dp0\.."
where ISCC.exe >nul 2>nul
if errorlevel 1 (
  echo Inno Setup 6 ISCC.exe was not found on PATH.
  exit /b 1
)
ISCC.exe installer\CBL_Ciper_Pro.iss

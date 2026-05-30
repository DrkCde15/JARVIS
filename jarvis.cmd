@echo off
set "JARVIS_DIR=%~dp0"

pushd "%JARVIS_DIR%" >nul

if exist "%JARVIS_DIR%jenv\Scripts\python.exe" (
    "%JARVIS_DIR%jenv\Scripts\python.exe" "%JARVIS_DIR%main.py" %*
) else (
    python "%JARVIS_DIR%main.py" %*
)

set "JARVIS_EXIT=%ERRORLEVEL%"
popd >nul
exit /b %JARVIS_EXIT%

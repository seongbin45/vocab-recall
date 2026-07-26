@echo off
setlocal
set "SCRIPT=%~dp0vocab.py"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)

where python >nul 2>&1
if %ERRORLEVEL%==0 (
  python "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)

echo Python 3 not found. Install from https://www.python.org/ or enable the py launcher.
exit /b 1

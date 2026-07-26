@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  py -3 -m streamlit run app.py --server.headless true
  exit /b %ERRORLEVEL%
)

python -m streamlit run app.py --server.headless true
exit /b %ERRORLEVEL%

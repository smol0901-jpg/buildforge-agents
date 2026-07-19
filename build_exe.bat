@echo off
setlocal
cd /d %~dp0
python -m venv .venv
call .venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm BuildForge.spec
echo.
echo Done: dist\BuildForgeAgents.exe
pause

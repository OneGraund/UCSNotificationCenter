@echo off

REM Kill the running Python script
taskkill /IM python.exe /F

REM Update files from Git repository
git pull origin main

REM Install libraries from requirements.txt
pip install -r requirements.txt

REM Run the Python file again
python bot.py
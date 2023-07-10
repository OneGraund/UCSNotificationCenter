@echo off

REM Kill the running Python script
taskkill /IM python.exe /F

cd C:\ucs\UCSNotificationCenter\UCSNotificationCenter

REM Update files from Git repository
git pull origin main

REM Install libraries from requirements.txt
pip install -r requirements.txt

REM Start the Python script and close the console window
start "" /B python bot.py updated

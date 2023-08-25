@echo off

REM Starting bot.py pyton script with all bots...
cd C:\ucs\UCSNotificationCenter
git pull origin main
pip install -r requirements.txt
start "" /B python bot.py updated
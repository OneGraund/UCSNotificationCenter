@echo off

REM Starting bot.py pyton script with all bots...
cd C:\ucs\UCSNotificationCenter\UCSNotificationCenter
git pull origin main
pip install -r requirements.txt
python bot.py
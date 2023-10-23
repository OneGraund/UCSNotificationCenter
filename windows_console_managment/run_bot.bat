@echo off

taskkill /IM python.exe /F
REM Starting bot.py pyton script with all bots...
cd C:\Users\Rkeeper\UCSNotificationCenter
git pull
pip install -r requirements.txt
start "" /B python main.py --disable_notifications --wks_upd_interval 30 --wks_output_upd
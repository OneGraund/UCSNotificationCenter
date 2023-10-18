@echo off

taskkill /IM python.exe /F
REM Starting bot.py pyton script with all bots...
cd C:\Users\Rkeeper\UCSNotificationCenter
git pull
git install -r requirements.txt
start "" /B python main.py --disable_notifications --notify_on_start --wks_upd_interval 2 --wks_output_upd
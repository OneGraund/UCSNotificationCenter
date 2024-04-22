@echo off

taskkill /IM python.exe /F
REM Starting bot.py pyton script with all bots...
cd C:\Users\Rkeeper\UCSNotificationCenter
pip install -r requirements.txt
start "" /B python -u main.py --disable_notifications --wks_upd_interval 10 --wks_output_upd --req_err_resol
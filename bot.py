import datetime
import os
import platform
import sys
import tkinter as tk
import dotenv
import threading
import time
import utils
import telebot
from sheets import SupportWKS, SupportDataWKS
import sip_call
from tkinter import font
from sip_call import call_employee

dotenv.load_dotenv()

support_wks = SupportWKS()
support_data_wks = SupportDataWKS()

TEST = True
START_MUTED = True
REQUEST_ERROR_RESOLUTION = False
NOTIFY_UCS_ON_START = False

INIT_DELAY = None
if TEST:
    INIT_DELAY = 5
else:
    INIT_DELAY = 75

class TelegramBot:
    def __init__(self, dotenv_tokenname):
        self.bot = None
        self.dotenv_tokenname = dotenv_tokenname
        self.API_KEY = os.getenv(dotenv_tokenname)
        print(f'[{utils.get_time()}] [TELEGRAM BOT] Starting telegram bot with api token {dotenv_tokenname} '
              f'in .env file...')
 
    def start_bot(self):
        self.bot = telebot.TeleBot(self.API_KEY)
        print(f'[{utils.get_time()}] [TELEGRAM BOT {self.dotenv_tokenname}] Telegram bot started! ✔')
        return self.bot

def is_from_ucs(message):
    if message.from_user.username == os.getenv('ALEX_TELEGRAM_USERNAME'):
        return 'Alex'
    elif message.from_user.username == os.getenv('EGOR_TELEGRAM_USERNAME') or \
            message.from_user.username == os.getenv('EGOR_SECOND_TELEGRAM_USERNAME'):
        return 'Egor'
    elif message.from_user.username == os.getenv('VOVA_TELEGRAM_USERNAME') or \
            message.from_user.username == os.getenv('VOVA_SECOND_TELEGRAM_USERNAME'):
        return 'Vova'
    elif message.from_user.username == os.getenv('Ivan_TELEGRAM_USERNAME'):
        return 'Ivan'
    else:
        return False


def is_thank_you(message):
    lowered = message.text.lower()
    thank_you_messages = (
        'thanks', 'thank', 'danke', 'dank'
    )
    greetings_messages = (
        'hi', 'hello', 'hallo', 'hey'
    )
    for th_msg in thank_you_messages:
        if th_msg in lowered:
            for gr_msg in greetings_messages:
                if gr_msg in lowered:
                    return False
            return True
    return False

def is_resolution_message(message):
    if 'done' in message.text.lower() or 'erledigt' in message.text.lower():
        return True


class UCSAustriaChanel:
    def __init__(self, bot, inits):
        if not TEST:
            self.chat_id = os.getenv('UCS_AUSTRIA_CHAT_ID')
        else:
            self.chat_id = os.getenv('TEST_UCS_SUPPORT_CHAT_ID')
        self.bot = bot
        self.launch_time = time.time()
        to_send = ''
        self.sent_messages = []
        for init in inits:
            to_send += f'\n✅{init}'
        if NOTIFY_UCS_ON_START:
            self.send_message(f'Бот запущен на этих каналах:{to_send}')
            self.send_message(f'Сегодня сапортит {support_wks.supporting_today()}')
            device_info = utils.get_device_info()
            del to_send
            to_send = 'Device info:'
            for key, value in device_info.items():
                to_send = to_send + f"\n{key}: {value}"
            self.send_message(to_send)
        threading.Thread(target=self.sender).start()

    def send_message(self, message_text):
        self.bot.send_message(self.chat_id, message_text, disable_notification=1)

    def request_problem_resoluion_codes(self, row, employee, restaurant_name):
        def check_for_replies(id, stop_event):
            while not stop_event.is_set():
                try:
                    updates = self.bot.get_updates()
                    for update in updates:
                        if update.message and update.message.reply_to_message:
                            if update.message.reply_to_message.message_id == id:
                                print(f'[{utils.get_date_and_time()}] Reply to issue {id} received')
                                stop_event.set()
                                error_code = update.message.text.split(' ')[0]
                                resol_code = update.message.text.split(' ')[1]
                                support_data_wks.update_problem_resolution_codes(row, error_code, resol_code)
                                self.send_message(f'Reply to issue {id} received and updated')
                            else:
                                print(f'This was a reply but not to correct message'
                                      f'\nupdate.message.reply_to_message.message_id = '
                                      f'{update.message.reply_to_message.message_id}\n'
                                      f'ID - {id}')
                except Exception as e:
                    print(f'Error {e}!!!')

        if (time.time() - self.launch_time) <= INIT_DELAY:
            print(f'[{utils.get_time()}] [UCS MAIN CHANEL] Initialisation not yet complete. ⏰'
                  f'\n\t[REMAINING FOR INIT] {INIT_DELAY - (time.time() - self.launch_time)}')
            return  # If bot was started less than a minute ago
        self.sent_messages.append(
            (self.bot.send_message(chat_id = self.chat_id, text = f'{employee}, please specify '
                                 f'problem code and resolution code '
                                f'for issue that you resolved in {restaurant_name}').message_id))
        stop_event = threading.Event()
        threading.Thread(target=check_for_replies,
                         args=(self.sent_messages[len(self.sent_messages)-1],
                               stop_event,)).start()




    def sender(self):
        while True:
            hh_mm_ss_formattime_now = datetime.datetime.now().strftime("%H:%M:%S")=='08:00:00'
            if hh_mm_ss_formattime_now=='08:00:00':
                to_p = os.getenv(support_wks.supporting_today().upper() + '_TELEGRAM_USERNAME')
                self.send_message(f'SH reminder @{to_p}')
            elif hh_mm_ss_formattime_now == '23:59:00':
                result = support_data_wks.today_results()
                self.send_message(f'Results for supporting today:')
            time.sleep(1)


class TelegramChanel:
    statuses = (
        'resolved', 'unresolved', 'unknown', 'locked'
    )
    warnings = (
        'warning1', 'warning2', 'warning3', 'warning4', 'warning5', 'no warning'
    )

    def __init__(self, dotenv_name, bot, language, main_chanel):
        self.start_time = None
        self.launch_time = time.time()
        self.dotenv_name = dotenv_name
        self.str_name = dotenv_name[:-7].replace('_', ' ').lower()
        self.chat_id = os.getenv(dotenv_name)
        self.bot = bot
        self.language = language
        self.main_chanel = main_chanel
        if len(sys.argv) > 1 and sys.argv[1] == 'updated':
            self.status = 'resolved'
        else:
            self.status='unknown'
            self.send_message(f'Resolution status unknow. @vova_ucs please specify current chanel status')
        self.warning = 'no warning'
        print(f'[{utils.get_time()}] [\t{self.str_name.upper()} TELEGRAM CHANEL] Initialising telegram chanel at chat {self.chat_id} '
              f'... With this params: Status={self.status}, Warning={self.warning}, Language={self.language}')
        print(
            f'[{utils.get_time()}]\t [{self.str_name.upper()} TELEGRAM CHANEL] '
            f'Starting message handler (incoming messages monitoring)...')

        self.start_monitoring()

    def send_message(self, message):
        print(f'[{utils.get_time()}] [{self.str_name} CHANNEL] Sending this message to chanel: 💬⬆️\n\t{message}')
        self.bot.send_message(self.chat_id, message, disable_notification=START_MUTED)

    def make_call_to(self, employee, phone):
        print(f'[{utils.get_time()}]\t[CALLING] {employee} is now beeing called on {phone} phone ⚠️')
        call_employee(employee=employee, cellphone=phone, chanel_name=self.str_name)

    def warning_thread(self, stop_event):
        print(f'[{utils.get_time()}] [{self.str_name.upper()} WARNING THREAD] '
              f'Thread for warning monitoring has bee started')
        seconds_elapsed = 0
        timings = {
            'warning1': 60 * 3,
            'warning2': 60 * 5,
            'warning3': 60 * 7,
            'warning4': 60 * 8,
            'warning5': 60 * 10
        }
        if TEST:
            timings = {
                'warning1': 3,
                'warning2': 5,
                'warning3': 7,
                'warning4': 8,
                'warning5': 10
            }
        try:
            while not stop_event.is_set():
                time.sleep(1)
                seconds_elapsed += 1
                if seconds_elapsed == timings['warning1']:
                    print(f'[{utils.get_time()}] [{self.str_name.upper()} NEW WARNING STATUS] Changing warning '
                          f'status to warning 1 and calling responsible employee')
                    self.warning = 'warning1'
                    # Call responsible
                    self.make_call_to(employee='main', phone='main')

                elif seconds_elapsed == timings['warning2']:
                    print(f'[{utils.get_time()}] [{self.str_name.upper()} NEW WARNING STATUS] Changing warning '
                          f'status to warning 2 and calling responsible second cellphone, pinging another responsible')
                    self.warning = 'warning2'
                    # Call seconds cellphone (if exists), ping another support employee
                    self.ping_second_responsible()
                    self.make_call_to('main', 'second')

                elif seconds_elapsed == timings['warning3']:
                    print(f'[{utils.get_time()}] [{self.str_name.upper()} NEW WARNING STATUS] Changing warning '
                          f'status to warning 3 and calling second employee')
                    self.warning = 'warning3'
                    # Call second employee, ping third
                    self.ping_third_responsible()
                    self.make_call_to('second', 'main')

                elif seconds_elapsed == timings['warning4']:
                    print(f'[{utils.get_time()}] [{self.str_name.upper()} NEW WARNING STATUS] Changing warning '
                          f'status to warning 4 and pinging Alex')
                    print(f'\t[PINGING] Alex has been pinged')
                    self.warning = 'warning4'
                    # Ping Alex
                    self.send_message("@" + os.getenv('ALEX_TELEGRAM_USERNAME'))

                elif seconds_elapsed == timings['warning5']:
                    print(f'[{utils.get_time()}] [{self.str_name.upper()} NEW WARNING STATUS] Changing warning'
                          f' status to warning 5 and calling Alex')
                    self.warning = 'warning5'
                    # Call Alex
                    self.make_call_to('Alex', 'main phone')
                    print(f'[{utils.get_time()}] \t[FINAL WARNING ❌] This was last warning. Exiting warning thread... ⚠️')
                    stop_event.set()
        except Exception as e:
            print(f'[{utils.get_date_and_time()}] [WARNING ISSUE THREAD] An error occured when running issue thread: '
                  f'{e}')

    def ping_responsible(self):
        to_ping_str = support_wks.supporting_today()
        print(f'[{utils.get_time()}]\t[PINGING] {to_ping_str} has been pinged ⚠️')
        if to_ping_str == 'Egor':
            if os.getenv("EGOR_SECOND_TELEGRAM_USERNAME") != '':
                self.send_message(
                    f"@{os.getenv('EGOR_TELEGRAM_USERNAME')} @{os.getenv('EGOR_SECOND_TELEGRAM_USERNAME')}")
            else:
                self.send_message(f"@{os.getenv('EGOR_TELEGRAM_USERNAME')}")
        elif to_ping_str == 'Vova':
            if os.getenv("VOVA_SECOND_TELEGRAM_USERNAME") != '':
                self.send_message(
                    f"@{os.getenv('VOVA_TELEGRAM_USERNAME')} @{os.getenv('VOVA_SECOND_TELEGRAM_USERNAME')}")
            else:
                self.send_message(f"@{os.getenv('VOVA_TELEGRAM_USERNAME')}")
        elif to_ping_str == 'Ivan':
            if os.getenv("Ivan_SECOND_TELEGRAM_USERNAME") != '':
                self.send_message(
                    f"@{os.getenv('Ivan_TELEGRAM_USERNAME')} @{os.getenv('Ivan_SECOND_TELEGRAM_USERNAME')}")
            else:
                self.send_message(f"@{os.getenv('Ivan_TELEGRAM_USERNAME')}")

    def ping_second_responsible(self):
        supporter = support_wks.supporting_today()
        to_ping_str = None
        if supporter == 'Egor':
            to_ping_str = 'Vova'
        elif supporter == 'Vova':
            to_ping_str = 'Egor'
        elif supporter == 'Ivan':
            to_ping_str = 'Egor'
        if os.getenv(f'{to_ping_str.upper()}_SECOND_TELEGRAM_USERNAME') != '':
            self.send_message(f"@{os.getenv(f'{to_ping_str.upper()}_TELEGRAM_USERNAME')} "
                              f"@{os.getenv(f'{to_ping_str.upper()}_SECOND_TELEGRAM_USERNAME')}")
        else:
            self.send_message(f"@{os.getenv(f'{to_ping_str.upper()}_TELEGRAM_USERNAME')}")
        print(f'[{utils.get_time()}]\t[PINGING] {to_ping_str} has been pinged ⚠️')

    def ping_third_responsible(self):
        supporter = support_wks.supporting_today()
        to_ping_str = None
        if supporter == 'Egor':
            to_ping_str = 'Ivan'
        elif supporter == 'Vova':
            to_ping_str = 'Ivan'
        elif supporter == 'Ivan':
            to_ping_str = 'Vova'
        if os.getenv(f'{to_ping_str.upper()}_SECOND_TELEGRAM_USERNAME') != '':
            self.send_message(f"@{os.getenv(f'{to_ping_str.upper()}_TELEGRAM_USERNAME')} "
                              f"@{os.getenv(f'{to_ping_str.upper()}_SECOND_TELEGRAM_USERNAME')}")
        else:
            self.send_message(f"@{os.getenv(f'{to_ping_str.upper()}_TELEGRAM_USERNAME')}")
        print(f'[{utils.get_time()}]\t[PINGING] {to_ping_str} has been pinged ⚠️')

    def start_monitoring(self):
        print(f'[{utils.get_time()}] [{self.str_name} TELEGRAM CHANEL] Started incoming messages monitoring ✅')
        self.start_time = None

        @self.bot.message_handler(func=lambda message: True)
        def monitor_incoming(message):
            if message.photo == None:
                lowered_message = message.text.lower()
            else:
                if message.caption:
                    message.text = message.caption
                    lowered_message = message.text.lower()
                else:
                    lowered_message = ''
            print(f'[{utils.get_time()}] [{self.str_name} TELEGRAM CHANEL] Received new message, message text: '
                  f'{message.text}, from {message.from_user.username}')

            # Check whether the actuation time has been elapsed to fight with issue #2
            if (time.time() - self.launch_time) <= INIT_DELAY:
                print(f'[{utils.get_time()}] [{self.str_name} CHANEL] Initialisation not yet complete. ⏰'
                      f'\n\t[REMAINING FOR INIT] {INIT_DELAY - (time.time() - self.launch_time)}')
                return  # If bot was started less than a minute ago

            # Update chat_id and .env file
            if self.chat_id!=message.chat.id:
                print(f'[{utils.get_time()} {self.str_name.upper()} TG CHANEL] Difference in chat_id!!!\n'
                      f'\t.env file shows -- {self.chat_id}, actual from message.chat_id -- {message.chat.id}')
                self.chat_id=message.chat.id


            # """-------------Change status of telegram chanel from unknown-------------"""
            if is_from_ucs(message) and self.status == 'unknown':
                for status in TelegramChanel.statuses:
                    if status == lowered_message:
                        stat_loc = lowered_message.find(status)
                        new_stat = lowered_message[stat_loc:len(status) + stat_loc]
                        self.status = new_stat
                        self.bot.send_message(self.chat_id, text=f'Changed status of '
                                                                 f'{self.dotenv_name[:-7]} to {self.status}',
                                              disable_notification=1)
                        print(f'[{utils.get_time()}] [STATUS SET UP] new status for this chanel '
                              f'has been set to {self.status} ✔')
                        return
                print(f'[{utils.get_time()}] [STATUS STILL UNKNOWN] UCS employee did not set new chanel status! '
                      f'Message does not contain new status!')
            # """-----------------------------------------------------------------------"""

            # """------------Create new issue tech report---Start warning thread--------"""
            elif self.status == 'resolved' and not is_from_ucs(message) and not is_thank_you(message):
                print(f'[{utils.get_time()}] [{self.str_name} TELEGRAM CHANEL] New issue report ⚠! Warning level 0')
                self.status = 'unresolved'
                self.warning = 'warning0'
                self.start_time = time.time()
                self.ping_responsible()
                print(f'[{utils.get_time()}] [{self.str_name} TELEGRAM CHANEL] Responsible for support employee has been pinged')
                self.stop_event = threading.Event()
                print(f'[{utils.get_time()}] [{self.str_name} TELEGRAM CHANEL] Starting issue thread...')
                self.warning_thread = threading.Thread(target=self.warning_thread, args=(self.stop_event,))
                self.warning_thread.start()
            # """-----------------------------------------------------------------------"""

            # """----------------Not an issue. Locking chanel for discussion------------------"""
            elif is_from_ucs(message) and (lowered_message == 'not an issue' or lowered_message == 'lock'):
                # or 'kein problem' in lowered_message:
                self.status = 'locked'
                self.stop_event.set()
                self.warning = 'no warning'
                print(f'[{utils.get_time()}] [{self.str_name.upper()} TG CHANEL] false issue. Setting to locked :|')
                self.send_message('Okay, removing issue. Locking bot for further discussion. Type "Unlock" to unlock')
            # """-----------------------------------------------------------------------"""

            # """-----------------Unlocking chanel--------------------------------------"""
            elif is_from_ucs(message) and lowered_message == 'unlock' and self.status == 'locked':
                self.status = 'resolved'
                print(f'[{utils.get_time()} [{self.str_name.upper()} TG CHANEL] unlocking chanel for further monitor')
                self.send_message('Chanel unlocked, continuing monitoring')
            # """-----------------------------------------------------------------------"""

            # """-------------Remove warning, but leave unresolved status---------------"""
            elif is_from_ucs(message) and self.status == 'unresolved' and self.warning != 'no warning':
                who_answered_to_report = is_from_ucs(message)
                self.send_message(f'{who_answered_to_report} is now resolving the issue in {self.str_name} after '
                                  f'{self.warning}')
                self.responsed_at_warning_level = self.warning
                self.stop_event.set()
                self.response_time = time.time()
                print(f"[{utils.get_time()}] [{self.str_name.upper()} TG CHANEL] {who_answered_to_report} replied to "
                      f"report and is now managing situation. Status: 'unresolved', Warning: no warning ❤️")
                self.warning = 'no warning'
                # del self.warning_thread
            # """-----------------------------------------------------------------------"""

            # """-----------------------Set status to resolved--------------------------"""
            elif self.status == 'unresolved' and self.warning == 'no warning' and is_resolution_message(message) \
                    and is_from_ucs(message):
                self.status = 'resolved'
                if self.start_time is not None:
                    end_time = time.time()
                    elapsed_time = end_time - self.start_time
                    hours, rem = divmod(elapsed_time, 3600)
                    minutes, seconds = divmod(rem, 60)
                    if hours > 0:
                        elapsed = "{} hours {} minutes {} seconds".format(int(hours), int(minutes), int(seconds))
                    elif minutes > 0:
                        elapsed = "{} minutes {} seconds".format(int(minutes), int(seconds))
                    else:
                        elapsed = "{} seconds".format(int(seconds))
                    if is_from_ucs(message).lower()=='Ivan':
                        resolved_by = 'Ivan'
                    else:
                        resolved_by = is_from_ucs(message)
                    self.send_message(f'Issue resolved by {is_from_ucs(message)} in {elapsed}')
                    rp_time = self.response_time - self.start_time
                    print(f"[{utils.get_time()}] [{self.str_name.upper()} TG CHANEL] {is_from_ucs(message)} resolved "
                          f"issue in {elapsed}")
                    row = support_data_wks.upload_issue_data(
                        response_time=rp_time, resolution_time=elapsed_time,
                        person_name=is_from_ucs(message), restaurant_name=self.str_name,
                        warning_status=self.responsed_at_warning_level
                    )
                    if REQUEST_ERROR_RESOLUTION:
                        self.main_chanel.request_problem_resoluion_codes(row, is_from_ucs(message), self.str_name)
                    to_append = f'{datetime.datetime.now().strftime("%A, %dth %B, %H:%M:%S")} issue resolved by ' \
                                f' {is_from_ucs(message)} in ' \
                                f'{elapsed_time} seconds. Response time: {end_time - self.response_time}\n'
                    if is_from_ucs(message).lower()=='vova':
                        with open('statistics/vova.txt', 'a') as f:
                            f.write(to_append)
                    elif is_from_ucs(message).lower()=='egor':
                        with open('statistics/egor.txt', 'a') as f:
                            f.write(to_append)
                    elif is_from_ucs(message).lower()=='Ivan':
                        with open('statistics/Ivan.txt') as f:
                            f.write(to_append)
                else:
                    print(f"[{utils.get_time()}] [{self.str_name.upper()} TG CHANEL] {is_from_ucs(message)} "
                          f"resolved issue")
                    self.send_message(f'Issue resolved by {is_from_ucs(message)}')
            # """-----------------------------------------------------------------------"""

            # """----------------------Nothing happened---------------------------------"""
            else:
                print(f'[{utils.get_time()}]\t[{self.str_name.upper()} TELEGRAM CHANEL] Message is '
                      f'discussion of problem. Doing nothing'.lower())
            # """-----------------------------------------------------------------------"""

        @self.bot.message_handler(content_types=['photo', 'video'])
        def photo_reaction(message):
            print(f'[{utils.get_date_and_time()}] [{utils.get_time()}] [{self.str_name} CHANNEL] An image '
                  f'or video was sent 📸')
            if not message.text:
                message.text = ''
            monitor_incoming(message)

        self.bot.polling(non_stop=True)


def create_telegram_channel(channel_id, language, bot, main_chanel):
    return TelegramChanel(channel_id, bot, language, main_chanel)


channel_params = {
    'WoerglChanel': ('KFC_WOERGL_CHATID', 'UCS_Support_Woergl_Bot_TELEGRAM_API_TOKEN', 'de'),
    'MilChanel': ('KFC_MIL_CHATID', 'Ucs_Support_Mil_Bot_TELEGRAM_API_TOKEN', 'de'),
    'KosiceChanel': ('KFC_KOSICE_CHATID', 'Ucs_Support_Kosice_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'DpChanel': ('KFC_DP_CHAT_ID', 'Ucs_Support_Dp_Bot_TELEGRAM_API_TOKEN', 'de'),
    'FloChanel': ('KFC_FLO_CHAT_ID', 'Ucs_Support_Flo_Bot_TELEGRAM_API_TOKEN', 'de'),
    'BrnChanel': ('KFC_BRN_CHAT_ID', 'UCS_Support_Brn_Bot_TELEGRAM_API_TOKEN', 'de'),
    'BoryMallChanel': ('KFC_BORYMALL_CHAT_ID', 'UCS_Support_Borymall_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'TrnChanel': ('KFC_TRN_CHAT_ID', 'UCS_Support_Trn_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'AuParkChanel': ('KFC_AUPARK_CHAT_ID', 'UCS_Support_Aupark_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'EuroveaChanel': ('KFC_EUROVEA_CHAT_ID', 'UCS_Support_Eurovea_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'NivyChanel': ('KFC_NIVY_CHAT_ID', 'UCS_Support_Nivy_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'TrnDrChanel': ('KFC_TRN_DR_CHAT_ID', 'UCS_Support_Trn_Dr_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'ScsChanel': ('KFC_SCS_CHAT_ID', 'UCS_Support_Scs_Bot_TELEGRAM_API_TOKEN', 'de'),
    'MhsChanel': ('KFC_MHS_CHAT_ID', 'UCS_Support_Mhs_Bot_TELEGRAM_API_TOKEN', 'de'),
    'ParChanel': ('KFC_PAR_CHAT_ID', 'UCS_Support_Par_Bot_TELEGRAM_API_TOKEN', 'de'),
    'ColChanel': ('KFC_COL_CHAT_ID', 'UCS_Support_Col_Bot_TELEGRAM_API_TOKEN', 'de'),
    'ColChanel': ('KFC_COL_CHAT_ID', 'UCS_Support_Col_Bot_TELEGRAM_API_TOKEN', 'de'),
    'VivoChanel': ('KFC_VIVO_CHAT_ID', 'UCS_Support_Vivo_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'RelaxChanel': ('KFC_RELAX_CHAT_ID', 'UCS_Support_Relax_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'LugChanel': ('KFC_LUG_CHAT_ID', 'UCS_Support_Lug_Bot_TELEGRAM_API_TOKEN', 'de'),
    'PlLinzChanel': ('KFC_PL_LINZ_CHAT_ID', 'UCS_Support_Pl_Linz_Bot_TELEGRAM_API_TOKEN', 'de'),
    'EuropaBbChanel': ('KFC_EUROPA_BB_CHAT_ID', 'UCS_Support_Europa_Bb_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'ZvonlenChanel': ('KFC_ZVLN_CHAT_ID', 'UCS_Support_Zvln_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'TestChanel': ('TEST_CHAT_ID', 'UCS_Support_Bot_TELEGRAM_API_TOKEN', 'de')
}


def return_channels_to_init():
    if TEST:
        channels_to_init = [name for name in channel_params.keys() if name == 'TestChanel']
    else:
        channels_to_init = [name for name in channel_params.keys() if name != 'TestChanel']
    return channels_to_init


def test_bots_starting(channels_to_init):
    start_failed = []
    for channel_name in channels_to_init:
        try:
            print(TelegramBot(dotenv_tokenname=channel_params[channel_name][1]))
            print(f'[{utils.get_time()}] [{channel_name.upper()} ✅] Started successfully.' + '\n' + '_' * 60)
        except:
            print(f'[{utils.get_time()}] [{channel_name.upper()} ❌] FAILED to start...')
            start_failed.append(channel_params[channel_name][1])
            continue
        # time.sleep(0.5)
    if len(start_failed) != 0:
        print(f'[{utils.get_time()}] [BOT START FAIL] This channels failed to start:')
        for channel in start_failed:
            print(f'\t{channel}')
    else:
        print(f'[{utils.get_time()}] [BOT START SUCCESS] Every bot can start properly')
        start_failed = False
    return start_failed


def start_bot_chanel_threads(channels_to_init, main_chanel):
    for channel_name in channels_to_init:
        bot = TelegramBot(dotenv_tokenname=channel_params[channel_name][1]).start_bot()
        print('- '*40)
        print(f'[{utils.get_time()}] [THREAD {channel_name.upper()}] Starting thread 🔁')
        threading.Thread(target=create_telegram_channel, args=(channel_params[channel_name][0],
                                                               channel_params[channel_name][2],
                                                               bot, main_chanel)).start()
        print(f'\n[{utils.get_time()}]\t[THREAD {channel_name.upper()}] Started ✅✅✅')
        time.sleep(1)
    print('='*80)
    print(f'[{utils.get_time()}] [ALL BOT THREADS STARTED] All specified bots were started 👍')


def input_thread():
    def on_kill():
        print(f"[{utils.get_time()}] Kill switch activated. Exiting gracefully...")
        # Perform any necessary cleanup or finalization tasks here
        os._exit(0)  # Terminate the script immediately

    def on_update():
        print(f"[{utils.get_time()}] Running update.bat...")
        # Run the update.bat file
        os.system("update.bat")

    # Create the tkinter window
    window = tk.Tk()
    window.title("Control Panel")
    window.geometry("200x100")
    window.resizable(False, False)  # Set window size as fixed

    # Configure a dark-grey color scheme
    bg_color = "#333333"  # Dark grey background color
    fg_color = "#ffffff"  # White foreground color

    window.configure(bg=bg_color)

    # Create a frame to contain the buttons
    button_frame = tk.Frame(window, bg=bg_color)
    button_frame.pack(fill="both", expand=True)

    # Define a bold font style
    button_font = font.Font(weight="bold")

    # Create the buttons
    kill_button = tk.Button(button_frame, text="Kill", command=on_kill, bg=bg_color, fg=fg_color, font=button_font)
    kill_button.pack(side="left", fill="both", expand=True)

    update_button = tk.Button(button_frame, text="Update", command=on_update, bg=bg_color, fg=fg_color,
                              font=button_font)
    update_button.pack(side="right", fill="both", expand=True)

    # Start the tkinter event loop
    window.mainloop()


if __name__ == '__main__':
    if platform.system()=='Windows':
        input_thread = threading.Thread(target=input_thread)
        input_thread.start()
    to_init = return_channels_to_init()

    # Initialise cellphone calling server that communicates later with android client
    call_server = threading.Thread(target=sip_call.start_telephony_server)
    # call_server.start()

    ucs_chanel = None
    if not TEST:
        ucs_chanel = UCSAustriaChanel(telebot.TeleBot(os.getenv("UCS_Support_Bot_TELEGRAM_API_TOKEN")), to_init)
    else:
        ucs_chanel = UCSAustriaChanel(telebot.TeleBot(os.getenv("TEST_UCS_SUPPORT_Bot_TELEGRAM_API_TOKEN")), to_init)
    test_bots_starting(to_init)
    start_bot_chanel_threads(to_init, ucs_chanel)

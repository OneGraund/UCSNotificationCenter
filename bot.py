import datetime
import os
import sys
import dotenv
import threading
import time
import telebot
from sheets import SupportWKS, SupportDataWKS
from sip_call import call_employee

dotenv.load_dotenv()

support_wks = SupportWKS()
support_data_wks = SupportDataWKS()

TEST = False
START_MUTED = True



class TelegramBot:
    def __init__(self, dotenv_tokenname):
        self.bot = None
        self.dotenv_tokenname = dotenv_tokenname
        self.API_KEY = os.getenv(dotenv_tokenname)
        print(f'[TELEGRAM BOT] Starting telegram bot with api token {dotenv_tokenname} in .env file...')

    def start_bot(self):
        self.bot = telebot.TeleBot(self.API_KEY)
        print(f'[TELEGRAM BOT {self.dotenv_tokenname}] Telegram bot started! ✔')
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
    elif message.from_user.username == os.getenv('YARO_TELEGRAM_USERNAME'):
        return 'Yaro'
    else:
        return False


def is_thank_you(message):
    lowered = message.text.lower()
    thank_you_messages = (
        'thanks', 'thank', 'danke', 'dank'
    )
    for msg in thank_you_messages:
        if msg in lowered:
            return True
    return False

def is_resolution_message(message):
    if 'done' in message.text.lower() or 'erledigt' in message.text.lower():
        return True


class UCSAustriaChanel:
    def __init__(self, bot, inits):
        self.chat_id = os.getenv('UCS_AUSTRIA_CHAT_ID')
        self.bot = bot
        to_send = ''
        for init in inits:
            to_send += f'{init}\n'
        self.send_message(f'UCS Notification Center has started for this chanels:\n{to_send}')
        threading.Thread(target=self.sender).start()

    def send_message(self, message_text):
        self.bot.send_message(self.chat_id, message_text)

    def sender(self):
        while True:
            if datetime.datetime.now().strftime("%H:%M:%S")=='08:00:00':
                to_p = os.getenv(support_wks.supporting_today().upper() + '_TELEGRAM_USERNAME')
                self.send_message(f'SH reminder @{to_p}')
            time.sleep(1)


class TelegramChanel:
    statuses = (
        'resolved', 'unresolved', 'unknown'
    )
    warnings = (
        'warning1', 'warning2', 'warning3', 'warning4', 'warning5', 'no warning'
    )

    def __init__(self, dotenv_name, bot, language):
        self.start_time = None
        self.dotenv_name = dotenv_name
        self.str_name = dotenv_name[:-7].replace('_', ' ').lower()
        self.chat_id = os.getenv(dotenv_name)
        self.bot = bot
        self.language = language
        if sys.argv[1]=='all_resolved':
            self.status='resolved'
        else:
            self.status = 'unknown'
        self.warning = 'no warning'
        # self.send_message(f'Resolution status unknow. @vova_ucs please specify current chanel status')
        if not START_MUTED:
            self.bot.send_message(self.chat_id, text=f'Resolution status unknow. @vova_ucs '
                                                        f'please specify current chanel status',
                                  disable_notification=1)
        print(f'[\t{self.str_name.upper()} TELEGRAM CHANEL] Initialising telegram chanel at chat {self.chat_id} '
              f'... With this params: Status={self.status}, Warning={self.warning}, Language={self.language}')
        print(
            f'\t [{self.str_name.upper()} TELEGRAM CHANEL] Starting message handler (incoming messages monitoring)...')

        self.start_monitoring()

    def send_message(self, message):
        self.bot.send_message(self.chat_id, message)

    def make_call_to(self, employee, phone):
        print(f'\t[CALLING] {employee} is now beeing called on {phone} phone ⚠️')
        call_employee(employee=employee, cellphone=phone, chanel_name=self.str_name)

    def warning_thread(self, stop_event):
        print(f'[{self.str_name.upper()} WARNING THREAD] Thread for warning monitoring has bee started')
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
        while not stop_event.is_set():
            time.sleep(1)
            seconds_elapsed += 1
            if seconds_elapsed == timings['warning1']:
                print(f'[{self.str_name.upper()} NEW WARNING STATUS] Changing warning status to warning 1 and '
                      f'calling responsible employee')
                self.warning = 'warning1'
                # Call responsible
                self.make_call_to(employee='main', phone='main')

            elif seconds_elapsed == timings['warning2']:
                print(f'[{self.str_name.upper()} NEW WARNING STATUS] Changing warning status to warning 2 and'
                      f' calling responsible second cellphone, pinging another responsible')
                self.warning = 'warning2'
                # Call seconds cellphone (if exists), ping another support employee
                self.ping_second_responsible()
                self.make_call_to('main', 'second')

            elif seconds_elapsed == timings['warning3']:
                print(f'[{self.str_name.upper()} NEW WARNING STATUS] Changing warning status to warning 3 and'
                      f' calling second employee')
                self.warning = 'warning3'
                # Call second employee, ping third
                self.ping_third_responsible()
                self.make_call_to('second', 'main')

            elif seconds_elapsed == timings['warning4']:
                print(f'[{self.str_name.upper()} NEW WARNING STATUS] Changing warning status to warning 4 and'
                      f' pinging Alex')
                print(f'\t[PINGING] Alex has been pinged')
                self.warning = 'warning4'
                # Ping Alex
                self.send_message("@" + os.getenv('ALEX_TELEGRAM_USERNAME'))

            elif seconds_elapsed == timings['warning5']:
                print(f'[{self.str_name.upper()} NEW WARNING STATUS] Changing warning status to warning 5 and'
                      f' calling Alex')
                self.warning = 'warning5'
                # Call Alex
                self.make_call_to('Alex', 'main phone')
                print(f'\t[FINAL WARNING ❌] This was last warning. Exiting warning thread... ⚠️')
                stop_event.set()

    def ping_responsible(self):
        to_ping_str = support_wks.supporting_today()
        print(f'\t[PINGING] {to_ping_str} has been pinged ⚠️')
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
        elif to_ping_str == 'Yaro':
            if os.getenv("YARO_SECOND_TELEGRAM_USERNAME") != '':
                self.send_message(
                    f"@{os.getenv('YARO_TELEGRAM_USERNAME')} @{os.getenv('YARO_SECOND_TELEGRAM_USERNAME')}")
            else:
                self.send_message(f"@{os.getenv('YARO_TELEGRAM_USERNAME')}")

    def ping_second_responsible(self):
        supporter = support_wks.supporting_today()
        to_ping_str = None
        if supporter == 'Egor':
            to_ping_str = 'Vova'
        elif supporter == 'Vova':
            to_ping_str = 'Egor'
        elif supporter == 'Yaro':
            to_ping_str = 'Egor'
        if os.getenv(f'{to_ping_str.upper()}_SECOND_TELEGRAM_USERNAME') != '':
            self.send_message(f"@{os.getenv(f'{to_ping_str.upper()}_TELEGRAM_USERNAME')} "
                              f"@{os.getenv(f'{to_ping_str.upper()}_SECOND_TELEGRAM_USERNAME')}")
        else:
            self.send_message(f"@{os.getenv(f'{to_ping_str.upper()}_TELEGRAM_USERNAME')}")
        print(f'\t[PINGING] {to_ping_str} has been pinged ⚠️')

    def ping_third_responsible(self):
        supporter = support_wks.supporting_today()
        to_ping_str = None
        if supporter == 'Egor':
            to_ping_str = 'Yaro'
        elif supporter == 'Vova':
            to_ping_str = 'Yaro'
        elif supporter == 'Yaro':
            to_ping_str = 'Vova'
        if os.getenv(f'{to_ping_str.upper()}_SECOND_TELEGRAM_USERNAME') != '':
            self.send_message(f"@{os.getenv(f'{to_ping_str.upper()}_TELEGRAM_USERNAME')} "
                              f"@{os.getenv(f'{to_ping_str.upper()}_SECOND_TELEGRAM_USERNAME')}")
        else:
            self.send_message(f"@{os.getenv(f'{to_ping_str.upper()}_TELEGRAM_USERNAME')}")
        print(f'\t[PINGING] {to_ping_str} has been pinged ⚠️')

    def start_monitoring(self):
        print(f'[{self.str_name} TELEGRAM CHANEL] Started incoming messages monitoring ✅')
        self.start_time = None

        @self.bot.message_handler(func=lambda message: True)
        def monitor_incoming(message):
            lowered_message = message.text.lower()
            print(f'[{self.str_name} TELEGRAM CHANEL] Received new message, message text: {message.text}, from '
                  f'{message.from_user.username}')
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
                        print(f'[STATUS SET UP] new status for this chanel has been set to {self.status} ✔')
                        return
                print(f'[STATUS STILL UNKNOWN] UCS employee did not set new chanel status! Message does not'
                      ' contain new status!')
            # """-----------------------------------------------------------------------"""

            # """------------Create new issue tech report---Start warning thread--------"""
            elif self.status == 'resolved' and not is_from_ucs(message) and not is_thank_you(message):
                print(f'[{self.str_name} TELEGRAM CHANEL] New issue report ⚠! Warning level 0')
                self.status = 'unresolved'
                self.warning = 'warning0'
                self.start_time = time.time()
                self.ping_responsible()
                print(f'[{self.str_name} TELEGRAM CHANEL] Responsible for support employee has been pinged')
                self.stop_event = threading.Event()
                print(f'[{self.str_name} TELEGRAM CHANEL] Starting issue thread...')
                self.warning_thread = threading.Thread(target=self.warning_thread, args=(self.stop_event,))
                self.warning_thread.start()
            # """-----------------------------------------------------------------------"""

            # """----------------Not an issue. False creation of issue------------------"""
            elif is_from_ucs(message) and lowered_message == 'not an issue':
                # or 'kein problem' in lowered_message:
                self.status = 'resolved'
                self.stop_event.set()
                self.warning = 'no warning'
                print(f'[{self.str_name.upper()} TG CHANEL] false issue. Setting to resolved :|')
                self.send_message('Okay, removing issue. Status is now resolved')
            # """-----------------------------------------------------------------------"""

            # """-------------Remove warning, but leave unresolved status---------------"""
            elif is_from_ucs(message) and self.status == 'unresolved' and self.warning != 'no warning':
                who_answered_to_report = is_from_ucs(message)
                self.send_message(f'{who_answered_to_report} is now resolving the issue in {self.str_name} after '
                                  f'{self.warning}')
                self.responsed_at_warning_level = self.warning
                self.stop_event.set()
                self.response_time = time.time()
                print(f"[{self.str_name.upper()} TG CHANEL] {who_answered_to_report} replied to report and is now mana"
                      f"ging situation. Status: 'unresolved', Warning: no warning ❤️")
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
                    self.send_message(f'Issue resolved by {is_from_ucs(message)} in {elapsed}')
                    rp_time = end_time - self.response_time
                    print(f"[{self.str_name.upper()} TG CHANEL] {is_from_ucs(message)} resolved issue in {elapsed}")
                    support_data_wks.upload_issue_data(
                        response_time=rp_time, resolution_time=elapsed_time,
                        person_name=is_from_ucs(message), restaurant_name=self.str_name,
                        warning_status=self.responsed_at_warning_level
                    )
                    to_append = f'{datetime.datetime.now().strftime("%A, %dth %B, %H:%M:%S")} issue resolved by ' \
                                f' {is_from_ucs(message)} in ' \
                                f'{elapsed_time} seconds. Response time: {end_time - self.response_time}'
                    if is_from_ucs(message).lower()=='vova':
                        with open('statistics/vova.txt', 'a') as f:
                            f.write(to_append)
                    elif is_from_ucs(message).lower()=='egor':
                        with open('statistics/egor.txt', 'a') as f:
                            f.write(to_append)
                    elif is_from_ucs(message).lower()=='yaro':
                        with open('statistics/yaro.txt') as f:
                            f.write(to_append)
                else:
                    print(f"[{self.str_name.upper()} TG CHANEL] {is_from_ucs(message)} resolved issue")
                    self.send_message(f'Issue resolved by {is_from_ucs(message)}')
            # """-----------------------------------------------------------------------"""

            # """----------------------Nothing happened---------------------------------"""
            else:
                print(f'\t[{self.str_name.upper()} TELEGRAM CHANEL] Message is discussion of problem. '
                      f'Doing nothing'.lower())
            # """-----------------------------------------------------------------------"""

        time.sleep(2)
        if TEST:
            self.bot.polling()
        else:
            self.bot.infinity_polling()


def create_telegram_channel(channel_id, language, bot):
    return TelegramChanel(channel_id, bot, language)


channel_params = {
    # 'WoerglChanel': ('KFC_WOERGL_CHATID', 'UCS_Support_Woergl_Bot_TELEGRAM_API_TOKEN', 'de'),
    # 'MilChanel': ('KFC_MIL_CHATID', 'Ucs_Support_Mil_Bot_TELEGRAM_API_TOKEN', 'de'),
    # 'KosiceChanel': ('KFC_KOSICE_CHATID', 'Ucs_Support_Kosice_Bot_TELEGRAM_API_TOKEN', 'sk'),
    # 'DpChanel': ('KFC_DP_CHAT_ID', 'Ucs_Support_Dp_Bot_TELEGRAM_API_TOKEN', 'de'),
    # 'FloChanel': ('KFC_FLO_CHAT_ID', 'Ucs_Support_Flo_Bot_TELEGRAM_API_TOKEN', 'de'),
    # 'BrnChanel': ('KFC_BRN_CHAT_ID', 'UCS_Support_Brn_Bot_TELEGRAM_API_TOKEN', 'de'),
    # 'BoryMallChanel': ('KFC_BORYMALL_CHAT_ID', 'UCS_Support_Borymall_Bot_TELEGRAM_API_TOKEN', 'sk'),
    # 'TrnChanel': ('KFC_TRN_CHAT_ID', 'UCS_Support_Trn_Bot_TELEGRAM_API_TOKEN', 'sk'),
    # 'AuParkChanel': ('KFC_AUPARK_CHAT_ID', 'UCS_Support_Aupark_Bot_TELEGRAM_API_TOKEN', 'sk'),
    # 'EuroveaChanel': ('KFC_EUROVEA_CHAT_ID', 'UCS_Support_Eurovea_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'NivyChanel': ('KFC_NIVY_CHAT_ID', 'UCS_Support_Nivy_Bot_TELEGRAM_API_TOKEN', 'sk'),
    # 'TrnDrChanel': ('KFC_TRN_DR_CHAT_ID', 'UCS_Support_Trn_Dr_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'ScsChanel': ('KFC_SCS_CHAT_ID', 'UCS_Support_Scs_Bot_TELEGRAM_API_TOKEN', 'de'),
    # 'MhsChanel': ('KFC_MHS_CHAT_ID', 'UCS_Support_Mhs_Bot_TELEGRAM_API_TOKEN', 'de'),
    # 'ParChanel': ('KFC_PAR_CHAT_ID', 'UCS_Support_Par_Bot_TELEGRAM_API_TOKEN', 'de'),
    # 'ColChanel': ('KFC_COL_CHAT_ID', 'UCS_Support_Col_Bot_TELEGRAM_API_TOKEN', 'de'),
    'VivoChanel': ('KFC_VIVO_CHAT_ID', 'UCS_Support_Vivo_Bot_TELEGRAM_API_TOKEN', 'sk'),
    # 'RelaxChanel': ('KFC_RELAX_CHAT_ID', 'UCS_Support_Relax_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'LugChanel': ('KFC_LUG_CHAT_ID', 'UCS_Support_Lug_Bot_TELEGRAM_API_TOKEN', 'de'),
    # 'PlLinzChanel': ('KFC_PL_LINZ_CHAT_ID', 'UCS_Support_Pl_Linz_Bot_TELEGRAM_API_TOKEN', 'de'),
    'EuropaBbChanel': ('KFC_EUROPA_BB_CHAT_ID', 'UCS_Support_Europa_Bb_Bot_TELEGRAM_API_TOKEN', 'sk'),
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
            print(f'[{channel_name.upper()} ✅] Started successfully.' + '\n' + '_' * 60)
        except:
            print(f'[{channel_name.upper()} ❌] FAILED to start...')
            start_failed.append(channel_params[channel_name][1])
            continue
        # time.sleep(0.5)
    if len(start_failed) != 0:
        print(f'[BOT START FAIL] This channels failed to start:')
        for channel in start_failed:
            print(f'\t{channel}')
    else:
        print(f'[BOT START SUCCESS] Every bot can start properly')
        start_failed = False
    return start_failed


def start_bot_chanel_threads(channels_to_init):
    for channel_name in channels_to_init:
        bot = TelegramBot(dotenv_tokenname=channel_params[channel_name][1]).start_bot()
        print(f'[THREAD {channel_name.upper()}] Starting thread 🔁')
        threading.Thread(target=create_telegram_channel, args=(channel_params[channel_name][0],
                                                               channel_params[channel_name][2], bot,)).start()
        print(f'\n\t[THREAD {channel_name.upper()}] Started ✅✅✅')
        time.sleep(1)


if __name__ == '__main__':
    to_init = return_channels_to_init()
    test_bots_starting(to_init)
    start_bot_chanel_threads(to_init)
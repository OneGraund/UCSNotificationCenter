import datetime
import statistics
import os
import json
import dotenv
import threading
import time
import utils
import telebot
from telebot import types
from telebot.types import ReplyKeyboardRemove
from sip_call import call_employee_with_priority

dotenv.load_dotenv()
NOTIFY_DONE_INTERVAL_MIN = 1

with open('resolution_codes.json', 'r') as resolution_codes_file:
    resol_dict = json.load(resolution_codes_file)




class TelegramBot:
    def __init__(self, dotenv_tokenname):
        self.bot = None
        self.dotenv_tokenname = dotenv_tokenname
        self.API_KEY = os.getenv(dotenv_tokenname)
        print(f'[{utils.get_time()}] [TELEGRAM BOT] Starting telegram bot with api token {dotenv_tokenname} '
              f'in .env file...')

    def start_bot(self):
        self.bot = telebot.TeleBot(self.API_KEY, threaded=True)
        # telebot.logger.setLevel(logging.DEBUG)
        print(f'[{utils.get_time()}] [TELEGRAM BOT {self.dotenv_tokenname}] Telegram bot started! ✔')
        return self.bot


def is_from_ucs(message, employees=None):
    # First we want to parse all employes telegram usernames in format of arrays, where main array contains
    # subarrays even if employe has only one telegram username
    # employes: [Vova, Egor, Yaro, Ivan, Igor, Alex] -> tg_usernames: [[vova_ucs, onegraund], [noname, egor_ucs], …]

    if message is None:
        return 'Bot'

    if employees:
        tg_names = []
        # print(f'[IS_FROM_UCS] Checking whether message was sent from ucs')
        for employee in employees:
            if os.getenv(f'{employee.upper()}_SECOND_TELEGRAM_USERNAME') != '':
                tg_names.append([os.getenv(f"{employee.upper()}_TELEGRAM_USERNAME"),
                                 os.getenv(f"{employee.upper()}_SECOND_TELEGRAM_USERNAME")])
            else:
                tg_names.append([os.getenv(f"{employee.upper()}_TELEGRAM_USERNAME")])

        for emp_id, tg_username in enumerate(tg_names):
            for id, sub_array in enumerate(tg_username):
                if message.from_user.username == sub_array:
                    return employees[emp_id]
        return False
    else:
        if message.from_user.username == os.getenv('ALEX_TELEGRAM_USERNAME'):
            return 'Alex'
        elif message.from_user.username == os.getenv('EGOR_TELEGRAM_USERNAME') or \
                message.from_user.username == os.getenv('EGOR_SECOND_TELEGRAM_USERNAME'):
            return 'Egor'
        elif message.from_user.username == os.getenv('VOVA_TELEGRAM_USERNAME') or \
                message.from_user.username == os.getenv('VOVA_SECOND_TELEGRAM_USERNAME'):
            return 'Vova'
        elif message.from_user.username == os.getenv('IVAN_TELEGRAM_USERNAME'):
            return 'Ivan'
        elif message.from_user.username == os.getenv('IGOR_TELEGRAM_USERNAME'):
            return 'Igor'
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


def generate_buttons(bts_names, markup):
    for button in bts_names:
        markup.add(types.KeyboardButton(button))
    return markup


def get_issues_and_codes(device, issue_type):
    issues_dict = statistics.load_error_descriptions()
    if device in issues_dict and issue_type in issues_dict[device]:
        issues = issues_dict[device][issue_type]
        return [[issue, code] for issue, code in issues.items()]
    else:
        return [["No data found for the given parameters."]]


def get_resolutions_and_codes(device, issue_type):
    if device in resol_dict and issue_type in resol_dict[device]:
        resolutions = resol_dict[device][issue_type]
        return [[issue, code] for issue, code in resolutions.items()]
    else:
        return [["No data found for the given parameters."]]


class UCSAustriaChanel:
    def __init__(self, bot, inits, TEST=False, NOTIFY_UCS_ON_START=1, INIT_DELAY=75,
                 support_wks=None, support_data=None):
        self.support_wks = support_wks
        self.support_data_wks = support_data
        if not TEST:
            self.chat_id = os.getenv('UCS_AUSTRIA_CHAT_ID')
            self.INIT_DELAY = INIT_DELAY
        else:
            self.chat_id = os.getenv('TEST_UCS_SUPPORT_CHAT_ID')
            self.INIT_DELAY = 5
        self.bot = bot
        self.pause_personal_monitoring = False
        self.launch_time = time.time()
        to_send = ''
        self.sent_messages = []
        for init in inits:
            to_send += f'\n✅{init}'
        if NOTIFY_UCS_ON_START:
            self.send_message(f'Бот запущен на этих каналах:{to_send}')
            self.send_message(f'Сегодня сапортит {self.support_wks.supporting_today()}')
            device_info = utils.get_device_info()
            del to_send
            to_send = 'Device info:'
            for key, value in device_info.items():
                to_send = to_send + f"\n{key}: {value}"
            self.send_message(to_send)
        threading.Thread(target=self.personal_chat_monitoring_thread).start()

    def send_message(self, message_text):
        self.bot.send_message(self.chat_id, message_text, disable_notification=1)

    def clear_pending_updates(self):
        print(f'[{utils.get_time()}] [MAIN BOT] [CLEARING PENDING UPDATES] Started clearing updates...')
        try:
            updates = self.bot.get_updates()
            if updates:
                last_update_id = updates[-1].update_id
                # Clear all pending updates
                updates = self.bot.get_updates(offset=last_update_id + 1)
                print("All pending updates have been cleared.")
            else:
                print("No updates to clear.")
        except Exception as e:
            print(f'[{utils.get_time()}] [CLEAR PENDING UPDATES] Error: {e}')

    def request_problem_resoluion_codes(self, row, employee, restaurant_name):
        print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Starting request for error code and resolution'
              f'code. Restaurant name - {restaurant_name}. Deactivating other commands...')
        personal_chat_id = str(os.getenv(f'{employee.upper()}_TELEGRAM_ID'))
        self.pause_personal_monitoring = True
        if employee == 'Bot':
            return

        def request_device_type():
            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Requesting now device type. Checking for '
                  f'updates...')
            markup = types.ReplyKeyboardMarkup(row_width=2)
            device_types = list(statistics.load_error_descriptions().keys())
            with_else = device_types + ['Else']
            markup = generate_buttons(with_else, markup)
            self.bot.send_message(personal_chat_id,
                                  f"Choose device type which you fixed in {restaurant_name}",
                                  reply_markup=markup)

            self.clear_pending_updates()
            while True:
                updates = self.bot.get_updates()
                for update in updates:
                    if update.message and str(update.message.chat.id) == personal_chat_id:
                        if update.message.text in device_types:
                            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Given device '
                                  f'{update.message.text} exists in the list, therefore it is successfully specified')
                            return update.message.text
                        elif update.message.text == 'Else':
                            print(f'[{utils.get_time()}] [REQ ERR SOL] User chose device type "Else" for device type')
                            return 'Else'
                        else:
                            print(f'[{utils.get_time()}] [REQ ERR SOL] Specified device type by user is not in list'
                                  f'. Message text: {update.message.text}')
                            self.bot.send_message(personal_chat_id,
                                                  'Please click on one of the buttons to proceed. If you are trying '
                                                  'to specify device that was not in the list, click "Else"',
                                                  reply_markup=markup, disable_notification=1)
                            self.clear_pending_updates()
                    else:
                        print(f'[{utils.get_time()}] [REQ ERR] Either update does not contain message, or it was not '
                              f'written in correct chat.\n\tChat dump:{update.message.chat} \n\tDump: {update}')
                time.sleep(1)

        def request_issue_type():
            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Requesting now issue type. Checking for '
                  f'updates...')
            markup = types.ReplyKeyboardMarkup(row_width=2)
            markup = generate_buttons(['Back 🔙', 'Software', 'Hardware'], markup)
            self.bot.send_message(personal_chat_id,
                                  'Did you have a Software-related issue or Hardware-related issue?',
                                  reply_markup=markup, disable_notification=1)

            self.clear_pending_updates()
            while True:
                updates = self.bot.get_updates()
                for update in updates:
                    if update.message and str(update.message.chat.id) == personal_chat_id:
                        if update.message.text.capitalize() in ['Software', 'Hardware']:
                            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Specified issue type exi'
                                  f'sts in the list. Proceeding...')
                            return update.message.text.capitalize()
                        elif update.message.text.capitalize() == 'Back 🔙':
                            # Get back to choosing device
                            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] User opted to get back to '
                                  f'previous choosing of device type. Going back...')
                            return 'Back'
                        else:
                            print(f'[{utils.get_time()}] [REQ ERR SOL] Message {update.message.text} is neither '
                                  f'Software, nor Hardware. Can not proceed..')
                            self.bot.send_message(personal_chat_id,
                                                  'Please specify either "Software" or "Hardware". If both of the issues'
                                                  ' are related, please choose one that is closer', reply_markup=markup,
                                                  disable_notification=1)
                            self.clear_pending_updates()

        def request_error_code(device_name, issue_type):
            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Requesting error code now. Checking for '
                  f'updates...')
            issues_and_codes = get_issues_and_codes(device_name, issue_type)
            issues = []
            codes = []

            for issue, code in issues_and_codes:
                issues.append(issue)
                codes.append(code)
            del issues_and_codes

            issues = ['Back 🔙'] + issues + ['Else 🤷‍♂️']
            markup = types.ReplyKeyboardMarkup(row_width=2)
            markup = generate_buttons(issues, markup)
            self.bot.send_message(personal_chat_id,
                                  'Choose the type of error you had',
                                  reply_markup=markup, disable_notification=1)

            self.clear_pending_updates()
            while True:
                updates = self.bot.get_updates()
                for update in updates:
                    if update.message and str(update.message.chat.id) == personal_chat_id:
                        if update.message.text in issues[1:-1]:  # and update.message.text in issues:
                            err_cd = codes[issues.index(update.message.text)-1]
                            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Error description specif'
                                  f'ied by user exists in the json file. Proceeding')
                            return err_cd
                        elif update.message.text == 'Back 🔙':
                            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] User opted to go back to'
                                  f' choosing issue type. Going back...')
                            # Get back to choosing issue type
                            return 'Back'
                        else:
                            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] User chose Else. Starting'
                                  f' the process of adding new error code')
                            return 'Else'

        def add_error_code(device_name, issue_type):
            buttons = ['Yes 👌', 'No, Edit 📝', 'Cancel adding ❌']
            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Starting the process of adding new error '
                  f'code. Device name: {device_name}, issue type: {issue_type}')

            def confirm_edit_deny_adding_error_code(error_code_description):
                self.clear_pending_updates()
                while True:
                    updates = self.bot.get_updates()
                    for update in updates:
                        if update.message and str(update.message.chat.id) == personal_chat_id:
                            if update.message.text == buttons[0]: # 'Yes'
                                print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] User is satisfied with'
                                      f' the error description. Starting the process of adding it to the json file...')
                                new_error_code = statistics.add_new_error_code(error_code_description, device_name,
                                                                               issue_type)
                                self.bot.send_message(personal_chat_id, 'Okay. Your new error has been added to json'
                                                                        ' file and now will be assigned to <b>'
                                                                        f'{new_error_code}</b>', parse_mode='HTML',
                                                      disable_notification=1)
                                return new_error_code
                            elif update.message.text == buttons[1]: # Edit
                                print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] User opted to change '
                                      f'the description of error')
                                add_error_code(device_name, issue_type)
                            elif update.message.text == buttons[2]: # Cancel
                                print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] User opted to cancell'
                                      f' the whole process of adding new error')
                                return None

            self.bot.send_message(personal_chat_id, 'Please write down the error description that you want to add',
                                  disable_notification=1, reply_markup=ReplyKeyboardRemove())
            self.clear_pending_updates()
            while True:
                updates = self.bot.get_updates()
                for update in updates:
                    if update.message and str(update.message.chat.id) == personal_chat_id:
                        print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Got this error description: '
                              f'{update.message.text}. Asking if this error description satisfies user...')
                        markup = types.ReplyKeyboardMarkup(row_width=2)
                        markup = generate_buttons(buttons, markup)

                        self.bot.send_message(personal_chat_id, f'Would you like to add new error type named:\n'
                                                                f'<b>{update.message.text}</b>?\nOr would you like '
                                                                f'to edit it?', reply_markup=markup, parse_mode='HTML',
                                              disable_notification=1)
                        return confirm_edit_deny_adding_error_code(update.message.text)


        def request_resolution_code(device_name, issue_type):
            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Requesting now resolution code. Checking '
                  f'for updates...')
            resolutions_and_codes = get_resolutions_and_codes(device_name, issue_type)
            resolutions = []
            codes = []
            for resolution, code in resolutions_and_codes:
                resolutions.append(resolution)
                codes.append(code)
            del resolutions_and_codes
            resolutions = ['Back 🔙'] + resolutions + ['Else 🤷‍♂️']

            markup = types.ReplyKeyboardMarkup(row_width=2)
            markup = generate_buttons(resolutions, markup)
            self.bot.send_message(personal_chat_id, 'Now specify how did you fix this issue', reply_markup=markup,
                                  disable_notification=1)
            self.clear_pending_updates()
            while True:
                updates = self.bot.get_updates()
                for update in updates:
                    if update.message and str(update.message.chat.id) == personal_chat_id:
                        if update.message.text in resolutions[1:-1]:
                            res_cd = codes[resolutions.index(update.message.text)-1]
                            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Resolution code entered '
                                  f'by user is in the list. Proceeding...')
                            return res_cd
                        elif update.message.text == 'Back 🔙':
                            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] User opted to go back to '
                                  f'choosing error code. Going back..')
                            return 'Back'
                        else:
                            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Resolution type specified '
                                  f'by user was not found in list. Starting adding new resolution type...')
                            return 'Else'

        def add_resol_code(device_name: str, issue_type: str):
            buttons = ['Yes 👌', 'No, Edit 📝', 'Cancel adding ❌']
            print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Starting the process of adding new resol '
                  f'code. Device name: {device_name}, issue type: {issue_type}')

            def confirm_edit_deny_adding_resol_code(resol_code_description):
                self.clear_pending_updates()
                while True:
                    updates = self.bot.get_updates()
                    for update in updates:
                        if update.message and str(update.message.chat.id) == personal_chat_id:
                            if update.message.text == buttons[0]:  # 'Yes'
                                print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] User is satisfied with'
                                      f' the resol description. Starting the process of adding it to the json file...')
                                new_resol_code = statistics.add_new_resol_code(resol_code_description, device_name,
                                                                               issue_type)
                                self.bot.send_message(personal_chat_id, 'Okay. Your new resolution has been added to json'
                                                                        ' file and now will be assigned to <b>'
                                                                        f'{new_resol_code}</b>', parse_mode='HTML',
                                                      disable_notification=1)
                                return new_resol_code
                            elif update.message.text == buttons[1]:  # Edit
                                print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] User opted to change '
                                      f'the description of resol')
                                add_resol_code(device_name, issue_type)
                            elif update.message.text == buttons[2]:  # Cancel
                                print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] User opted to cancell'
                                      f' the whole process of adding new resol')
                                return None

            self.bot.send_message(personal_chat_id, 'Please write down the resolution description that you want to add',
                                  disable_notification=1, reply_markup=ReplyKeyboardRemove())
            self.clear_pending_updates()
            while True:
                updates = self.bot.get_updates()
                for update in updates:
                    if update.message and str(update.message.chat.id) == personal_chat_id:
                        print(f'[{utils.get_time()}] [{employee.upper()} PERSONAL CHAT] Got this resol description: '
                              f'{update.message.text}. Asking if this resol description satisfies user...')
                        markup = types.ReplyKeyboardMarkup(row_width=2)
                        markup = generate_buttons(buttons, markup)

                        self.bot.send_message(personal_chat_id, f'Would you like to add new resol type named:\n'
                                                                f'<b>{update.message.text}</b>?\nOr would you like '
                                                                f'to edit it?', reply_markup=markup, parse_mode='HTML',
                                              disable_notification=1)
                        return confirm_edit_deny_adding_resol_code(update.message.text)

        def check_for_error(stop_event):
            print(f'[{utils.get_time()}] [REQ ERR] Function for asking employee for error type has started...')
            device_name = None
            issue_type = None
            error_code = None
            resolution_code = None

            create_new_error_code = False
            create_new_resolution_code = False

            while not stop_event.is_set():
                print(f'[{utils.get_time()}] [REQ ERR] while loop cycle with questioning employee with '
                      f'device name, issue type, error code and resolution code. Current given data: '
                      f'Device name - {device_name}, Issue type - {issue_type}, Error code - {error_code},'
                      f' Resolution code - {resolution_code}.')

                if create_new_error_code:
                    new_error_code = add_error_code(device_name, issue_type)
                    create_new_error_code = False
                    if new_error_code is not None:
                        error_code = new_error_code
                    else:
                        error_code = None
                if create_new_resolution_code:
                    new_resol_code = add_resol_code(device_name, issue_type)
                    create_new_resolution_code = False
                    if new_resol_code is not None:
                        resolution_code = new_resol_code
                    else:
                        resolution_code = None



                if device_name is None and issue_type is None and error_code is None and resolution_code is None:
                    device_name = request_device_type()
                    if device_name == 'Else':
                        self.bot.send_message(personal_chat_id, "If not any of the specified devices didn't "
                                                                "match the one you fixed, than you don't have to "
                                                                "report on error code and issue code. Just leave "
                                                                "it like that and contact @vova_ucs to discuss "
                                                                "adding new device type...",
                                              reply_markup=ReplyKeyboardRemove(), disable_notification=1)
                        stop_event.set()
                        break
                    else:
                        print(f'[{utils.get_date_and_time()}] [REQ ERR] Device type in {restaurant_name} - {device_name}')

                elif device_name and issue_type is None and error_code is None and resolution_code is None:
                    issue_type = request_issue_type()
                    if issue_type == 'Back':
                        issue_type = None
                        device_name = None
                        continue
                    print(f'[{utils.get_time()}] [REQ ERR] Issue type with device {device_name} - {issue_type}')

                elif device_name and issue_type and error_code is None and resolution_code is None:
                    error_code = request_error_code(device_name, issue_type)
                    if error_code == 'Back':
                        print('Back was chosen for error_code going back')
                        error_code = None
                        issue_type = None
                        #self.clear_pending_updates()
                        continue
                    elif error_code == 'Else':
                        create_new_error_code = True
                        error_code = None
                        print(f'[{utils.get_time()}] [REQ ERR] User wants to add new error code.')
                        continue
                    print(f'[{utils.get_time()}] [REQ ERR] Error code for {issue_type} issue with {device_name} is '
                          f'{error_code}')

                elif device_name and issue_type and error_code and resolution_code is None :
                    resolution_code = request_resolution_code(device_name, issue_type)
                    if resolution_code == 'Back':
                        print('Back was chosen for resolution_code, going back')
                        resolution_code = None
                        error_code = None
                        continue
                    elif resolution_code == 'Else':
                        create_new_resolution_code = True
                        resolution_code = None
                        print(f'[{utils.get_time()}] [REQ ERR] User wants to add new resolution code.')
                        continue

                elif device_name and issue_type and error_code and resolution_code:
                    stop_event.set()
                    self.send_message(f'Got update on issue in {restaurant_name} that was fixed by {employee}.'
                                      f'\nError code - {error_code}, resolution code - {resolution_code}. Issue is '
                                      f'now fully closed')
                    self.bot.send_message(personal_chat_id, 'Thank you. All needed info was received and database in '
                                                            'worksheet was updated, you can continue '
                                                            'with your work or relaxation ;)',
                                          reply_markup=ReplyKeyboardRemove(), disable_notification=1)
                    self.clear_pending_updates()
                    self.pause_personal_monitoring = False
                    error_code = error_code.split(' ')[1]
                    resolution_code = resolution_code.split(' ')[1]
                    self.support_data_wks.update_problem_resolution_codes(row, error_code, resolution_code)

                else:
                    print(f'[{utils.get_time()}] [ERROR REQUEST ERROR RESOL] Unknown unmatched state has occured!'
                          f'Stoping thread and exiting...')
                    stop_event.set()


        if (time.time() - self.launch_time) <= self.INIT_DELAY:
            print(f'[{utils.get_time()}] [UCS MAIN CHANEL] Initialisation not yet complete. ⏰'
                  f'\n\t[REMAINING FOR INIT] {self.INIT_DELAY - (time.time() - self.launch_time)}')
            return  # If bot was started less than a minute ago

        stop_event = threading.Event()
        threading.Thread(target=check_for_error,
                         args=(stop_event,)).start()

    def personal_chat_monitoring_thread(self):
        while True:  # Replace with a more suitable condition for your application
            if not self.pause_personal_monitoring:
                try:
                    updates = self.bot.get_updates(timeout=1)  # Adjust timeout as needed
                    # Process each update
                    for update in updates:
                        if update.message:  # Check if the update contains a message
                            chat_id = update.message.chat.id
                            text = update.message.text
                            if text == '/my_id':
                                self.bot.send_message(chat_id, f'{is_from_ucs(update.message)}, your Telegram ID is: '
                                                               f'{chat_id}')
                            elif '/killyourself' in text and is_from_ucs(update.message):
                                print(f'[{utils.get_time()}] [KILLYOURSELF COMMAND RECEIVED] Running os._exit(0)')
                                self.send_message('KILLYOURSELF received, STOPING Bot!')
                                try:
                                    os._exit(0)
                                except Exception as e:
                                    print(f'[{utils.get_time()}] [KILLYOURSELF ERROR] Failed running os._exit(0),'
                                          f' info: {e}')

                            elif '/stat' in text:
                                restaurant_name = statistics.extract_restaurant_name_generic(text)
                                available_restaurant_names = self.support_data_wks.fetch_available_restaurant_names()
                                if restaurant_name in available_restaurant_names:
                                    dates = statistics.parse_command_date(text)
                                    if dates is not None:
                                        codes = self.support_data_wks.get_object_common_issues(
                                            restaurant_name, dates[0], dates[1])
                                        self.bot.send_message(chat_id,
                                                              f'<b>{restaurant_name.upper()}</b> statistics\n'
                                                              f'Start date: {dates[0][2]}.{dates[0][1]}.{dates[0][0]}\n'
                                                              f'End date: {dates[1][2]}.{dates[1][1]}.{dates[1][0]}\n' +
                                                              str(statistics.format_statistics(codes)),
                                                              parse_mode='HTML')
                                    else:
                                        self.bot.send_message(chat_id, 'Error❌\n Specified date is not supported. Please '
                                                                       'use DD.MM.YYY format for entering date')
                                elif restaurant_name == 'help':
                                    # /stat test from April 2024 till May 2024
                                    continue
                                #elif restaurant_name == None:
                                #    continue
                                    # present statistics of all restaurants
                                else:
                                    to_send = (f'{restaurant_name} was not found in google worksheet. Available '
                                               f'restaurant names are: \n')
                                    for rst_name in available_restaurant_names:
                                        to_send += f'*{rst_name}*\n'
                                    self.bot.send_message(chat_id, to_send, parse_mode='Markdown')
                    # Update the offset to confirm processing of updates
                    if updates:
                        last_update_id = updates[-1].update_id
                        self.bot.get_updates(offset=last_update_id + 1, timeout=1)
                except Exception as e:
                    print(f"[{utils.get_time()}] Error fetching updates in personal monitoring thread: {e}")
                    self.clear_pending_updates()
            #else:
            #    print("Polling paused.")
            time.sleep(1)  # Adjust sleep time as needed to control the polling rate


class TelegramChanel:
    statuses = ('resolved', 'unresolved', 'unknown', 'locked')
    warnings = ('warning1', 'warning2', 'warning3', 'warning4', 'warning5', 'no warning')

    def __init__(self,
                 dotenv_name,
                 bot,
                 language,
                 main_chanel,
                 employees,
                 START_MUTED=False,
                 ASK_RESOL_STAT=False,
                 REQUEST_ERROR_RESOLUTION_CODE=False,
                 TEST=False,
                 INIT_DELAY=75,
                 PROD_TIMINGS=[3, 5, 7, 8, 10],
                 TEST_TIMINGS=[0.1, 0.2, 0.3, 0.4, 0.5],
                 support_wks=None,
                 support_data_wks=None,
                 thread_data=None
                 ):
        self.START_MUTED = START_MUTED
        self.TEST = TEST
        if TEST:
            self.NOTIFY_DONE_INTERVAL_MIN = 1
        else:
            self.NOTIFY_DONE_INTERVAL_MIN = 30
        self.REQUEST_ERROR_RESOLUTION_CODE = REQUEST_ERROR_RESOLUTION_CODE
        self.INIT_DELAY = INIT_DELAY
        if TEST and self.INIT_DELAY != 0:
            self.INIT_DELAY = 5
        self.PROD_TIMINGS = PROD_TIMINGS
        self.TEST_TIMINGS = TEST_TIMINGS
        self.start_time = None
        self.who_answered_to_report = None
        self.last_msg_time = None
        self.done_reminders_sent = 0
        self.support_wks = support_wks
        self.support_data_wks = support_data_wks
        self.employees = employees
        self.launch_time = time.time()
        self.dotenv_name = dotenv_name
        self.str_name = dotenv_name[:-7].replace('_', ' ').lower()
        self.chat_id = os.getenv(dotenv_name)
        self.bot = bot
        self.language = language
        self.thread_data = thread_data
        self.main_chanel = main_chanel


        if not ASK_RESOL_STAT:
            self.status = 'resolved'
        else:
            self.status = 'unknown'
            self.send_message(f'Resolution status unknow. Please specify current chanel status')
            self.ping_with_priority(priority=0)
        self.warning = 'no warning'
        print(
            f'[{utils.get_time()}] [\t{self.str_name.upper()} TELEGRAM CHANEL] Initialising telegram chanel at chat '
            f'{self.chat_id} '
            f'... With this params: Status={self.status}, Warning={self.warning}, Language={self.language}')
        print(
            f'[{utils.get_time()}]\t [{self.str_name.upper()} TELEGRAM CHANEL] '
            f'Starting message handler (incoming messages monitoring)...')

        threading.Thread(target=self.sender).start()

        self.start_monitoring()

    def sender(self):
        print(f'[{utils.get_time()}] [{self.str_name.upper()} TG CH] Sender has been started!')

        while True:
            if self.last_msg_time is not None:
                end_time = time.time()
                elapsed_time = end_time - self.last_msg_time
                hours, rem = divmod(elapsed_time, 3600)
                minutes, seconds = divmod(rem, 60)
                # print(f'Elapsed: {hours} hours {minutes} minutes {seconds} seconds after last message')
                if self.status == 'unresolved' and self.warning == 'no warning' and minutes >= self.NOTIFY_DONE_INTERVAL_MIN\
                        and hours < 474761:   # I mean this is because strangely it tries to substract, soooo
                    if self.done_reminders_sent >= 3:
                        self.send_message('Closing issue automatically after 3 requests to close it manually')
                        print(f'[{utils.get_time()}] [{self.str_name.upper()} TG CH] Setting status to resolved after '
                              f'3 notifications to {self.who_answered_to_report} to close an issue')
                        self.set_status_to_resolved()

                    else:
                        self.send_message('Is it done?')
                        self.last_msg_time = time.time()
                        self.done_reminders_sent += 1
                        if self.who_answered_to_report is not None:
                            self.ping(self.who_answered_to_report)
            time.sleep(1)

    def send_message(self, message):
        print(f'[{utils.get_time()}] [{self.str_name} CHANNEL] Sending this message to chanel: 💬⬆️\n\t{message}')
        self.bot.send_message(self.chat_id, message, disable_notification=self.START_MUTED)

    def make_call_with_priority(self, priority):
        print(f'[{utils.get_time()}]\t[CALLING] Sending call to employee with priority {priority} ⚠️')
        call_employee_with_priority(employees=self.employees, priority=priority, chanel_name=self.str_name)

    def warning_thread(self, stop_event):
        print(f'[{utils.get_time()}] [{self.str_name.upper()} WARNING THREAD] '
              f'Thread for warning monitoring has bee started')
        seconds_elapsed = 0
        timings = {
            'warning1': 60 * self.PROD_TIMINGS[0],
            'warning2': 60 * self.PROD_TIMINGS[1],
            'warning3': 60 * self.PROD_TIMINGS[2],
            'warning4': 60 * self.PROD_TIMINGS[3],
            'warning5': 60 * self.PROD_TIMINGS[4]
        }
        if self.TEST:
            timings = {
                'warning1': 60 * self.TEST_TIMINGS[0],
                'warning2': 60 * self.TEST_TIMINGS[1],
                'warning3': 60 * self.TEST_TIMINGS[2],
                'warning4': 60 * self.TEST_TIMINGS[3],
                'warning5': 60 * self.TEST_TIMINGS[4]
            }
        """This try except block handles all the warnings and their functions"""
        try:
            while not stop_event.is_set():
                time.sleep(1)
                seconds_elapsed += 1
                # ------------------------------------Specify-warning-actions-here-----------------------------------
                # ------------------------------------------Warning-1------------------------------------------------
                if seconds_elapsed == timings['warning1']:
                    print(f'[{utils.get_time()}] [{self.str_name.upper()} NEW WARNING STATUS] Changing warning '
                          f'status to warning 1 and calling responsible employee')
                    self.warning = 'warning1'
                    # Call responsible
                    self.make_call_with_priority(priority=0)
                # ---------------------------------------------------------------------------------------------------
                # -----------------------------------------Warning-2-------------------------------------------------
                elif seconds_elapsed == timings['warning2']:
                    print(f'[{utils.get_time()}] [{self.str_name.upper()} NEW WARNING STATUS] Changing warning '
                          f'status to warning 2 and pinging another responsible')
                    self.warning = 'warning2'
                    self.ping_with_priority(priority=1)
                # ---------------------------------------------------------------------------------------------------
                # ------------------------------------------Warning-3------------------------------------------------
                elif seconds_elapsed == timings['warning3']:
                    print(f'[{utils.get_time()}] [{self.str_name.upper()} NEW WARNING STATUS] Changing warning '
                          f'status to warning 3 and calling second employee')
                    self.warning = 'warning3'
                    self.ping_with_priority(priority=2)
                    self.make_call_with_priority(priority=1)
                # ---------------------------------------------------------------------------------------------------
                # -----------------------------------------Warning-4-------------------------------------------------
                elif seconds_elapsed == timings['warning4']:
                    print(f'[{utils.get_time()}] [{self.str_name.upper()} NEW WARNING STATUS] Changing warning '
                          f'status to warning 4 and pinging Alex')
                    print(f'\t[PINGING] Alex has been pinged')
                    self.warning = 'warning4'
                    # Ping Alex
                    self.ping_with_priority(priority=3)
                # ---------------------------------------------------------------------------------------------------
                # -----------------------------------------Warning-5-----LAST_WARNING--------------------------------
                elif seconds_elapsed == timings['warning5']:
                    print(f'[{utils.get_time()}] [{self.str_name.upper()} NEW WARNING STATUS] Changing warning'
                          f' status to warning 5 and calling Alex')
                    self.warning = 'warning5'
                    self.make_call_with_priority(priority=3)
                    print(
                        f'[{utils.get_time()}] \t[FINAL WARNING ❌] This was last warning. '
                        f'Exiting warning thread... ⚠️')
                    stop_event.set()
                # --------------------------------------------------------------------------------------------------
        except Exception as e:
            print(f'[{utils.get_date_and_time()}] [{self.str_name.upper()} [WARNING ISSUE THREAD] An error occurred '
                  f'when running issue thread: {e}')


    def ping(self, employee_name):
        print(f'[{utils.get_time()}]\t[PINGING] {employee_name} has been pinged ⚠️')
        if os.getenv(f'{employee_name.upper()}_SECOND_TELEGRAM_USERNAME') != '':  # In case employee has second tg user
            self.send_message(
                f"@{os.getenv(f'{employee_name.upper()}_TELEGRAM_USERNAME')} "
                f"@{os.getenv(f'{employee_name.upper()}_SECOND_TELEGRAM_USERNAME')}"
            )
        else:
            self.send_message(f"@{os.getenv(f'{employee_name.upper()}_TELEGRAM_USERNAME')}")

    def ping_with_priority(self, priority):
        """ This function takes as input the number of priority of whom to ping and then pings accordingly
            Input priorities: from 0 to len(employees)-1

            Example: employees = [Yaro, Vova, Egor, Ivan, Igor, Alex], priority = 1
            Priorities go from higher to lower, where the lower the int is, the more employee
            can be pinged the most.

            ping_with_priority(priority=0) -> Will deliver Yaro, in case Yaro is supporting today
            ping_with_priority(priority=1) -> Will deliver Vova if Yaro sup. today
            ping_with_priority(priority=2) -> Will deliver Egor
            ...
            ping_with_priority(priority=5) -> Will delivery Alex. This is the highest priority possible

            return None in case we run out of priorities and writes that to console
        """
        if priority <= (len(self.employees) - 1):
            self.ping(self.employees[priority])
        else:
            print(f'[{utils.get_date_and_time()}] [{self.str_name.upper()}] [PING_WITH_PRIORITY] Incorrect priority'
                  f'given. Priority = {priority}')
            return None

    def set_status_to_resolved(self, message=None):
        self.status = 'resolved'
        self.done_reminders_sent = 0
        with open('restart_permission.txt', 'w') as file:
            file.writelines(['Permited'])
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
            elapsed_time = round(elapsed_time)
            rp_time = self.response_time - self.start_time
            rp_time = round(rp_time)

            # Calculate hours, minutes, and seconds
            rp_hours = rp_time // 3600
            remaining_seconds = rp_time % 3600
            rp_minutes = remaining_seconds // 60
            rp_seconds = remaining_seconds % 60
            if rp_hours > 0:
                rp_elapsed = f'{rp_hours} hours {rp_minutes} minutes {rp_seconds} seconds'
            elif rp_minutes > 0:
                rp_elapsed = f'{rp_minutes} minutes {rp_seconds} seconds'
            else:
                rp_elapsed = f'{rp_seconds} seconds'
            self.main_chanel.send_message(
                f'{self.str_name}\nIssue resolved by {is_from_ucs(message, self.employees)} in'
                f' {elapsed}.\nResponse time: {rp_elapsed}')
            print(
                f"[{utils.get_time()}] [{self.str_name.upper()} TG CHANEL] "
                f"{is_from_ucs(message, self.employees)} resolved"
                f"issue in {elapsed}")
            row = self.support_data_wks.upload_issue_data(
                response_time=rp_time, resolution_time=elapsed_time,
                person_name=is_from_ucs(message, self.employees), restaurant_name=self.str_name,
                warning_status=self.responsed_at_warning_level
            )
            if self.REQUEST_ERROR_RESOLUTION_CODE:
                self.main_chanel.request_problem_resoluion_codes(row, is_from_ucs(message, self.employees),
                                                                 self.str_name)
            to_append = f'{datetime.datetime.now().strftime("%A, %dth %B, %H:%M:%S")} issue resolved by ' \
                        f' {is_from_ucs(message, self.employees)} in ' \
                        f'{elapsed_time} seconds. Response time: {end_time - self.response_time}\n'
            with open(f'statistics/{is_from_ucs(message, self.employees).lower()}.txt', 'a') as f:
                f.write(to_append)
        else:
            print(
                f"[{utils.get_time()}] [{self.str_name.upper()} TG CHANEL] "
                f"{is_from_ucs(message, self.employees)} "
                f"resolved issue")
            self.main_chanel.send_message(f'Issue resolved by {is_from_ucs(message, self.employees)}')

    def restart_monitoring(self):
        self.start_monitoring()

    def start_monitoring(self):
        print(f'[{utils.get_time()}] [{self.str_name} TELEGRAM CHANEL] Started incoming messages monitoring ✅')
        self.start_time = None

        @self.bot.message_handler(func=lambda message: True)
        def monitor_incoming(message):
            self.last_msg_time = time.time()
            if message.photo == None:
                lowered_message = message.text.lower()
            else:
                if message.caption:
                    message.text = message.caption
                    lowered_message = message.text.lower()
                else:
                    lowered_message = ''
            print(f'[{utils.get_time()}] [{self.str_name} TELEGRAM CHANEL] Received new message, message text: '
                  f'{message.text}, from {message.from_user.username}. Is_from_UCS -- '
                  f'{is_from_ucs(message, self.employees)}')

            # Check whether the actuation time has been elapsed to fight with issue #2
            if (time.time() - self.launch_time) <= self.INIT_DELAY != 0:
                print(f'[{utils.get_time()}] [{self.str_name} CHANEL] Initialisation not yet complete. ⏰'
                      f'\n\t[REMAINING FOR INIT] {self.INIT_DELAY - (time.time() - self.launch_time)}')
                return  # If bot was started less than a minute ago

            # Update chat_id and .env file
            if self.chat_id != message.chat.id:
                print(f'[{utils.get_time()} {self.str_name.upper()} TG CHANEL] Difference in chat_id!!!\n'
                      f'\t.env file shows -- {self.chat_id}, actual from message.chat_id -- {message.chat.id}')
                self.chat_id = message.chat.id

            # """-------------Change status of telegram chanel from unknown-------------"""
            if is_from_ucs(message, self.employees) and self.status == 'unknown':
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
            elif self.status == 'resolved' and not is_from_ucs(message, self.employees) and not is_thank_you(message):
                print(f'[{utils.get_time()}] [{self.str_name} TELEGRAM CHANEL] New issue report ⚠! Warning level 0')
                self.status = 'unresolved'
                self.warning = 'warning0'
                self.done_reminders_sent = 0
                self.start_time = time.time()
                self.ping_with_priority(priority=0)
                print(
                    f'[{utils.get_time()}] [{self.str_name} TELEGRAM CHANEL] Responsible for support employee has '
                    f'been pinged')
                self.stop_event = threading.Event()
                print(f'[{utils.get_time()}] [{self.str_name} TELEGRAM CHANEL] Starting issue thread...')
                threading.Thread(target=self.warning_thread, args=(self.stop_event,)).start()
            # """-----------------------------------------------------------------------"""

            # """----------------Not an issue. Locking chanel for discussion------------------"""
            elif is_from_ucs(message, self.employees) and (
                    lowered_message == 'not an issue' or lowered_message == 'lock' or lowered_message == 'not a issue'):
                # or 'kein problem' in lowered_message:
                self.status = 'locked'
                self.stop_event.set()
                self.warning = 'no warning'
                self.done_reminders_sent = 0
                print(f'[{utils.get_time()}] [{self.str_name.upper()} TG CHANEL] false issue. Setting to locked :|')
                self.send_message('Okay, removing issue. Locking bot for further discussion. Type "Unlock" to unlock')
            # """-----------------------------------------------------------------------"""

            # """-----------------Unlocking chanel--------------------------------------"""
            elif is_from_ucs(message, self.employees) and lowered_message == 'unlock' and self.status == 'locked':
                self.status = 'resolved'
                self.done_reminders_sent = 0
                print(f'[{utils.get_time()} [{self.str_name.upper()} TG CHANEL] unlocking chanel for further monitor')
                self.send_message('Chanel unlocked, continuing monitoring')
            # """-----------------------------------------------------------------------"""

            # """-------------Remove warning, but leave unresolved status---------------"""
            elif is_from_ucs(message, self.employees) and self.status == 'unresolved' and self.warning != 'no warning':
                self.who_answered_to_report = is_from_ucs(message, self.employees)
                self.send_message(f'{self.who_answered_to_report} is now resolving the issue in {self.str_name} after '
                                  f'{self.warning}')
                self.responsed_at_warning_level = self.warning
                self.stop_event.set()
                self.response_time = time.time()
                print(f"[{utils.get_time()}] [{self.str_name.upper()} TG CHANEL] {self.who_answered_to_report} replied to "
                      f"report and is now managing situation. Status: 'unresolved', Warning: no warning ❤️")
                self.warning = 'no warning'
                self.done_reminders_sent = 0
                # del self.warning_thread
            # """-----------------------------------------------------------------------"""

            # """-----------------------Set status to resolved--------------------------"""
            elif self.status == 'unresolved' and self.warning == 'no warning' and is_resolution_message(message) \
                    and is_from_ucs(message, self.employees):
                self.set_status_to_resolved(message)
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

        try:
            self.bot.polling(non_stop=True)
        except:
            print(f'[{utils.get_date_and_time()}] [{self.str_name}] Polling failed, restarting monitoring ‼️')
            self.restart_monitoring()


def create_telegram_channel(dotenv_name,
                            bot,
                            language,
                            main_chanel,
                            employees,
                            START_MUTED,
                            ASK_RESOL_STAT,
                            REQUEST_ERROR_RESOLUTION_CODE,
                            TEST,
                            INIT_DELAY,
                            PROD_TIMINGS,
                            TEST_TIMINGS,
                            support_wks,
                            support_data_wks):
    return TelegramChanel(
        dotenv_name=dotenv_name,
        bot=bot,
        language=language,
        main_chanel=main_chanel,
        employees=employees,
        START_MUTED=START_MUTED,
        ASK_RESOL_STAT=ASK_RESOL_STAT,
        REQUEST_ERROR_RESOLUTION_CODE=REQUEST_ERROR_RESOLUTION_CODE,
        TEST=TEST,
        INIT_DELAY=INIT_DELAY,
        PROD_TIMINGS=PROD_TIMINGS,
        TEST_TIMINGS=TEST_TIMINGS,
        support_wks=support_wks,
        support_data_wks=support_data_wks
    )


def return_channels_to_init(channel_params, TEST=True):
    if TEST:
        channels_to_init = [name for name in channel_params.keys() if name == 'TestChanel']
    else:
        channels_to_init = [name for name in channel_params.keys() if name != 'TestChanel']
    return channels_to_init


def test_bots_starting(channels_to_init, channel_params):
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


def start_bot_chanel_threads(main_chanel, channel_params,
                             employees, START_MUTED, ASK_RESOL_STAT, REQUEST_ERROR_RESOLUTION_CODE, INIT_DELAY,
                             PROD_TIMINGS, TEST_TIMINGS, TEST, support_wks, support_data_wks, fast_start):
    bot_threads = []
    for channel_name in return_channels_to_init(channel_params, TEST):
        bot = TelegramBot(dotenv_tokenname=channel_params[channel_name][1]).start_bot()
        print('- ' * 40)
        print(f'[{utils.get_time()}] [THREAD {channel_name.upper()}] Starting thread 🔁')

        if fast_start:
            INIT_DELAY = 0

        bot_threads.append(
            threading.Thread(target=create_telegram_channel, args=
            (
                channel_params[channel_name][0],
                bot,
                channel_params[channel_name][2],
                main_chanel,
                employees,
                START_MUTED,
                ASK_RESOL_STAT,
                REQUEST_ERROR_RESOLUTION_CODE,
                TEST,
                INIT_DELAY,
                PROD_TIMINGS,
                TEST_TIMINGS,
                support_wks,
                support_data_wks
            )
                             )
        )
        bot_threads[len(bot_threads) - 1].setName(f'THREAD_{channel_name.upper()}')
    for bot_thread in bot_threads:
        bot_thread.start()
        print(f'\n[{utils.get_time()}]\t[THREAD {channel_name.upper()}] Started ✅✅✅')
        time.sleep(1)
    print('=' * 80)
    print(f'[{utils.get_time()}] [ALL BOT THREADS STARTED] All specified bots were started 👍')

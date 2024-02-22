import os
import platform
import threading
import telebot
import sip_call
import socket
import argparse
import time

import utils
from sheets import SupportWKS, SupportDataWKS
from gui import input_thread

# sup

TEST = False
START_MUTED = False
REQUEST_ERROR_RESOLUTION = False
ASK_RESOL_STAT = False
NOTIFY_UCS_ON_START = False
REQUEST_ERROR_RESOLUTION_CODE = False
WORKSHEETS_UPD_INTERVALS = 5
WORKSHEETS_OUTPUT_UPDATES = True
FAST_START = False
TELEPHONY = False
PROD_TIMINGS = [3, 5, 7, 8, 10]
TEST_TIMINGS = [0.5, 1, 1.25, 1.50, 1.75]
HOST = (socket.gethostbyname(socket.gethostname()), 10000)

INIT_DELAY = None
if TEST:
    INIT_DELAY = 5
else:
    INIT_DELAY = 75

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
    'VivoChanel': ('KFC_VIVO_CHAT_ID', 'UCS_Support_Vivo_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'RelaxChanel': ('KFC_RELAX_CHAT_ID', 'UCS_Support_Relax_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'LugChanel': ('KFC_LUG_CHAT_ID', 'UCS_Support_Lug_Bot_TELEGRAM_API_TOKEN', 'de'),
    'PlLinzChanel': ('KFC_PL_LINZ_CHAT_ID', 'UCS_Support_Pl_Linz_Bot_TELEGRAM_API_TOKEN', 'de'),
    'EuropaBbChanel': ('KFC_EUROPA_BB_CHAT_ID', 'UCS_Support_Europa_Bb_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'ZvonlenChanel': ('KFC_ZVLN_CHAT_ID', 'UCS_Support_Zvln_Bot_TELEGRAM_API_TOKEN', 'sk'),
    'TestChanel': ('TEST_CHAT_ID', 'UCS_Support_Bot_TELEGRAM_API_TOKEN', 'de')
}


def fetch_employees_from_env():
    employees = []
    for i in range(1, 20):
        val = os.getenv(f'EMPLOYEE{i}_NAME')
        if val!='':
            employees.append(val)
        else:
            break
    return employees

employees = fetch_employees_from_env()


if __name__ == '__main__':
    # Reconfigure employees array, to put on the highest priority the person that is supporting today

    parser = argparse.ArgumentParser(description="Start telegram bots handlers and senders to increase efficiency "
                                                 "of answering to support requests. Pings and calls employees "
                                                 "accordingly by priority")


    parser.add_argument("--test", action="store_true",
                        help="Set to TEST mode, the only chanel that will be working after that is UCSTestEnviroment")
    parser.add_argument("--disable_notifications", action="store_true",
                        help="Disable notifications, when one of the bots is sending messages. Pings are still going "
                             "to give notification to the one who was pinged")
    parser.add_argument("--spec_stat", action="store_true",
                        help="DANGEROUS!!! If set, than sends a message to all the channels asking in which resolution "
                             "is the chanel currently. Made to start during the day, when on some channels may be "
                             "ongoing support. Write to each chanel either resolved or unresolved to specify status"
                             ".\n If not set, than set all channels to resolved")
    parser.add_argument("--notify_on_start", action="store_true",
                        help="If is specified, than on launch will send a message to the main chanel specifying "
                             "on which PC, operating system it is running and outputs the channels on which "
                             "bots are being ran")
    parser.add_argument("--req_err_resol", action="store_true",
                        help="If is specified, than after resolving issue, a message will be sent to main chanel"
                             "asking to specify error code and resolution code that will later be updated at "
                             "support data worksheet")
    parser.add_argument("--telephony_ip", type=str,
                        help="Specify the IP address of server where telephony TCP server is running."
                             "Default: IPv4 address of this PC")
    parser.add_argument("--telephony_port", type=int,
                        help="Specify port of server where telephony TCP server is running. Default = 10000")
    parser.add_argument("--wks_upd_interval", type=int,
                        help="Specify time interval between each worksheet buffer update. Default = 5")
    parser.add_argument("--wks_output_upd", action="store_true",
                        help="If specified, than outputs in terminal that buffer of wks was updated")
    parser.add_argument("--fast_start", action="store_true",
                        help="Fast start without init delay or any in case")
    parser.add_argument("--telephony", action="store_true",
                        help="If specified, run telephony thread server for calling")

    # Parse the command-line arguments
    args = parser.parse_args()


    # Update variables based on command-line arguments
    new_HOST = [None, None]
    if args.test:
        TEST = True
    if args.disable_notifications:
        START_MUTED = True
    if args.spec_stat:
        ASK_RESOL_STAT = True
    if args.notify_on_start:
        NOTIFY_UCS_ON_START = True
    if args.req_err_resol:
        REQUEST_ERROR_RESOLUTION_CODE = True
    if args.telephony:
        TELEPHONY = True
    if args.telephony_ip is not None:
        new_HOST[0] = args.telephony_ip
    if args.telephony_port is not None:
        new_HOST[1] = args.telephony_port
    if args.wks_upd_interval is not None:
        WORKSHEETS_UPD_INTERVALS = args.wks_upd_interval
    if args.wks_output_upd:
        WORKSHEETS_OUTPUT_UPDATES = True
    if args.fast_start:
        FAST_START = True


    tmp_tuple_host = HOST
    del HOST
    if new_HOST[0] is not None and new_HOST[1] is not None:
        HOST = (new_HOST[0], new_HOST[1])
    elif new_HOST[0] is not None and new_HOST[1] is None:
        HOST = (new_HOST[0], tmp_tuple_host[1])
    elif new_HOST[0] is None and new_HOST[1] is not None:
        HOST = (tmp_tuple_host[0], new_HOST[1])
    elif new_HOST[0] is None and new_HOST[1] is None:
        HOST = (tmp_tuple_host[0], tmp_tuple_host[1])
    else:
        print('HOST specification is bad...')
        HOST = (tmp_tuple_host[0], tmp_tuple_host[1])

    print(f'[{utils.get_date_and_time()}] [MAIN] STARTING SCRIPT!!!! \n\tPARAMS:\n'
          f'\t\tTEST={TEST}, START_MUTED={START_MUTED}, ASK_RESOL_STAT={ASK_RESOL_STAT},\n'
          f'\t\tNOTIFY_ON_START={NOTIFY_UCS_ON_START}, REQUEST_ERROR_RESOLUTION_CODE={REQUEST_ERROR_RESOLUTION_CODE}\n'
          f'\t\tTELEPHONY_HOST={HOST}, WORKSHEETS_UPD_INTERVALS={WORKSHEETS_UPD_INTERVALS}\n'
          f'\t\tWORKSHEETS_OUTPUT_UPDATES={WORKSHEETS_OUTPUT_UPDATES}')
    print(f'[{utils.get_date_and_time()}] [MAIN SCRIPT] [EMPLOYEES] Employees that are in db: {employees}')
    if not FAST_START:
        if TEST:
            time.sleep(5)
        else:
            time.sleep(15)

    from bot import return_channels_to_init, UCSAustriaChanel, start_bot_chanel_threads

    support_wks = SupportWKS(UPD_INTERVAL=WORKSHEETS_UPD_INTERVALS,OUTPUT_UPDATES=WORKSHEETS_OUTPUT_UPDATES)
    support_data_wks = SupportDataWKS(UPD_INTERVAL=WORKSHEETS_UPD_INTERVALS,OUTPUT_UPDATES=WORKSHEETS_OUTPUT_UPDATES)

    supporting_today = support_wks.supporting_today()

    if supporting_today in employees:
        sup_today_id = employees.index(supporting_today)
        employees.pop(sup_today_id)
        employees.insert(0, supporting_today)

    if platform.system() == 'Windows':
        input_thread = threading.Thread(target=input_thread)
        input_thread.start()
    to_init = return_channels_to_init(channel_params, TEST=False)

    # Initialise cellphone calling server that communicates later with android client
    if TELEPHONY:
        call_server = threading.Thread(target=sip_call.start_telephony_server, args=(HOST,))
        call_server.start()

    ucs_chanel = None
    if not TEST:
        ucs_chanel = UCSAustriaChanel(
            bot=telebot.TeleBot(os.getenv("UCS_Support_Bot_TELEGRAM_API_TOKEN")),
            inits=to_init,
            TEST=0,
            NOTIFY_UCS_ON_START=NOTIFY_UCS_ON_START,
            INIT_DELAY=INIT_DELAY,
            support_wks=support_wks,
            support_data=support_data_wks
        )
    else:
        ucs_chanel = UCSAustriaChanel(
            telebot.TeleBot(os.getenv("TEST_UCS_SUPPORT_Bot_TELEGRAM_API_TOKEN")),
            inits=to_init,
            TEST=1,
            NOTIFY_UCS_ON_START=NOTIFY_UCS_ON_START,
            INIT_DELAY=INIT_DELAY,
            support_wks=support_wks,
            support_data=support_data_wks
        )

    start_bot_chanel_threads(main_chanel=ucs_chanel,
                             channel_params=channel_params,
                             employees=employees,
                             START_MUTED=START_MUTED,
                             ASK_RESOL_STAT=ASK_RESOL_STAT,
                             REQUEST_ERROR_RESOLUTION_CODE=REQUEST_ERROR_RESOLUTION_CODE,
                             INIT_DELAY=INIT_DELAY,
                             PROD_TIMINGS=PROD_TIMINGS,
                             TEST_TIMINGS=TEST_TIMINGS,
                             TEST=TEST,
                             support_wks=support_wks,
                             support_data_wks=support_data_wks,
                             fast_start=FAST_START
                             )

    print(f'[{utils.get_date_and_time()}] [MAIN] Starting issue handling thread...')

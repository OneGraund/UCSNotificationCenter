import gspread
import dotenv
import os
from datetime import datetime, date
import time
import threading
import holidays
import statistics
import utils
from utils import Logger

logger = Logger(filename="logs", logging_level=0)

dotenv.load_dotenv()


def is_holiday():
    today = date.today()
    holidays_in_austria = holidays.Austria()
    if today in holidays_in_austria:
        return True
    else:
        return False


def write_lists_to_file(lists, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for lst in lists:
            for item in lst:
                f.write(f'{item}\n')
            f.write('----\n')  # separator line


def read_lists_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lists = []
        current_list = []
        for line in f:
            stripped_line = line.strip()
            if stripped_line == '----':  # separator line
                lists.append(current_list)
                current_list = []
            else:
                current_list.append(stripped_line)
        if current_list:  # handle the last list
            lists.append(current_list)
    return lists


class Spreadsheet:
    def __init__(self):
        self.spreadsheet_name = os.getenv('GOOGLE_SHEETS_SPREADSHEET_NAME')
        logger.log(f'[SPREADSHEET {self.spreadsheet_name.upper()}] '
              f'Opening spreadsheet {self.spreadsheet_name}', 1)
        self.service_account = gspread.service_account('./service_account.json')
        self.spreadsheet = self.establish_gspread_connection(self.spreadsheet_name)

        logger.log(f'[SPREADSHEET {self.spreadsheet_name.upper()}] '
              f'Spreadsheet opened successfully ✅ \n\tAvailable worksheets: ', 1)
        for wks in self.spreadsheet.worksheets():
            logger.log(f'\t{wks}', 0)

    def establish_gspread_connection(self, spreadsheet_name):
        spreadsheet = None
        for i in range(0, 5):
            try:
                spreadsheet = self.service_account.open(spreadsheet_name)
                connection_error = None
            except Exception as e:
                connection_error = str(e)
            if connection_error:
                logger.log(f'[{utils.get_date_and_time()}] [ERROR CONNECTING WITH GSPREAD] Gspread '
                      f'could not open spreadsheet {spreadsheet_name}. Retrying after 10 seconds...', 3)
                time.sleep(10)
            else:
                logger.log(f'[GSPREAD] Connected to spreadsheet {spreadsheet_name} successfully', 1)
                break
        return spreadsheet


class Worksheet(Spreadsheet):
    def __init__(self, worksheet_name, UPD_INTERVAL=5, OUTPUT_UPDATES=True):
        super().__init__()
        self.OUTPUT_UPDATES = OUTPUT_UPDATES
        self.UPD_INTERVAL = UPD_INTERVAL
        logger.log(f'[WORKSHEET {worksheet_name.upper()}] Opening worksheet named {worksheet_name}', 0)
        self.worksheet_name = worksheet_name
        self.worksheet = self.spreadsheet.worksheet(worksheet_name)
        self.buff = self.worksheet.get_all_values()
        write_lists_to_file(self.buff, f'{self.worksheet_name}_buff.txt')
        logger.log(f'[WORKSHEET {worksheet_name.upper()}] Opened worksheet and created buff in '
              f'{worksheet_name}_buff.txt ✅', 0)
        logger.log(f'[WORKSHEET {worksheet_name.upper()}] Starting buff updater...', 1)
        buff_updater_thread = threading.Thread(target=self.buff_updater, args=())
        buff_updater_thread.start()

    def get_buff(self):
        logger.log('[WORKSHEET CLASS] Getting buff...')
        try:
            return read_lists_from_file(f'{self.worksheet_name}_buff.txt')
        except Exception as e:
            logger.log(f'[WORKSHEET CLASS] Failed getting buff for {self.worksheet}, reason {e}', 3)

    def buff_updater(self):
        logger.log(f'[{self.worksheet_name.upper()} BUFFER UPDATER] Buffer updater is started and regularly updates .txt ✅', 0)
        while True:
            time.sleep(60 * self.UPD_INTERVAL)
            for i in range(0, 5):
                try:
                    write_lists_to_file(self.worksheet.get_all_values(), f'{self.worksheet_name}_buff.txt')
                    connection_error = None
                except Exception as e:
                    connection_error = str(e)
                if connection_error:
                    logger.log(f'[{utils.get_date_and_time()}] [ERROR CONNECTING WITH GSPREAD] Gspread '
                          f'could not establish connection to google sheets...', 3)
                    time.sleep(4)
                    if i == 3:
                        logger.log(f'[BUFFER NOT UPDATE] Could not update buffer for {self.worksheet_name.upper()} because '
                              f'of error when connecting to google sheets API...', 4)
                else:
                    break
            if self.OUTPUT_UPDATES:
                logger.log(f'[{utils.get_time()}]\t[{self.worksheet_name.lower()} buffer] updated 💤', 0)


class SupportWKS(Worksheet):
    def __init__(self, UPD_INTERVAL=5, OUTPUT_UPDATES=True):
        super().__init__(
            os.getenv('GOOGLE_SHEETS_SUPPORT_WORKSHEET_NAME'),
            UPD_INTERVAL=UPD_INTERVAL, OUTPUT_UPDATES=OUTPUT_UPDATES
        )
        threading.Thread(target=self.update_holiday_payment).start()

    def update_holiday_payment(self):
        while True:
            if is_holiday():
                holiday_payment = '40'
                at_row = None
                for row, value in enumerate(self.get_buff()):
                    if value[0] == datetime.now().strftime("%d-%b-%Y"):
                        at_row = row
                self.worksheet.update(f'D{at_row}', holiday_payment)
                logger.log(f'\t[{utils.get_date_and_time()}][SUPPORT WORKSHEET] Today is holiday, updated payment 🎁', 1)
            else:
                logger.log(f'[{utils.get_date_and_time()}]\t[SUPPORT WORKSHEET] Today is not a holiday, therefore  I am '
                      f'not changing payment', 1)
            time.sleep(24 * 60 * 60)

    def supporting_today(self):
        today = datetime.now().strftime("%d-%b-%Y")
        if today.startswith('0'):
            today = today[1:]
        at_row = None
        for row, value in enumerate(self.get_buff()):
            if value[0] == today:
                at_row = row

        return self.get_buff()[at_row][4]


class SupportDataWKS(Worksheet):
    def __init__(self, UPD_INTERVAL=5, OUTPUT_UPDATES=True):
        super().__init__(
            os.getenv('GOOGLE_SHEETS_SUPPORTDATA_WORKSHEET_NAME'),
            UPD_INTERVAL=UPD_INTERVAL, OUTPUT_UPDATES=OUTPUT_UPDATES
        )

    def today_results(self):
        pass

    def get_array_of_row(self, row_num):
        return self.get_buff()[row_num-1]

    def get_object_common_issues(self, restaurant_name, start_period=None, end_period=None):
        """
        Calculate the common issues for a given restaurant within a specified period.

        Parameters:
        restaurant_name (str): The name of the restaurant to filter the issues.
        start_period (list of int, optional): The start period date as a list in the form [Year, Month, Day].
        end_period (list of int, optional): The end period date as a list in the form [Year, Month, Day].

        Returns:
        dict: A dictionary where keys are error codes and values are the counts of their occurrences.

        This function iterates over all rows in the worksheet buffer and aggregates the count of each
        problem code for the specified restaurant. If only start_period or end_period is specified,
        it will consider issues from the start_period onwards or up to the end_period, respectively.
        Rows with unspecified problem codes are counted under the key 'NotGiven' and will be shown last
        in the sorted statistics.
        """

        # Initialize a dictionary to store error code occurrences.
        error_code_counts = {}

        # Convert start_period and end_period into datetime objects if they are provided
        start_date = datetime(*start_period) if start_period else datetime.min
        end_date = datetime(*end_period) if end_period else datetime.max

        # Iterate over the rows of the worksheet.
        for row in self.get_buff()[1:]:
            # Check if the restaurant name matches.
            if row[9] == restaurant_name:
                # Extract the row's date as a datetime object for comparison.
                row_date = datetime(int(row[1]), int(row[2]), int(row[3]))

                # Check the date range condition
                if start_date <= row_date <= end_date:
                    # Get the problem code or mark it as 'NotGiven'.
                    problem_code = row[7] if row[7] else 'NotGiven'

                    # Increment the count for this problem code in the dictionary.
                    error_code_counts[problem_code] = error_code_counts.get(problem_code, 0) + 1

        # Ensure 'NotGiven' comes last if it's present.
        not_given_count = error_code_counts.pop('NotGiven', None)
        if not_given_count is not None:
            error_code_counts['NotGiven'] = not_given_count

        return error_code_counts

    def fetch_available_restaurant_names(self):
        rst_names = []
        for row in self.get_buff()[1:]:
            if row[9] != '' and row[9] not in rst_names:
                rst_names.append(row[9])
        return rst_names

    def update_problem_resolution_codes(self, row_to_upload, error_code, resol_code):
        logger.log(f'[SHEETS] Received error code and resolution code for row {row_to_upload},'
              f' error code - {error_code}, resol_code - {resol_code}. Uploading...', 1)
        self.worksheet.update(f'H{row_to_upload}', error_code)
        self.worksheet.update(f'I{row_to_upload}', resol_code)
        self.worksheet.update(f'L{row_to_upload}', statistics.get_erorr_description_from_code(error_code))
        self.worksheet.update(f'M{row_to_upload}', statistics.get_resolution_descrioption_from_code(resol_code))
        self.worksheet.update(f'N{row_to_upload}', statistics.get_device_name_from_code(error_code))
        self.worksheet.update(f'O{row_to_upload}', statistics.get_issue_type_from_code(error_code))

    def update_error_resol_descriptions(self):
        # fetch not updated rows
        logger.log(f'[SUPPORTDATA WORKSHEET] Updating SupportData with error descriptions'
              f'and resolution descriptions that have not been yet entered', 1)
        time.sleep(3)
        for row_num, row in enumerate(self.get_buff()[1:]):
            if row[7] != '' and row[8] != '' and row[11] == '' and row[12] == '' and row[0] != '' and row[9] != 'test':
                row[11] = statistics.get_erorr_description_from_code(row[7])
                row[12] = statistics.get_resolution_descrioption_from_code(row[8])
                logger.log(f'[SUPPORTDATA WORKSHEET] Updating row {row_num+2} with '
                     f'error description and resolution description. \n\tCodes are:'
                     f'{row[7]} {row[8]}\n\tdescriptions: \n\t\t{row[11]}\n\t\t'
                     f'{row[12]}', 0)
                self.worksheet.update(f'L{row_num+2}', row[11])
                self.worksheet.update(f'M{row_num+2}', row[12])
                time.sleep(5)
                #print(row)

    def update_device_name_issue_type(self):
        logger.log(f'[SUPPORTDATA WORKSHEET] Updating SupportData with device names and issue types of issues', 1)
        time.sleep(3)
        for row_num, row in enumerate(self.get_buff()[1:]):
            if row[0] != '' and row[7] != '' and row[8] != '' and row[13] == '' and row[14] == '' and row[9] != 'test':
                # row[13] is device name, row[14] is issue type
                row[13] = statistics.get_device_name_from_code(row[7])
                row[14] = statistics.get_issue_type_from_code(row[7])
                logger.log(f'[SUPPORTDATA WORKSHEET] Updating row {row_num + 2} with device names and issue types'
                      f'\n\tCode: {row[7]}, \n\tIssue description: {row[11]},\n\tDevice name: {row[13]}\n\t'
                      f'Issue type: {row[14]}', 0)
                self.worksheet.update(f'N{row_num + 2}', row[13])
                self.worksheet.update(f'O{row_num + 2}', row[14])
                time.sleep(5)
                #print(row)


    def upload_issue_data(self, response_time, resolution_time, person_name, restaurant_name, warning_status,
                          restaurant_country, problem_code=None, resolution_code=None):
        logger.log(f'[SUPPORT DATA] Received a request to upload data without error/resol codes', 0)
        current_datetime = datetime.now()
        current_month = current_datetime.strftime('%m')
        current_day = current_datetime.strftime('%d')
        current_year = current_datetime.strftime('%Y')
        current_time = current_datetime.strftime('%H:%M:%S')

        # get_last_row
        row_to_upload_num = None
        for row_id, row in enumerate(self.get_buff()):
            #logger.log(f'\t{row}', 0)
            if row[0] == '':
                row_to_upload_num = row_id
                break
        logger.log(f'[{utils.get_date_and_time()}] [SUPPORT DATA WKS] Uploading data to row '
                   f'{row_to_upload_num + 1}', 1)
        row_to_upload_num = row_to_upload_num + 1
        self.worksheet.update(f'A{row_to_upload_num}', person_name)
        self.worksheet.update(f'B{row_to_upload_num}', current_year)
        self.worksheet.update(f'C{row_to_upload_num}', current_month)
        self.worksheet.update(f'D{row_to_upload_num}', current_day)
        self.worksheet.update(f'E{row_to_upload_num}', current_time)
        self.worksheet.update(f'F{row_to_upload_num}', response_time)
        self.worksheet.update(f'G{row_to_upload_num}', resolution_time)
        self.worksheet.update(f'H{row_to_upload_num}', problem_code)
        self.worksheet.update(f'I{row_to_upload_num}', resolution_code)
        self.worksheet.update(f'J{row_to_upload_num}', restaurant_name)
        self.worksheet.update(f'K{row_to_upload_num}', warning_status)
        self.worksheet.update(f'P{row_to_upload_num}', restaurant_country)

        logger.log(f'[SUPPORT DATA WKS] Data was uploaded', 0)

        return row_to_upload_num

    # Goes through support data wks and fetches issues that WERE closed in telegram channels, but didn't have
    # completed error/resolution codes
    # Input:
    #   employee: str employee
    #   month:    int of a month to be checked (default this month)
    #   year:     int of a year to be checked (default this year)
    # Returns:
    #   2-D array of tickets, where first dimensions are tickets themselves and second one its location in spreadsheet
    def retrieve_incomplete_tickets(self, employee, month=utils.get_int_month(), year=utils.get_int_year()):
        logger.log(f'[SUPPORT DATA WKS] Retrieving incomplete tickets for {employee}, {month}, {year}', 1)
        tickets = []
        rows = []
        month = str(month)
        if len(month) == 1:
            month = '0' + month
        year = str(year)
        for row_num, row in enumerate(self.get_buff()[1:]):
            if row[0] == employee and row[1] == year and row[2] == month and row[7] == '' and row[8] == '':
                tickets.append(row)
                rows.append(row_num+2)
                # MIGHT BE OFF BY 1
            if row[0] == '' and row[1] == '' and row[2] == '' and row[3] == '':
                break
        return [tickets, rows]








if __name__ == '__main__':
    support_data_wks = SupportDataWKS(UPD_INTERVAL=2, OUTPUT_UPDATES=True)
    #time.sleep(4)
    #tickets = support_data_wks.retrieve_incomplete_tickets('Egor')
    #print(utils.format_incomplete_tickets(tickets))

    print(support_data_wks.get_array_of_row(1812))
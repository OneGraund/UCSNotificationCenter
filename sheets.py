import gspread
import dotenv
import os
from datetime import datetime, date
import time
import threading
import holidays
import statistics
import utils

dotenv.load_dotenv()


def is_holiday():
    today = date.today()
    holidays_in_austria = holidays.Austria()
    if today in holidays_in_austria:
        return True
    else:
        return False


def write_lists_to_file(lists, filename):
    with open(filename, 'w') as f:
        for lst in lists:
            for item in lst:
                f.write(f'{item}\n')
            f.write('----\n')  # separator line


def read_lists_from_file(filename):
    with open(filename, 'r') as f:
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
        print(f'[{utils.get_time()}] [SPREADSHEET {self.spreadsheet_name.upper()}] '
              f'Opening spreadsheet {self.spreadsheet_name}')
        self.service_account = gspread.service_account('./service_account.json')
        self.spreadsheet = self.establish_gspread_connection(self.spreadsheet_name)

        print(f'[{utils.get_time()}] [SPREADSHEET {self.spreadsheet_name.upper()}] '
              f'Spreadsheet opened successfully ✅ \n\tAvailable worksheets: ')
        for wks in self.spreadsheet.worksheets():
            print(f'\t{wks}')

    def establish_gspread_connection(self, spreadsheet_name):
        spreadsheet = None
        for i in range(0, 5):
            try:
                spreadsheet = self.service_account.open(spreadsheet_name)
                connection_error = None
            except Exception as e:
                connection_error = str(e)
            if connection_error:
                print(f'[{utils.get_date_and_time()}] [ERROR CONNECTING WITH GSPREAD] Gspread '
                      f'could not open spreadsheet {spreadsheet_name}. Retrying after 10 seconds...')
                time.sleep(10)
            else:
                print(f'[{utils.get_time()}] [GSPREAD] Connected to spreadsheet {spreadsheet_name} successfully')
                break
        return spreadsheet


class Worksheet(Spreadsheet):
    def __init__(self, worksheet_name, UPD_INTERVAL=5, OUTPUT_UPDATES=True):
        super().__init__()
        self.OUTPUT_UPDATES = OUTPUT_UPDATES
        self.UPD_INTERVAL = UPD_INTERVAL
        print(f'[{utils.get_time()}] [WORKSHEET {worksheet_name.upper()}] Opening worksheet named {worksheet_name}')
        self.worksheet_name = worksheet_name
        self.worksheet = self.spreadsheet.worksheet(worksheet_name)
        self.buff = self.worksheet.get_all_values()
        write_lists_to_file(self.buff, f'{self.worksheet_name}_buff.txt')
        print(f'[{utils.get_time()}] [WORKSHEET {worksheet_name.upper()}] Opened worksheet and created buff in '
              f'{worksheet_name}_buff.txt ✅')
        print(f'[{utils.get_time()}] [WORKSHEET {worksheet_name.upper()}] Starting buff updater...')
        buff_updater_thread = threading.Thread(target=self.buff_updater, args=())
        buff_updater_thread.start()

    def get_buff(self):
        return read_lists_from_file(f'{self.worksheet_name}_buff.txt')

    def buff_updater(self):
        print(f'[{self.worksheet_name.upper()} BUFFER UPDATER] Buffer updater is started and regularly updates .txt ✅')
        while True:
            time.sleep(60 * self.UPD_INTERVAL)
            for i in range(0,5):
                try:
                    write_lists_to_file(self.worksheet.get_all_values(), f'{self.worksheet_name}_buff.txt')
                    connection_error = None
                except Exception as e:
                    connection_error = str(e)
                if connection_error:
                    print(f'[{utils.get_date_and_time()}] [ERROR CONNECTING WITH GSPREAD] Gspread '
                          f'could not establish connection to google sheets...')
                    time.sleep(4)
                    if i == 3:
                        print(f'[BUFFER NOT UPDATE] Could not update buffer for {self.worksheet_name.upper()} because '
                              f'of error when connecting to google sheets API...')
                else:
                    break
            if self.OUTPUT_UPDATES:
                print(f'[{utils.get_time()}]\t[{self.worksheet_name.lower()} buffer] updated 💤')


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
                print(f'\t[{utils.get_date_and_time()}][SUPPORT WORKSHEET] Today is holiday, updated payment 🎁')
            else:
                print(f'[{utils.get_date_and_time()}]\t[SUPPORT WORKSHEET] Today is not a holiday, therefore  I am '
                      f'not changing payment')
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
        print(f'[SHEETS] [{utils.get_time()}] Received error code and resolution code for row {row_to_upload},'
              f' error code - {error_code}, resol_code - {resol_code}. Uploading...')
        self.worksheet.update(f'H{row_to_upload}', error_code)
        self.worksheet.update(f'I{row_to_upload}', resol_code)

    def upload_issue_data(self, response_time, resolution_time, person_name, restaurant_name, warning_status,
                          problem_code=None, resolution_code=None):
        if person_name == 'Ivan':  # because in google sheets always Ivan
            person_name = 'Ivan'
        current_datetime = datetime.now()
        current_month = current_datetime.strftime('%m')
        current_day = current_datetime.strftime('%d')
        current_year = current_datetime.strftime('%Y')
        current_time = current_datetime.strftime('%H:%M:%S')

        # get_last_row
        row_to_upload_num = None
        for row_id, row in enumerate(self.get_buff()):
            if row[0] == '':
                row_to_upload_num = row_id
                break
        print(f'[{utils.get_date_and_time()}] [SUPPORT DATA WKS] Uploading data to row {row_to_upload_num+1}')
        row_to_upload_num=row_to_upload_num+1
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

        return row_to_upload_num

if __name__ == '__main__':
    support_data_wks = SupportDataWKS(UPD_INTERVAL=2,OUTPUT_UPDATES=True)
    restaurant_names = support_data_wks.fetch_available_restaurant_names()
    print(restaurant_names)
    for rst_name in restaurant_names:
        print(statistics.format_statistics(support_data_wks.get_object_common_issues(restaurant_name=rst_name)))

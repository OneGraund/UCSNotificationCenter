import json
from datetime import datetime
import re

import utils
from utils import Logger

logger = Logger(filename='logs',  logging_level=0)


def get_description(code, descriptions):
    # print(f'[get description] code - {code}, descriptions - {descriptions}')
    for system, categories in descriptions.items():
        for category, errors in categories.items():
            for description, error_code in errors.items():
                if str(error_code).endswith(code):  # Assuming error codes are unique.
                    return description
    return "Description not found"

def get_dvc_name_iss_type(code, descriptions):
    for system, categories in descriptions.items():
        for category, errors in categories.items():
            for description, error_code in errors.items():
                if str(error_code).endswith(code):  # Assuming error codes are unique.
                    return system, category
    return "Device not found", "Issue type unknown"

def format_statistics(error_code_counts: dict) -> str:
    """
    Create a Markdown formatted string of statistics from the error code counts dictionary,
    including the description of each error, formatted for Telegram bot messages.

    Parameters:
    error_code_counts (dict): A dictionary where keys are error codes and values are the counts of their occurrences.

    Returns:
    str: A Markdown formatted string for Telegram representing the statistics of error codes with descriptions.
    """

    error_descriptions = load_error_descriptions()

    # Helper function to get the description for an error code.


    # Sort the error codes by occurrence count, ensuring 'NotGiven' is last.
    sorted_error_codes = sorted(
        error_code_counts.items(),
        key=lambda item: (item[0] == 'NotGiven', -item[1])
    )

    # Initialize an empty list to hold the formatted lines.
    formatted_lines = [0]

    # Format each error code with its count and description using Markdown.
    for error_code, count in sorted_error_codes:
        description = get_description(error_code, error_descriptions)
        line = f"<b>Error Code '{error_code}':</b> {count} occurrences - <i>{description}</i>"
        formatted_lines[0] += count
        formatted_lines.append(line)

    # Join the formatted lines into a single string separated by new lines.
    formatted_lines[0] = f'<b><u>Total amount of errors:</u> {formatted_lines[0]}</b> issues.\n'
    formatted_statistics = "\n".join(formatted_lines)

    return formatted_statistics

def parse_command_date(input_str):
    # Default min and current dates
    min_date = datetime(1900, 1, 1)
    current_date = datetime.now()

    # Regular expressions to find dates
    from_match = re.search(r'from\s+(\d{2}\.\d{2}\.\d{4})', input_str)
    till_match = re.search(r'till\s+(\d{2}\.\d{2}\.\d{4})', input_str)

    if from_match:
        try:
            start_date = datetime.strptime(from_match.group(1), '%d.%m.%Y')
        except Exception as e:
            logger.log(f'[{utils.get_time()}] [STATISTICS] [PARSE COMMAND DATE] Could not parse '
                  f'start date. Maybe wrong format? Error: {e}', 3)
            return None
    else:
        start_date = min_date

    if till_match:
        try:
            end_date = datetime.strptime(till_match.group(1), '%d.%m.%Y')
        except Exception as e:
            logger.log(f'[{utils.get_time()}] [STATISTICS] [PARSE COMMAND DATE] Could not parse '
                  f'end date. Maybe wrong format? Error: {e}', 3)
            return None
    else:
        end_date = current_date

    return [start_date.year, start_date.month, start_date.day], [end_date.year, end_date.month, end_date.day]


def extract_restaurant_name_generic(input_str):
    """
    Extracts the restaurant name from the input string for any one-word command.
    The command is followed by the restaurant name and optionally by "from [date]" and/or "till [date]".
    """
    # Adjust the regex to match any one-word command followed by a space
    name_part = re.search(r'^/\w+\s+(.*?)(?=\s+from|\s+till|$)', input_str)
    restaurant_name = name_part.group(1).strip() if name_part else None

    return restaurant_name


def load_error_descriptions():
    with open('error_codes.json', 'r') as error_codes_file:
        return json.load(error_codes_file)

def load_resolutions_descriptions():
    with open('resolution_codes.json', 'r') as resolution_codes_file:
        return json.load(resolution_codes_file)

def update_error_json(updated_errors: dict) -> bool:
    """
    :param updated_errors: A dictionary that contains as well as all previous errors, as well as a new one
    :return: Return True if succesfully updated, False if an error occurred
    """
    try:
        with open('error_codes.json', 'w') as file:
            json.dump(updated_errors, file, indent=4)
        return True
    except Exception as e:
        logger.log(f'[{utils.get_time()}] [STATISTICS] Failed updating error_codes.json. Reason:\n\t{e}', 3)
        return False

def update_resol_json(updated_resols: dict) -> bool:
    """
    :param updated_resols: A dictionary that contains as well as all previous resolutions, as well as a new one
    :return: Return True if succesfully updated, False if an error occurred
    """
    try:
        with open('resolution_codes.json', 'w') as file:
            json.dump(updated_resols, file, indent=4)
        return True
    except Exception as e:
        logger.log(f'[{utils.get_time()}] [STATISTICS] Failed updating resolution_codes.json. Reason:\n\t{e}', 3)
        return False

def add_new_error_code(error_desc: str, device_name: str, issue_type: str):
    # Input: error description of an error that needs to be added, device_name and issue_type to categorise correctly
    # Return: error code that this error was assigned to
    new_error_code = 0
    error_descriptions = load_error_descriptions()

    max_error = int(list(error_descriptions[device_name][issue_type].values())[0][6:])
    for value in list(error_descriptions[device_name][issue_type].values()):
        logger.log(f'Value: {value}. Type: {type(value)}', 0)
        if int(value[6:]) > max_error:
            max_error = int(value[6:])
    category = str(list(error_descriptions[device_name][issue_type].values())[0].split(' ')[1][:2])

    new_error_code = 'Error ' + category + str(max_error + 1)[-2:]

    error_descriptions[device_name][issue_type][error_desc] = new_error_code
    if update_error_json(error_descriptions):
        logger.log(f'[{utils.get_time()}] [STATISTICS] Successfully added new error code for Category: {device_name} '
              f'{issue_type}. Description: {error_desc}. New error_code: {new_error_code}', 1)
        return new_error_code
    else:
        logger.log(f"[{utils.get_time()}] [STATISTICS] Failed adding new error_code to json file. Exiting add_new_error_code", 3)
        return None

def add_new_resol_code(resol_desc: str, device_name: str, issue_type: str):
    # Input: resol description that needs to be added, device_name and issue_type to categorise correctly
    # Return: resol code that this error was assigned to
    new_resol_code = 0
    resolution_descriptions = load_resolutions_descriptions()

    max_error = int(list(resolution_descriptions[device_name][issue_type].values())[0][6:])
    for value in list(resolution_descriptions[device_name][issue_type].values()):
        logger.log(f'Value: {value}. Type: {type(value)}', 0)
        if int(value[6:]) > max_error:
            max_error = int(value[6:])
    category = str(list(resolution_descriptions[device_name][issue_type].values())[0].split(' ')[1][:2])

    new_resol_code = 'Resol ' + category + str(max_error + 1)[-2:]

    resolution_descriptions[device_name][issue_type][resol_desc] = new_resol_code
    if update_resol_json(resolution_descriptions):
        logger.log(f'[{utils.get_time()}] [STATISTICS] Successfully added new resol code for Category: {device_name} '
              f'{issue_type}. Description: {resol_desc}. New resol_code: {new_resol_code}', 1)
        return new_resol_code
    else:
        logger.log(f"[{utils.get_time()}] [STATISTICS] Failed adding new resol_code to json file. Exiting add_new_resol_code", 3)
        return None

def return_device_names():
    error_codes = load_error_descriptions()
    resolution_codes = load_resolutions_descriptions()
    dvcs_errors = list(error_codes.keys())
    dvcs_resols = list(resolution_codes.keys())
    if dvcs_errors == dvcs_resols:
        return dvcs_errors
    else:
        print(f'[{utils.get_time()}] [RETURN DEVICE NAMES] Devices in error_codes.json and in resolution_codes.json'
              f' dont match...', 3)
        return None

def map_errors_and_resolutions_to_codes():
    error_codes = load_error_descriptions()
    device_names = return_device_names()
    if not device_names:
        return None
    first_two_nums = '00'
    for device_id, device in enumerate(device_names):
        first_two_nums = int(first_two_nums)
        first_two_nums += 1
        if first_two_nums < 10:
            first_two_nums = f'0{first_two_nums}'
        else:
            first_two_nums = str(first_two_nums)
        hardware_error_list = list(error_codes[device]['Hardware'])
        software_error_list = list(error_codes[device]['Software'])

        for sw_err_id, sw_err in enumerate(software_error_list):
            second_two_nums = None
            if sw_err_id < 10:
                second_two_nums = f'0{sw_err_id}'
            else:
                second_two_nums = str(sw_err_id)
            error_codes[device]['Software'][sw_err] = \
                f'Error {first_two_nums}{second_two_nums}'
            logger.log(f'Assigning: Error {first_two_nums}{second_two_nums},'
                  f'to {device} software {sw_err}')

        first_two_nums = int(first_two_nums)
        first_two_nums += 1
        if first_two_nums < 10:
            first_two_nums = f'0{first_two_nums}'
        else:
            first_two_nums = str(first_two_nums)

        for hd_err_id, hd_err in enumerate(hardware_error_list):
            second_two_nums = None
            if hd_err_id < 10:
                second_two_nums = f'0{hd_err_id}'
            else:
                second_two_nums = str(hd_err_id)
            logger.log(f'Assigning: Error {first_two_nums}{second_two_nums},'
                  f'to {device} hardware {hd_err}', 3)
            error_codes[device]['Hardware'][hd_err] = \
                f'Error {first_two_nums}{second_two_nums}'

    resolution_codes = load_resolutions_descriptions()
    first_two_nums = '00'
    for device_id, device in enumerate(device_names):
        first_two_nums = int(first_two_nums)
        first_two_nums += 1
        if first_two_nums < 10:
            first_two_nums = f'0{first_two_nums}'
        else:
            first_two_nums = str(first_two_nums)
        hardware_error_list = list(resolution_codes[device]['Hardware'])
        software_error_list = list(resolution_codes[device]['Software'])

        for sw_err_id, sw_err in enumerate(software_error_list):
            second_two_nums = None
            if sw_err_id < 10:
                second_two_nums = f'0{sw_err_id}'
            else:
                second_two_nums = str(sw_err_id)
            resolution_codes[device]['Software'][sw_err] = \
                f'Error {first_two_nums}{second_two_nums}'
            logger.log(f'Assigning: Resol {first_two_nums}{second_two_nums},'
                  f'to {device} software {sw_err}', 3)

        first_two_nums = int(first_two_nums)
        first_two_nums += 1
        if first_two_nums < 10:
            first_two_nums = f'0{first_two_nums}'
        else:
            first_two_nums = str(first_two_nums)

        for hd_err_id, hd_err in enumerate(hardware_error_list):
            second_two_nums = None
            if hd_err_id < 10:
                second_two_nums = f'0{hd_err_id}'
            else:
                second_two_nums = str(hd_err_id)
            logger.log(f'Assigning: Resol {first_two_nums}{second_two_nums},'
                  f'to {device} hardware {hd_err}', 3)
            resolution_codes[device]['Hardware'][hd_err] = \
                f'Resol {first_two_nums}{second_two_nums}'
    update_error_json(error_codes)
    update_resol_json(resolution_codes)

def get_erorr_description_from_code(code):
    if code == '0000':
        return 'Not an issue'
    return get_description(code, load_error_descriptions())

def get_resolution_descrioption_from_code(code):
    if code == '0000':
        return 'Not an issue'
    return get_description(code, load_resolutions_descriptions())

def get_device_name_from_code(code):
    if code == '0000':
        return 'Not an issue'
    return get_dvc_name_iss_type(code, load_error_descriptions())[0]

def get_issue_type_from_code(code):
    if code == '0000':
        return 'Not an issue'
    return get_dvc_name_iss_type(code, load_error_descriptions())[1]

if __name__ == '__main__':
    # print(add_new_error_code('Some stuff happened3', 'Kiosk', 'Hardware'))
    # print(map_errors_to_error_codes())
    # print(map_errors_and_resolutions_to_codes())
    # print(add_new_resol_code('Some stuff happened', 'Kiosk', 'Hardware'))
    pass
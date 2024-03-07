import json
from datetime import datetime
import re

import utils


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
    def get_description(code, descriptions):
        # print(f'[get description] code - {code}, descriptions - {descriptions}')
        for system, categories in descriptions.items():
            for category, errors in categories.items():
                for description, error_code in errors.items():
                    if str(error_code).endswith(code):  # Assuming error codes are unique.
                        return description
        return "Description not found"

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
            print(f'[{utils.get_time()}] [STATISTICS] [PARSE COMMAND DATE] Could not parse '
                  f'start date. Maybe wrong format? Error: {e}')
            return None
    else:
        start_date = min_date

    if till_match:
        try:
            end_date = datetime.strptime(till_match.group(1), '%d.%m.%Y')
        except Exception as e:
            print(f'[{utils.get_time()}] [STATISTICS] [PARSE COMMAND DATE] Could not parse '
                  f'end date. Maybe wrong format? Error: {e}')
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
            file.write(json.dumps(updated_errors))
        return True
    except Exception as e:
        print(f'[{utils.get_time()}] [STATISTICS] Failed updating error_codes.json. Reason:\n\t{e}')
        return False

def add_new_error_code(error_desc: str, device_name: str, issue_type: str):
    # Input: error description of an error that needs to be added, device_name and issue_type to categorise correctly
    # Return: error code that this error was assigned to
    new_error_code = 0
    error_descriptions = load_error_descriptions()

    max_error = int(list(error_descriptions[device_name][issue_type].values())[0][6:])
    for value in list(error_descriptions[device_name][issue_type].values()):
        print(f'Value: {value}. Type: {type(value)}')
        if int(value[6:]) > max_error:
            max_error = int(value[6:])
    category = str(list(error_descriptions[device_name][issue_type].values())[0].split(' ')[1][:2])

    new_error_code = 'Error ' + category + str(max_error + 1)[-2:]

    error_descriptions[device_name][issue_type][error_desc] = new_error_code
    if update_error_json(error_descriptions):
        print(f'[{utils.get_time()}] [STATISTICS] Successfully added new error code for Category: {device_name} '
              f'{issue_type}. Description: {error_desc}. New error_code: {new_error_code}')
        return new_error_code
    else:
        print(f"[{utils.get_time()}] [STATISTICS] Failed adding new error_code to json file. Exiting add_new_error_code")
        return None

if __name__ == '__main__':
    # print(add_new_error_code('Some stuff happened3', 'Kiosk', 'Hardware'))
    print(format_statistics({
        'Error 0101': 12,
        'Error 0102': 2,
        'Error 0201': 20,
        'NotGiven': 100
    }))
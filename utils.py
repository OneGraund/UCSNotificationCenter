from datetime import datetime
import platform


def get_date_and_time():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")

def get_time():
    return datetime.now().strftime("%H:%M:%S")


def get_device_info():
    system_info = {
        "Operating System": platform.system(),
        "OS Release": platform.release(),
        "Architecture": platform.architecture(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
    }
    return system_info

import os
from datetime import datetime


class Logger:
    def __init__(self, filename: str = "", file_extension: str = ".log", logging_level: int = 0):
        self.filename = os.path.join("logs/", filename + file_extension)
        self.logging_level = logging_level

    def log(self, message: str, level: int = 0) -> None:
        """
        :param message: Message that will be bounded
        :param level: Eiter <= 0 for DEBUG, 1 for INFO, 2 for WARNING, 3 for ERROR, 4 for CRITICAL
        :return:
        """

        level_msg = ''
        if level <= 0:
            level_msg = 'DEBUG'
        elif level == 1:
            level_msg = 'INFO'
        elif level == 2:
            level_msg = 'WARNING'
        elif level == 3:
            level_msg = 'ERROR'
        elif level >= 4:
            level_msg = 'CRITICAL'

        if level >= self.logging_level:
            with open(self.filename, "a", encoding='utf-8') as file:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - {level_msg} - {message}")
                file.write(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] - {level_msg} - {message}\n"
                )


# Example usage:
if __name__ == "__main__":
    logger = Logger(filename="logs")
    logger.log("Test debugging message", 0)
    logger.log("Test info message", 1)
    logger.log("Test warning message", 2)
    logger.log("Test error message", 3)
    logger.log("Test critical message", 4)
    print(logger.filename)

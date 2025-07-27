from datetime import datetime
import platform
import os
import time

def get_date_and_time():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")

def get_time():
    return datetime.now().strftime("%H:%M:%S")

def get_date():
    return datetime.now().strftime("%d_%m_%Y")

def get_int_year():
    return int(datetime.now().strftime("%Y"))

def get_int_month():
    return int(datetime.now().strftime("%m"))

def format_incomplete_tickets(tickets):
    to_return = (f'For year {tickets[0][0][1]}, at month {tickets[0][0][2]}, you have {len(tickets[0])} closed tickets '
                 f'with unspecified error/resolution codes:\n')
    for num, ticket in enumerate(tickets[0]):
        to_return += f'• Ticket: {tickets[1][num]}, Rst: {ticket[9]}, day: {ticket[3]}, time: {ticket[4][:5]}\n'
    return to_return + '\nDo you want to start the process to fill tickets?'


def fetch_employees_from_env():
    employees = []
    for i in range(1, 20):
        val = os.getenv(f'EMPLOYEE{i}_NAME')
        if val!='':
            employees.append(val)
        else:
            break
    return employees

def get_device_info():
    system_info = {
        "Operating System": platform.system(),
        "OS Release": platform.release(),
        "Architecture": platform.architecture(),
        "Machine": platform.machine(),
        "Processor": platform.processor(),
    }
    return system_info



class Logger:
    def __init__(self, filename: str = "", file_extension: str = ".log", logging_level: int = 0):
        self.filename = os.path.join("logs/", filename + get_date() + "_" + file_extension)
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

class Locker:
    def __init__(self, logger:Logger, name:str, lock_dir="lockfiles", timeout=22, check_interval=0.1):
        self.logger = logger
        self.lock_dir = lock_dir
        os.makedirs(self.lock_dir, exist_ok=True) # create lock dir, don't raise error if exists
        self.lockfile_path = os.path.join(self.lock_dir, f'{name}.lock') # /lockfiles/kfc_nivy.lock
        self.timeout = timeout
        self.check_interval = check_interval
        self.fd = None
        self.logger.log(f"[LOCKER] [{name.upper()}] locker initiated")

        if os.path.exists(self.lockfile_path):
            try:
                os.remove(self.lockfile_path)
            except Exception as e:
                self.logger.log("[LOCKER] {e}", 4)

    # try to acquire the access to the request by infinitely checking whether the lock file already exists
    # if it does, then we wait maximum of (float) timeout seconds with check intervals of check_interval
    def lock(self) -> bool:
        start_time = time.time()
        while True:
            try:
                # O_CREAT - create if doesn't exist 
                # O_EXCL  - will raise FileExistsError jumping to exception handler if file exists
                # O_RDWR  - opens the file for both read and write (we want to write PID into the file)
                self.fd = os.open(self.lockfile_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self.fd, str(os.getpid()).encode()) # encode because os.write expects bytes
                    # to read: pid = int(f.read().decode())
                self.logger.log(f'[LOCKER] [{self.lockfile_path.upper()}] locked 🔒');
                return True
            except FileExistsError:
                if time.time() - start_time >= self.timeout:
                    return False
                time.sleep(self.check_interval)

    def unlock(self) -> bool:
        try:
            if self.fd is not None: 
                os.close(self.fd)
            if os.path.exists(self.lockfile_path):
                os.remove(self.lockfile_path)
        except Exception:
            return False
        self.logger.log(f'[LOCKER] [{self.lockfile_path.upper()}] unlocked 🔓');
        return True

# Example usage:
if __name__ == "__main__":
    logger = Logger(filename="logs")
    logger.log("Test debugging message", 0)
    logger.log("Test info message", 1)
    logger.log("Test warning message", 2)
    logger.log("Test error message", 3)
    logger.log("Test critical message", 4)
    print(logger.filename)

from datetime import datetime

def get_date_and_time():
    return datetime.now().strftime("%d.%m.%Y %H:%M:%S")

def get_time():
    return datetime.now().strftime("%H:%M:%S")
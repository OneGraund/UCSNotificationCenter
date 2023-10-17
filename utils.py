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

# Example usage:
if __name__ == "__main__":
    device_info = get_device_info()
    for key, value in device_info.items():
        print(f"{key}: {value}")

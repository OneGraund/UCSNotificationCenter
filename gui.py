import os
import platform
import tkinter as tk
import dotenv
import threading
import utils
from tkinter import font

dotenv.load_dotenv()

def input_thread():
    def on_kill():
        print(f"[{utils.get_time()}] Kill switch activated. Exiting gracefully...")
        # Perform any necessary cleanup or finalization tasks here
        os._exit(0)  # Terminate the script immediately

    def on_update():
        print(f"[{utils.get_time()}] Running update.bat...")
        # Run the update.bat file
        os.system("update.bat")

    # Create the tkinter window
    window = tk.Tk()
    window.title("Control Panel")
    window.geometry("200x100")
    window.resizable(False, False)  # Set window size as fixed

    # Configure a dark-grey color scheme
    bg_color = "#333333"  # Dark grey background color
    fg_color = "#ffffff"  # White foreground color

    window.configure(bg=bg_color)

    # Create a frame to contain the buttons
    button_frame = tk.Frame(window, bg=bg_color)
    button_frame.pack(fill="both", expand=True)

    # Define a bold font style
    button_font = font.Font(weight="bold")

    # Create the buttons
    kill_button = tk.Button(button_frame, text="Kill", command=on_kill, bg=bg_color, fg=fg_color, font=button_font)
    kill_button.pack(side="left", fill="both", expand=True)

    update_button = tk.Button(button_frame, text="Update", command=on_update, bg=bg_color, fg=fg_color,
                              font=button_font)
    update_button.pack(side="right", fill="both", expand=True)

    # Start the tkinter event loop
    window.mainloop()


if __name__=='__main__':
    if platform.system()=='Windows':
        input_thread = threading.Thread(target=input_thread)
        input_thread.start()
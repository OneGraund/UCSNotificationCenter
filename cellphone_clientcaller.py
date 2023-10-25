import select
import socket
import sys
import subprocess
import time
import re  # for regular expression matching

def is_valid_phone_number(number):
    # Replace this with your actual validation logic
    return re.fullmatch(r'\+\d{10,15}', number) is not None

while True:
    DEFAULT_HOST = "192.168.192.114"
    DEFAULT_PORT = 10000

    if len(sys.argv) == 1:
        HOST = (DEFAULT_HOST, DEFAULT_PORT)
    elif len(sys.argv) == 2:
        HOST = (DEFAULT_HOST, int(sys.argv[1]))
    else:
        HOST = (sys.argv[2], int(sys.argv[1]))

    main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            main_socket.connect(HOST)
            print(f"Connected to {HOST[0]}:{HOST[1]}")
            break
        except Exception as e:
            print(f"Could not connect to {HOST[0]}:{HOST[1]}. Error: {e}")
            time.sleep(5)

    while True:
        read_buffers = [sys.stdin, main_socket]
        try:
            read_list, _, _ = select.select(read_buffers, [], [])
            for sock in read_list:
                if sock == main_socket:
                    data = sock.recv(4096)
                    if data:
                        data_str = data.decode()
                        if is_valid_phone_number(data_str):
                            try:
                                subprocess.call(f"termux-telephony-call {data_str}", shell=True)
                            except Exception as e:
                                print(f"Failed to initiate call. Error: {e}")
                        print(data_str)
                    else:
                        print("Disconnected from server!")
                        main_socket.close()
                        break
                else:
                    msg = sys.stdin.readline()
                    print(f"You> {msg}")
                    main_socket.send(msg.encode())
        except Exception as e:
            print(f"Error occurred: {e}")
            main_socket.close()
            break

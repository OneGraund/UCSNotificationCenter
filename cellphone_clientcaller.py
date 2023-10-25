#!/usr/bin/env python3

import select
import socket
import sys
import subprocess
import time

# usage: ./client.py [PORT] [HOST]

while True:  # Infinite loop to attempt reconnection
    if len(sys.argv) == 1:
        HOST = ("localhost", 10000)
    elif len(sys.argv) == 2:
        HOST = ("localhost", int(sys.argv[1]))
    else:
        HOST = (sys.argv[2], int(sys.argv[1]))

    main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:  # Infinite loop to attempt connection
        try:
            main_socket.connect(HOST)
            sys.stdout.write("Connected to " + HOST[0] + ":" + str(HOST[1]) + '\n')
            sys.stdout.flush()
            break  # Exit the loop if connected
        except:
            sys.stdout.write("Could not connect to " + HOST[0] + ":" + str(HOST[1]) + '\n')
            sys.stdout.flush()
            time.sleep(5)  # Wait for 5 seconds before trying again

    while True:
        read_buffers = [sys.stdin, main_socket]
        try:
            read_list, write_list, error_list = select.select(read_buffers, [], [])
            for sock in read_list:
                if sock == main_socket:
                    data = sock.recv(4096)
                    if data:
                        data = data.decode()
                        if '+' in str(data):
                            subprocess.call(f"termux-telephony-call {str(data)}", shell=True)
                        sys.stdout.write(data)
                        sys.stdout.flush()
                    else:
                        print("Disconnected from server!")
                        main_socket.close()
                        break  # break inner loop to reattempt connection
                else:
                    msg = sys.stdin.readline()
                    sys.stdout.write("You> " + msg)
                    sys.stdout.flush()
                    main_socket.send(msg.encode())
        except Exception as e:
            print(f'Error occurred {e}')
            main_socket.close()
            break  # break inner loop to reattempt connection

import dotenv
import os

dotenv.load_dotenv()
import socket
import socketserver
import utils
import threading
import time
import sys

SERVER_TIMEOUT = 1


def call_employee_with_priority(employees, priority, chanel_name=None):
    # Open call_request.txt and create a request for server to send call
    if priority==0:
        employee = employees[0]
    elif priority <= (len(employees)-1) and priority!=0:
        employee = employees[priority]
    else:
        print(f'[{utils.get_date_and_time()}] [CALL_EMPLOYEE_WITH_PRIORITY] [{chanel_name.upper()}] '
              f'Wrong priority specified. Priority = {priority}')
        return None

    cellphone = 'Main'

    with open('call_request.txt', 'w') as call_request:
        print(f'{employee.upper()}_{cellphone.upper()}CELLPHONE_NUMBER')
        number = os.getenv(f'{employee.upper()}_{cellphone.upper()}CELLPHONE_NUMBER')
        print(f'[{utils.get_date_and_time()}] Sending request to call {number}')
        call_request.writelines(
            [number]
        )


def start_telephony_server(HOST=('192.168.192.114', 10000)):
    CLIENTS = []

    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        pass

    class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
        def handle(self):
            CLIENTS.append(self.request)
            welcomeMsg = self.client_address[0] + ":" + str(self.client_address[1]) + " joined." + '\n'
            sys.stdout.write(welcomeMsg)
            sys.stdout.flush()
            for cli in CLIENTS:
                if cli is not self.request:
                    cli.sendall(welcomeMsg.encode())
            while True:
                data = self.request.recv(4096)
                if data:
                    data = data.decode()
                    sendMsg = self.client_address[0] + ":" + str(self.client_address[1]) + "> " + data
                    sys.stdout.write(sendMsg)
                    sys.stdout.flush()
                    for cli in CLIENTS:
                        if cli is not self.request:
                            cli.sendall(sendMsg.encode())
                else:
                    sendMsg = self.client_address[0] + ":" + str(self.client_address[1]) + " left." + '\n'
                    sys.stdout.write(sendMsg)
                    sys.stdout.flush()
                    CLIENTS.remove(self.request)
                    for cli in CLIENTS:
                        cli.sendall(sendMsg.encode())
                    break

    print(f'[{utils.get_date_and_time()}] [CALLING SERVER] Starting calling server at {HOST}')

    server = ThreadedTCPServer(HOST, ThreadedTCPRequestHandler)
    server.daemon_threads = True

    server_thread = threading.Thread(target=server.serve_forever)

    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    print(f'[{utils.get_date_and_time()}] [CALLING SERVER] Server started, now in infinity loop')
    while 1:
    #try:
        with open('call_request.txt', 'r') as file:
            lines = file.readlines()
        # print(lines)          # DEBUG
        if lines[0].find('+')!=-1:
            print(f'[{utils.get_date_and_time()}] [TELEPHONY SERVER] Sending a request '
                  f'to a client_android_phone to call {lines[0]}')
            for client in CLIENTS:
                client.sendall(f'{lines[0]}\n'.encode())
                lines[0]='None'
            with open('call_request.txt', 'w') as file:
                file.writelines('None')
    #except Exception as e:
        #print(f'[{utils.get_date_and_time()}] [CALLING SERVER] An error occured when running server.'
             # f'Details:\n{e}')

        time.sleep(SERVER_TIMEOUT)

    server.shutdown()
    server.server_close()
    sys.stdout.write("Server is closed." + '\n')
    sys.stdout.flush()


if __name__ == '__main__':
    start_telephony_server()

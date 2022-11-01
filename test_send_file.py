import base64
import os
import time
from threading import Thread
from time import sleep
from tkinter import filedialog

import stomper
from tkinterDnD import tk

from mr_power_manager import StompClient

BYTES_LIMIT = 10240
token = 'MrPio'
pcName = 'i7-10750H'
stomp_client = StompClient(token, pcName, None)


def send_base64(data, header, wait=0.001):
    if (data == ''):
        return
    print(len(data))
    maxStomps = int(len(data) / BYTES_LIMIT)
    stomp = stomper.send(dest="/app/sendMessage/to/client/" + token + "/" + pcName,
                         msg='START_OF_MESSAGE@@@' + header + '@@@' + str(maxStomps + 1))
    stomp_client.ws.send(stomp)
    for i in range(maxStomps + 1):
        print(round(i * 100 / maxStomps, 1))
        if i < maxStomps:
            stomp = stomper.send(dest="/app/sendMessage/to/client/" + token + "/" + pcName,
                                 msg=data[i * BYTES_LIMIT:(i + 1) * BYTES_LIMIT])
        elif i == maxStomps:
            stomp = stomper.send(dest="/app/sendMessage/to/client/" + token + "/" + pcName,
                                 msg=data[maxStomps * BYTES_LIMIT:])

        # if len(list(data)) > BYTES_LIMIT:
        #     data = data[BYTES_LIMIT:]
        # stomp = stomper.send(dest="/app/sendMessage/to/client/" + token + "/" + pcName, msg=msg)
        stomp_client.ws.send(stomp)
        time.sleep(wait)

    # stomp = stomper.send(dest="/app/sendMessage/to/client/" + token + "/" + pcName,
    #                      msg='END_OF_MESSAGE')
    # stomp_client.ws.send(stomp)


def connect_socket():
    StompClient.KEEP_ALIVE = True

    if not StompClient.IS_RUNNING:
        print('Stomp client offline! Gonna start it...')
        t = Thread(target=stomp_client.create_connection)
        t.daemon = True
        t.start()
        c = 0
        while not StompClient.IS_RUNNING:
            sleep(0.5)
            c += 1
            if c > 32:
                raise 'timeout nella connessione del socket!'
        print('Now the stomp client is online!')


connect_socket()
stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='True')
stomp_client.ws.send(stomp)

root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename()
if file_path != '' and os.path.getsize(filename=file_path) < 512000000:
    with open(file_path, "rb") as file:
        base64_file = base64.b64encode(file.read()).decode("utf-8")
        send_base64(base64_file, 'FILE_FROM_SERVER:' + file_path.split('/')[-1], wait=0.015)

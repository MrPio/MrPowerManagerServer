import os
import socket
import time

IP = socket.gethostbyname(socket.gethostname())
HOST = '0.tcp.eu.ngrok.io'    # The remote host
PORT = 11803
ADDR = (HOST, PORT)
FORMAT = "utf-8"
SIZE = 1024


def main2():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IP, PORT))

def main():
    print(IP)
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    file = open("to_send", "rb")
    data = file.read()
    client.send(str(os.path.getsize(filename="to_send")).encode(FORMAT))
    client.send(data)
    # time.sleep(1)
    # msg = client.recv(SIZE).decode(FORMAT)
    # print(f"[SERVER]: {msg}")
    file.close()
    client.close()


if __name__ == "__main__":
    main()

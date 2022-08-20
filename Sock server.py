import datetime
import socket
import time

IP = socket.gethostbyname(socket.gethostname())
PORT = 80
ADDR = (IP, PORT)
SIZE = 1024*100
FORMAT = "utf-8"


def main():
    print("[STARTING] Server is starting.")
    print(IP)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print("[LISTENING] Server is listening.")

    while True:
        print(f"[WAITING FOR CONNECTION]...")
        #QUI IL SERVER ASPETTA LA CONNESSIONE DI UN CLIENT
        conn, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected.")

        file = open('file_ricevuto', "wb")
        file_size=0
        count=0
        start=''
        while True:
            #QUI IL SERVER ASPETTA DATA DAL CLIENT O LA SUA CHIUSURA
            data = conn.recv(SIZE)
            if not data:
                file.close()
                break
            print(data.decode(FORMAT))
            print('    ')

            # if file_size==0:
            #     file_size=int(data.decode(FORMAT))
            #     start = time.time_ns()
            #     continue
            # count+=1
            # # if count*SIZE/file_size>=1:
            # print(str((time.time_ns() - start) / 1000000) + ' --->' +
            #       str(round(count * 100 * SIZE / file_size, 2)) + '%')
            # file.write(data)
            # conn.send("File data received".encode(FORMAT))
            # conn.close()
            # print(f"[DISCONNECTED] {addr} disconnected.")

if __name__ == "__main__":
    main()

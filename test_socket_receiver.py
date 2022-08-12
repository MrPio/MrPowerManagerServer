# import random
#
# import stomper
# import websocket
#
#
# class MSG(object):
#     def __init__(self, msg):
#         self.msg = msg
#         sp = self.msg.split("\n")
#         self.destination = sp[1].split(":")[1]
#         self.content = sp[2].split(":")[1]
#         self.subs = sp[3].split(":")[1]
#         self.id = sp[4].split(":")[1]
#         self.len = sp[5].split(":")[1]
#         # sp[6] is just a \n
#         self.message = ''.join(sp[7:])[0:-1]  # take the last part of the message minus the last character which is \00
#
#
#
# websocket.enableTrace(True)
#
# # Connecting to websocket
# ws = websocket.create_connection("ws://localhost:5000/chat")
#
# # Subscribing to topic
# username = 'MrPio'
# client_id = str(random.randint(0, 1000))
#
# sub = stomper.subscribe("/topic/greeting" , client_id, ack='auto')
# ws.send(sub)
#
# # Sending some message
# # ws.send(stomper.send("/app/chat/MrPio2", ("Hello there!")))
#
# while True:
#     print("Receiving data: ")
#     d = ws.recv()
#     print(MSG(d))
#
"""
Author: srinivas.kumarr
Python client for interacting with a server via STOMP over websockets.
"""
import datetime
import json
from threading import Thread

import pyautogui
import websocket
import stomper
import queue


ws_uri = "ws://localhost:5000/chat/websocket"
# ws_uri = "ws://mrpowermanager.herokuapp.com/chat/websocket"


class StompClient(object):
    NOTIFICATIONS = None
    KEEP_ALIVE = True
    IS_RUNNING = False
    DESTINATIONS = ["/server/MrPio/i7_10750H/commands"]

    # Do note that in this case we use jwt_token for authentication hence we are
    # passing the same in the headers, else we can pass encoded passwords etc.
    def __init__(self, jwt_token):
        """
        Initializer for the class.
        Args:
          jwt_token(str): JWT token to authenticate.
          server_ip(str): Ip of the server.
          port_number(int): port number through which we want to make the
                            connection.
          destinations(list): List of topics which we want to subscribe to.
        """
        self.NOTIFICATIONS = queue.Queue()
        if jwt_token is not None:
            self.headers = {"Authorization": "Bearer " + jwt_token}
        else:
            self.headers = {}
        self.ws = None

    @staticmethod
    def on_open(ws):
        """
        Handler when a websocket connection is opened.
        Args:
          ws(Object): Websocket Object.
        """
        # Initial CONNECT required to initialize the server's client registries.
        ws.send("CONNECT\naccept-version:1.0,1.1,2.0\n\n\x00\n")

        # Subscribing to all required desitnations.
        for destination in StompClient.DESTINATIONS:
            sub = stomper.subscribe(destination, "uniqueId", ack="auto")
            ws.send(sub)
        StompClient.IS_RUNNING = True
        print("The websocket connection is open.")

    def sendKeepAlive(self):
        while True:
            pyautogui.sleep(48)
            if not StompClient.KEEP_ALIVE:
                print("Keep alive pooling deactivated!")
                return
            print("sending keepAlive packet...")
            self.ws.send(stomper.send("/app/keepAlive", "keepAlive"))

    def create_connection(self):
        """
        Method which starts of the long term websocket connection.
        """

        self.ws = websocket.WebSocketApp(ws_uri, header=self.headers,
                                         on_message=self.on_msg,
                                         on_error=self.on_error,
                                         on_close=self.on_closed)
        self.ws.on_open = self.on_open

        Thread(target=self.sendKeepAlive).start()

        # Run until interruption to client or server terminates connection.
        self.ws.run_forever()

    def add_notifications(self, msg):
        """
        Method to add a message to the websocket queue.
        Args:
          msg(dict): Unpacked message received from stomp watches.
        """
        self.NOTIFICATIONS.put(msg)

    def on_msg(self, c, msg):
        """
        Handler for receiving a message.
        Args:
          msg(str): Message received from stomp watches.
        """
        frame = stomper.Frame()
        unpacked_msg = stomper.Frame.unpack(frame, msg)
        if len(unpacked_msg['body'])>1:
            command = dict(json.loads(unpacked_msg['body']))
            if 'command' in command.keys():
                command=Command(
                    command['command'],int(command['id']),int(command['commandValue']),command['commandScheduledDate'])
                execute_command(command)

    def on_error(self, err, b):
        """
        Handler when an error is raised.
        Args:
          err(str): Error received.
        """
        print("The Error is:- " + str(b))

    def on_closed(self, a, b, c):
        """
        Handler when a websocket is closed, ends the client thread.
        """
        StompClient.IS_RUNNING = False
        print("The websocket connection is closed.")

# stomp_client = StompClient(None)
# stomp_client.create_connection()

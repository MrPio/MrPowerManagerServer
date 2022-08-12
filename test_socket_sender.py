from random import randrange

import pyautogui
import stomper
import websocket

# ws_uri = "ws://localhost:5000/chat/websocket"
ws_uri = "ws://mrpowermanager.herokuapp.com/chat/websocket"
ws = websocket.create_connection(ws_uri)

# msg=['PLAY_PAUSE',156,'']
# stomp=stomper.send(dest="/app/scheduleCommand/MrPio/i7-10750H",msg=''.join(str(x)+"~" for x in msg)[0:-1])
# ws.send(stomp)
while 1:
    msg = [randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), randrange(100), 1258]
    stomp = stomper.send(dest="/app/updatePcStatus/MrPio/i7-10750H", msg=''.join(str(x) + "~" for x in msg)[0:-1])
    ws.send(stomp)
    pyautogui.sleep(1)

msg = [True]
stomp = stomper.send(dest="/app/setOnline/MrPio/i7-10750H", msg=''.join(str(x) + "~" for x in msg)[0:-1])
ws.send(stomp)


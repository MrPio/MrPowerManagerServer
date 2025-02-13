from __future__ import unicode_literals

import asyncio
import base64
import ctypes
import json
import math
import os
import queue
import re
import sched
import sys
import time
from fernet import FernetCipher
import tkinter as tk
import tkinter.font as font
import webbrowser
from asyncio import sleep
from ctypes import cast, POINTER
from datetime import datetime
from pathlib import Path
from threading import Thread
from tkinter import filedialog, X
from tkinter.ttk import Progressbar, Style

import PIL.Image
import cv2
import ffmpeg
import icoextract
import numpy as np
import polling2
import psutil
import pyautogui
import pygame
import pyperclip
import pystray
import requests
import screen_brightness_control
import stomper
import tkinterDnD as tkdnd
import userpaths
import websocket
import win32api
import win32security
import wmi
from GPUtil import GPUtil
from PIL import Image, ImageGrab
from PIL.Image import Resampling, Palette
from comtypes import CLSCTX_ALL
from cv2 import VideoCapture
from dragonfly import Window
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
# ws_uri = "ws://localhost:5000/chat/websocket"
from pynput.keyboard import Controller

# ===========================================================================================
# ===========================================================================================

ws_uri = "ws://mrpowermanager.herokuapp.com/chat/websocket"
# ws_uri = "ws://localhost:5000/chat/websocket"

message = ''


# its_me_who_is_sending_message = False


class StompClient(object):
    NOTIFICATIONS = None
    KEEP_ALIVE = True
    IS_RUNNING = False
    DESTINATIONS = []

    # Do note that in this case we use jwt_token for authentication hence we are
    # passing the same in the headers, else we can pass encoded passwords etc.
    def __init__(self,token,pcName, jwt_token):
        """
        Initializer for the class.
        Args:
          jwt_token(str): JWT token to authenticate.
          server_ip(str): Ip of the server.
          port_number(int): port number through which we want to make the
                            connection.
          destinations(list): List of topics which we want to subscribe to.
        """
        StompClient.DESTINATIONS=[
            "/server/" + re.sub('[^a-zA-Z0-9 \n.]', '_', token) + "/" + re.sub('[^a-zA-Z0-9 \n.]', '_',
                                                                               pcName) + "/commands",

            "/server/" + re.sub('[^a-zA-Z0-9 \n.]', '_', token) + "/online",

            "/server/" + re.sub('[^a-zA-Z0-9 \n.]', '_', token) + "/" + re.sub('[^a-zA-Z0-9 \n.]', '_',
                                                                               pcName) + "/message",
            ]
        self.NOTIFICATIONS = queue.Queue()
        if jwt_token is not None:
            self.headers = {"Authorization": "Bearer " + jwt_token}
        else:
            self.headers = {}
        self.ws = None

    pygame_mix_started = False

    @staticmethod
    def on_open(ws):
        global log
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
        add_log( "The websocket connection is open.")
        StompClient.IS_RUNNING = True

    def sendKeepAlive(self):
        global log
        pyautogui.sleep(3)
        while True:
            if not StompClient.KEEP_ALIVE:
                add_log( "Keep alive pooling deactivated!")
                return
            add_log( "sending keepAlive packet...")
            try:
                self.ws.send(stomper.send("/app/keepAlive", "keepAlive"))
                pyautogui.sleep(30)
            except Exception as e:
                add_log( "COULD NOT SEND KEEP ALIVE! another try in 2 secs...")
                pyautogui.sleep(2)

    def create_connection(self):
        """
        Method which starts of the long term websocket connection.
        """

        if self.ws is None:
            self.ws = websocket.WebSocketApp(ws_uri, header=self.headers,
                                             on_message=self.on_msg,
                                             on_error=self.on_error,
                                             on_close=self.on_closed)
            Thread(target=self.sendKeepAlive).start()

            self.ws.on_open = self.on_open

        # Run until interruption to client or server terminates connection.
        self.ws.run_forever()

    def add_notifications(self, msg):
        """
        Method to add a message to the websocket queue.
        Args:
          msg(dict): Unpacked message received from stomp watches.
        """
        self.NOTIFICATIONS.put(msg)

    def go_offline(self):
        global log

        global client_online
        while (datetime.now() - last_client_online).seconds < 20:
            if not client_online:
                return
            time.sleep(3)
        log += ('\n' + datetime.now().strftime(
            "%H-%M-%S") + ' -> ' + 'il cliente non si è fatto più sentire... concludo che è andato offline!')
        client_online = False

    def on_msg(self, c, msg):
        global log

        """
        Handler for receiving a message.
        Args:
          msg(str): Message received from stomp watches.
        """
        frame = stomper.Frame()
        unpacked_msg = stomper.Frame.unpack(frame, msg)
        if len(unpacked_msg['body']) <= 1:
            return
        socket_message = dict(json.loads(unpacked_msg['body']))
        add_log( str(socket_message))
        if 'command' in socket_message.keys():
            socket_message = Command(
                socket_message['command'], int(socket_message['id']), int(socket_message['commandValue']),
                socket_message['commandScheduledDate'])
            execute_command(socket_message)
        elif 'message' in socket_message.keys():

            if 'SHARE_CLIPBOARD' in socket_message['message']:
                val = socket_message['message'].split('@@@')[1]
                if val != 'null':
                    pyperclip.copy(val)
                return
            global message
            max = int(socket_message['message'].split('@@@')[2])
            index = int(socket_message['message'].split('@@@')[1])
            if (index == 0):
                message = ''
            message += socket_message['message'].split('@@@')[3]
            if (index == max):
                add_log( 'gonna reproduce audio')
                decode_string = base64.b64decode(message)
                path = userpaths.get_local_appdata() + '\MrPowerManager\\rec ' + datetime.now().strftime(
                    "%Y-%m-%d %H-%M-%S") + '.mp3'
                open(path, "wb").write(decode_string)
                if (not self.pygame_mix_started):
                    pygame.mixer.init()
                    self.pygame_mix_started = True
                # pygame.mixer.music.stop()
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
        elif 'online' in socket_message.keys():
            global last_client_online, client_online
            if str(socket_message['online']).lower() == 'true':
                last_client_online = datetime.now()
                if not client_online:
                    add_log( 'client è andato ONLINE!')
                    client_online = True
                    Thread(target=self.go_offline).start()
            else:
                if client_online:
                    add_log( 'client è andato offline!')
                client_online = False

    def on_error(self, err, b):
        """
        Handler when an error is raised.
        Args:
          err(str): Error received.
        """
        global log
        add_log( "The Error is:- " + str(b))
        log += ('\n' + datetime.now().strftime("%H-%M-%S") + 'provo a risolvere riavviando create_connection()')
        self.ws.close()
        self.create_connection()

    def on_closed(self, a, b, c):
        global log

        """
        Handler when a websocket is closed, ends the client thread.
        """
        StompClient.IS_RUNNING = False
        add_log( "The websocket connection is closed.")
        # log+=('\n'+datetime.now().strftime("%H-%M-%S")+'provo a risolvere riavviando create_connection()')
        # self.create_connection()


# ===========================================================================================
# ===========================================================================================
def add_log(str):
    global log
    log += ('\n ' + datetime.now().strftime("%H-%M-%S") + ' -> ' +str)


UPDATE_STATUS = 1
CLIENT_OFFLINE = 3
STREAMING_SPEED = 0.4
WEBCAM_SPEED = 0.1
STREAMING_QUALITY = 15
WEBCAM_QUALITY = 30
STREAMING_TIMEOUT = 12
BYTES_LIMIT = 15000
REQUEST_AVAILABLE_COMMANDS = 2
web = "https://mrpowermanager.herokuapp.com"

token = ''
pcName = ''
battery_perc = 0
battery_plugged = False
battery_left = 0
battery_charge_rate = 0
battery_discharge_rate = 0
cpu_usage = 0
ram_usage = 0
disk_usage = 0
gpu_usage = 0
gpu_temp = 0
wifi = False
wifi_interface = ""
volume = 0
brightness = 0
available_commands_response = None
last_volume = 0
# is_locked = False
# is_locked_last = datetime(2000, month=1, day=1)
last_client_online = datetime(2000, 1, 1)
last_streaming_start = datetime(2000, 1, 1)
last_webcam_start = datetime(2000, 1, 1)
wattage_entries = []
thread_get_commands_online = True
open_windows = []
last_open_windows = []
log = ''

c = wmi.WMI()
t = wmi.WMI(moniker="//./root/wmi")

keyboard = Controller()

force_exit = False

volume_interface = None
win_ver = 11

event_schedule = sched.scheduler(time.time, time.sleep)

stomp_client = None
# websocket_sender = websocket.create_connection(ws_uri)

collect_wattage_in_background = True
client_online = False
shareClipboard = False

base64Screen = ''
base64Webcam = ''
cam = ''


def clipboard_listener():
    recent_value = ""
    global log
    while True:
        if not shareClipboard:
            time.sleep(2)
            continue
        tmp_value = pyperclip.paste()

        if recent_value not in [tmp_value]:
            try:
                if type(stomp_client.ws) == type(None):
                    time.sleep(1)
                    continue

                image = ImageGrab.grabclipboard()
                if image != None:
                    path = userpaths.get_local_appdata() + '\MrPowerManager\screen.jpg'
                    image.convert('RGB').save(path, "JPEG", optimize=True, quality=int(95))
                    with open(path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
                        if recent_value == image:
                            time.sleep(1)
                            continue
                        recent_value = image
                        send_base64(base64_image, 'CLIPBOARD_IMAGE')
                else:
                    recent_value = tmp_value

                    add_log( "Value changed: %s" % str(
                        recent_value)[:100])

                    send_base64(recent_value, 'SHARE_CLIPBOARD')
                    # stomp = stomper.send(dest="/app/sendMessage/to/client/" + token + "/" + pcName,
                    #                      msg='SHARE_CLIPBOARD@@@' + recent_value)
                    # stomp_client.ws.send(stomp)
            except Exception as e:
                add_log( 'err--->' + str(e))

        time.sleep(0.5)


async def work_offline():
    global log
    add_log( 'work_offline() start')
    global wattage_entries
    while True:

        get_wattage_data()
        # Thread(target=get_wattage_data).start()
        entry = {
            "dateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "isPlugged": battery_plugged,
            "cpuPercentage": cpu_usage,
            "gpuPercentage": gpu_usage,
            "ramPercentage": ram_usage,
            "diskPercentage": disk_usage,
            "temp": gpu_temp,
            "batteryPercentage": battery_perc,
            "batteryChargeRate": battery_charge_rate,
            "batteryDischargeRate": battery_discharge_rate
        }
        wattage_entries.append(entry)
        add_log( 'wattage_entries--->' + str(len(wattage_entries)))

        if len(wattage_entries) > 1:
            add_log( 'upload_wattage_entries')
            Thread(target=upload_wattage_entries).start()

        await asyncio.sleep(240)

        if not collect_wattage_in_background or force_exit:
            return


# def is_client_online():
#     global last_client_online, client_online
#     while True:
#         if force_exit:
#             return
#
#         # TODO if list_files("/database/clients").__contains__(token + ".user"):
#         if True:
#             if not client_online:
#                 log+=('\n'+datetime.now().strftime("%H-%M-%S")+' -> '+'client è andato ONLINE!')
#             client_online = True
#             last_client_online = datetime.now()
#             time.sleep(12)
#         else:
#             if client_online:
#                 log+=('\n'+datetime.now().strftime("%H-%M-%S")+' -> '+'client è andato offline!')
#             client_online = False
#             time.sleep(3)

def get_open_windows_and_icons():
    global open_windows, last_open_windows, log
    windows = Window.get_all_windows()
    c = 0
    data = ''
    open_windows = []
    for window in windows:
        if window.is_visible and window._get_window_text() != '':
            try:
                path = userpaths.get_local_appdata() + '\MrPowerManager' + '\\icon_' + str(c)
                icoextract.IconExtractor(window.executable).export_icon(path + '.png')
                pil_image = Image.open(path + '.png')

                pil_image = pil_image.resize((96, 96), Resampling.LANCZOS)
                pil_image = pil_image.convert("P", palette=Palette.ADAPTIVE, colors=256)
                c += 1
                pil_image.save(path + '.png', optimize=True)
                open_windows.append(window)
                data += window._get_window_text()
                with open(path + '.png', "rb") as image_file:
                    data += '~' + base64.b64encode(image_file.read()).decode("utf-8") + '#'

            except Exception:
                pass
    # if last_open_windows==open_windows:
    #     return ''
    # last_open_windows=open_windows
    return data


def start_up_commands():
    global log
    if request_available_commands().status_code == 200:
        add_log( "found commands!")
        response_dict = dict(available_commands_response.json())
        if 'pc not found' in response_dict['result']:
            add_log( "pc does not exit")
            path = userpaths.get_local_appdata() + '\MrPowerManager'
            os.remove(path + '\config.dat')
            global force_exit
            force_exit = True
            exit()

        for command in response_dict['commands']:
            execute_command(
                Command(command['command'], command['id'], command['commandValue'],
                        command['commandScheduledDate']))


def screen_to_base64():
    global log

    global base64Screen
    path = userpaths.get_local_appdata() + '\MrPowerManager\screen'
    pyautogui.screenshot().save(path,
                                "JPEG",
                                optimize=True,
                                quality=int(STREAMING_QUALITY))
    with open(path, "rb") as image_file:
        base64Screen = base64.b64encode(image_file.read()).decode("utf-8")


def webcam_to_base64():
    global log

    global base64Webcam
    result, image = cam.read()
    if result:
        path = userpaths.get_local_appdata() + '\MrPowerManager\webcam'
        Image.fromarray(image).convert('L').save(path,
                                                 "JPEG",
                                                 optimize=True,
                                                 quality=int(WEBCAM_QUALITY))
        with open(path, "rb") as image_file:
            base64Webcam = base64.b64encode(image_file.read()).decode("utf-8")
    else:
        base64Webcam = ''


def record_screen(fps='30', duration='5', quality='25', h265='True'):
    global log

    codec = 'libx265' if h265.__str__().lower() == 'true' else 'libx264'
    path = userpaths.get_desktop() + '\\' + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + '.mkv'
    process2 = (
        ffmpeg
            .input('pipe:')
            .filter('fps', fps=fps, round='up')
            .output(path, vcodec=codec, crf=quality, video_track_timescale='420000')
            .overwrite_output()
            .run_async(pipe_stdin=True)
    )
    now = datetime.now()

    while (datetime.now() - now).seconds <= int(duration):
        img = pyautogui.screenshot()
        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        _, encoded_image = cv2.imencode('.jpg', img)
        # Write the frame into the file 'output.avi'
        process2.stdin.write(
            encoded_image
                .astype(np.uint8)
                .tobytes()
        )


maxStomps = 0
send_start = time.time_ns()


def send_base64(data, header, make_progress=False, wait=0.001):
    global log

    global force_block, maxStomps, send_start
    if (data == ''):
        return
    add_log( str(len(data)))
    maxStomps = int(len(data) / BYTES_LIMIT)
    stomp = stomper.send(dest="/app/sendMessage/to/client/" + token + "/" + pcName,
                         msg='START_OF_MESSAGE@@@' + header + '@@@' + str(maxStomps + 1))
    stomp_client.ws.send(stomp)
    send_start = time.time_ns()
    for i in range(maxStomps + 1):
        if force_block:
            force_block = False
            return
        if (make_progress):
            progress(round(i * 100 / maxStomps, 1))
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


def streaming():
    global log

    global base64Screen
    add_log( 'STREAMING started...')
    screen_to_base64()
    while True:
        if (datetime.now() - last_streaming_start).seconds > STREAMING_TIMEOUT:
            add_log( 'STREAMING stopped...')
            # its_me_who_is_sending_message = False
            time.sleep(6)
        else:
            Thread(target=screen_to_base64).start()
            # its_me_who_is_sending_message = True
            send_base64(base64Screen, 'STREAMING')

        time.sleep(STREAMING_SPEED)


def webcam():
    global log

    global base64Webcam, cam
    add_log( 'WEBCAM started...')
    if type(cam) == str and cam == '':
        cam = VideoCapture(0)
    webcam_to_base64()
    while True:
        if (datetime.now() - last_webcam_start).seconds > STREAMING_TIMEOUT:
            cam.release()
            add_log( 'WEBCAM stopped...')
            # its_me_who_is_sending_message = False
            time.sleep(5)
        else:
            if not cam.isOpened():
                cam.open(0)

            # its_me_who_is_sending_message = True
            Thread(target=webcam_to_base64).start()
            send_base64(base64Webcam, 'WEBCAM', False, 0.001)

        time.sleep(WEBCAM_SPEED)


# check_client_online_thread = Thread(target=is_client_online)
streaming_thread = Thread(target=streaming)
webcam_thread = Thread(target=webcam)
clipboard_thread = Thread(target=clipboard_listener)


# Here is the heart of the script
async def update_status():
    global log

    add_log( 'avvio update_status()...')
    asyncio.create_task(work_offline())
    add_log( 'work_offline thread started')

    start_up_commands()
    add_log( 'start_up_commands done')
    # time.sleep(16)

    clipboard_thread.start()
    add_log( 'clipboard_thread thread started')

    # log+=('\n'+datetime.now().strftime("%H-%M-%S")+' -> '+'avvio check_client_online_thread()...')
    # check_client_online_thread.start()
    while True:
        if force_exit:
            return
        StompClient.KEEP_ALIVE = True

        if not StompClient.IS_RUNNING:
            add_log( 'Stomp client offline! Gonna start it...')
            try:
                t = Thread(target=stomp_client.create_connection)
                t.daemon = True
                t.start()
                c = 0
                while not StompClient.IS_RUNNING:
                    await sleep(0.5)
                    c += 1
                    if c > 32:
                        raise 'timeout nella connessione del socket!'
                add_log( 'Now the stomp client is online!')

            except Exception as e:
                add_log( 'errore 3 catturato! ', e)

        if not client_online:
            # if stomp_client.ws is not None and StompClient.IS_RUNNING:
            #     stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='False')
            #     stomp_client.ws.send(stomp)
            #
            #     StompClient.KEEP_ALIVE = False
            #     stomp_client.ws.close()
            await sleep(CLIENT_OFFLINE)

        else:
            stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='True')
            stomp_client.ws.send(stomp)
            add_log( '/app/setOnline/  TRUE!')

            # if not thread_get_commands_online:
            #     start_thread_get_list_commands()

            Thread(target=get_pc_data).start()
            await sleep(UPDATE_STATUS)
            # url = web + '/updatePcStatus'
            # headers = {
            #     'Content-type': 'application/json',
            #     'Accept': 'application/json'
            # }
            # data = {
            #     "wifi": wifi,
            #     'bluetooth': True,  # <===================================
            #     'batteryPlugged': battery_plugged,
            #     'sound': volume,
            #     'brightness': brightness,
            #     'batteryPerc': battery_perc,
            #     'batteryMinutes': battery_left,
            #     'batteryChargeRate': battery_charge_rate,
            #     'batteryDischargeRate': battery_discharge_rate,
            #     'cpuLevel': cpu_usage,
            #     'gpuLevel': gpu_usage,
            #     'gpuTemp': gpu_temp,
            #     'ramLevel': ram_usage,
            #     'storageLevel': disk_usage,
            #     'airplane': wifi,  # <===================================REMOVED
            #     'mute': volume == 0,
            #     'redLight': False,  # <===================================
            #     'saveBattery': False,  # <===================================REMOVED
            #     'hotspot': False,  # <===================================
            #     'redLightLevel': 50,  # <===================================REMOVED
            #     'isLocked': is_locked,
            # }
            msg = [wifi, True, battery_plugged, wifi, volume == 0, False,
                   False, False, shareClipboard, volume, brightness, battery_perc
                , battery_left, cpu_usage, ram_usage, 50, disk_usage
                , gpu_usage, gpu_temp, battery_charge_rate, battery_discharge_rate]
            stomp = stomper.send(dest="/app/updatePcStatus/" + token + "/" + pcName,
                                 msg=''.join(str(x) + "~" for x in msg)[0:-1])
            stomp_client.ws.send(stomp)
            add_log( '/app/updatePcStatus/')

            # log+=('\n'+datetime.now().strftime("%H-%M-%S")+' -> '+"pcStatus sent through Socket!")

            # params = {
            #     'token': token,
            #     'pcName': pcName,
            # }

            # response = requests.post(url, headers=headers, params=params, data=json.dumps(data))
            # log+=('\n'+datetime.now().strftime("%H-%M-%S")+' -> '+response.content)


def upload_wattage_entries():
    global log

    url = web + '/uploadWattageEntries'
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json'
    }
    params = {
        'token': token,
        'pcName': pcName,
    }
    global wattage_entries

    response = requests.post(url, headers=headers, params=params, data=json.dumps(wattage_entries))
    wattage_entries = []
    add_log( response.content.decode('utf-8'))


def get_wattage_data():
    global log

    battery = psutil.sensors_battery()
    global battery_perc, battery_plugged, battery_left
    battery_perc = battery.percent
    battery_plugged = battery.power_plugged

    global battery_charge_rate, battery_discharge_rate, batteries
    batteries = t.ExecQuery('Select * from BatteryStatus where Voltage > 0')
    _, b = list(enumerate(batteries))[0]
    battery_charge_rate = b.ChargeRate
    battery_discharge_rate = b.DischargeRate

    global cpu_usage, ram_usage, disk_usage, gpu_usage, gpu_temp
    cpu_usage = int(psutil.cpu_percent())
    gpu = get_gpu()
    gpu_usage = int(gpu.load * 100)
    gpu_temp = int(gpu.temperature)
    ram_usage = int(psutil.virtual_memory().percent)
    disk_usage = int(psutil.disk_usage('C:').percent)


def get_pc_data():
    global log
    battery = psutil.sensors_battery()
    global battery_perc, battery_plugged, battery_left
    battery_perc = battery.percent
    battery_plugged = battery.power_plugged
    if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft < 3600 * 10:
        battery_left = int(battery.secsleft / 60)

    global cpu_usage, ram_usage, disk_usage, gpu_usage, gpu_temp
    cpu_usage = int(psutil.cpu_percent())
    # gpu = get_gpu()
    # gpu_usage = int(gpu.load * 100)
    # gpu_temp = int(gpu.temperature)
    ram_usage = int(psutil.virtual_memory().percent)
    disk_usage = int(psutil.disk_usage('C:').percent)

    # global wifi
    # lines = list(filter(None, os.popen("netsh interface show interface").read().splitlines()))
    # wifi = not lines[-1].lower().__contains__("dis")
    # wifi = True

    global volume, volume_interface
    volume = get_volume()

    global brightness
    brightness = screen_brightness_control.get_brightness()[0]

    add_log( 'get_pc_data gotten!')
    # global is_locked
    # if (datetime.utcnow() - is_locked_last).total_seconds() > 12:
    #     is_locked = is_system_locked()


def set_volume(value):
    volume_interface.SetMasterVolumeLevel(int_to_db(value), None)


def get_volume():
    return db_to_int(volume_interface.GetMasterVolumeLevel())


def int_to_db(value):
    if value == 0:
        return -63.5
    return maxStomps(-63.5, math.log(value) * 13.7888 - 63.5)


def db_to_int(value):
    return int(math.pow(math.e, (0.9 * value + 63.5) / 13.7488) - 1.346)


def set_brightness(value):
    return screen_brightness_control.set_brightness(value=value)


def get_brightness():
    return screen_brightness_control.get_brightness()


def set_wifi(value):
    #     pyautogui win, "air", enter, [tabx2],enter,
    # last_word = "enabled" if value else "disabled"
    # command="netsh interface set interface \"" + "Wi-Fi" + "\" " + last_word
    #
    # process = subprocess.Popen(
    #     [
    #         'runas',
    #         '/user:Administrator',
    #         'cmd /C "'+command+'"'
    #     ],
    #     stdin=subprocess.PIPE
    # )
    # process.stdin.write(b'pass')
    # process.stdin.flush()
    pass


def set_bluetooth(value):
    # pyautogui win, "air", enter, [tabx2],enter,
    pass


def set_airplane(value):
    # pyautogui win, "air", enter, [tabx2],enter,
    pass


def set_night_light(value):
    # pyautogui
    pass


def check_sored_data_or_validate():
    global log
    path = userpaths.get_local_appdata() + '\MrPowerManager'
    if not os.path.exists(path):
        os.makedirs(path)

    if not Path(path + '\config.dat').is_file():
        exec(open("validate_code.py").read(),globals())
    else:
        f = open(path + '\config.dat', "r")
        values = f.readline().split("@@@")
        add_log( 'config.dat = ' + str(values))
        f.close()
        global token, pcName
        token = values[0]
        pcName = values[1]


# ================================================================================================================
# ================================================================================================================

def shutdown():
    stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='False')
    stomp_client.ws.send(stomp)
    return os.system("shutdown /s /t 1")


def restart():
    return os.system("shutdown /r /t 1")


def logout():
    return os.system("shutdown -l")


def suspend():
    stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='False')
    stomp_client.ws.send(stomp)
    priv_flags = (win32security.TOKEN_ADJUST_PRIVILEGES |
                  win32security.TOKEN_QUERY)
    hToken = win32security.OpenProcessToken(
        win32api.GetCurrentProcess(),
        priv_flags
    )
    priv_id = win32security.LookupPrivilegeValue(
        None,
        win32security.SE_SHUTDOWN_NAME
    )
    old_privs = win32security.AdjustTokenPrivileges(
        hToken,
        0,
        [(priv_id, win32security.SE_PRIVILEGE_ENABLED)]
    )
    win32api.SetSystemPowerState(True, True)


def hibernate():
    stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='False')
    stomp_client.ws.send(stomp)
    hibernate = True
    """Puts Windows to Suspend/Sleep/Standby or Hibernate.

    Parameters
    ----------
    hibernate: bool, default False
        If False (default), system will enter Suspend/Sleep/Standby state.
        If True, system will Hibernate, but only if Hibernate is enabled in the
        system settings. If it's not, system will Sleep.

    --------
    """
    # Enable the SeShutdown privilege (which must be present in your
    # token in the first place)
    priv_flags = (win32security.TOKEN_ADJUST_PRIVILEGES |
                  win32security.TOKEN_QUERY)
    hToken = win32security.OpenProcessToken(
        win32api.GetCurrentProcess(),
        priv_flags
    )
    priv_id = win32security.LookupPrivilegeValue(
        None,
        win32security.SE_SHUTDOWN_NAME
    )
    old_privs = win32security.AdjustTokenPrivileges(
        hToken,
        0,
        [(priv_id, win32security.SE_PRIVILEGE_ENABLED)]
    )

    if (win32api.GetPwrCapabilities()['HiberFilePresent'] == False and
            hibernate == True):
        import warnings
        warnings.warn("Hibernate isn't available. Suspending.")
    try:
        ctypes.windll.powrprof.SetSuspendState(not hibernate, True, False)
    except:
        # True=> Standby; False=> Hibernate
        win32api.SetSystemPowerState(not hibernate, True)

    # Restore previous privileges
    win32security.AdjustTokenPrivileges(
        hToken,
        0,
        old_privs
    )


# ================================================================================================================
# ================================================================================================================


def press_special_key(code):
    # codes: https://docs.microsoft.com/it-it/windows/win32/inputdev/virtual-key-codes?redirectedfrom=MSDN
    hwcode = win32api.MapVirtualKey(code, 0)
    win32api.keybd_event(code, hwcode)


def mute_key():
    press_special_key(0xAD)


def volume_down_key():
    press_special_key(0xAE)


def volume_up_key():
    press_special_key(0xAF)


def prev_trak_key():
    press_special_key(0xB1)


def next_trak_key():
    press_special_key(0xB0)


def play_pause_key():
    press_special_key(0xB3)


# ================================================================================================================
# ================================================================================================================


class Command:
    commands = []

    def __init__(self, command, id, value, scheduleDate):
        self.command = command
        self.id = id
        self.value = value
        self.is_scheduled = scheduleDate is not None
        self.scheduleDate = None
        if scheduleDate is not None:
            self.scheduleDate = datetime.strptime(scheduleDate, '%Y-%m-%d %H:%M:%S')


def request_password_encrypted(name):
    global log

    url = web + '/login'
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json'
    }
    params = {
        'token': token,
    }
    response = dict(requests.get(url, headers=headers, params=params).json())

    for pc in response['user']['pcList']:
        if pc['name'] == pcName:
            for login in pc['logins']:
                if login['title'] == name:
                    return login


def request_key():
    global log

    url = web + '/requestKey'
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json'
    }
    params = {
        'token': token,
        'pcName': pcName,
        'passwordType': 'WINDOWS',
    }
    response = dict(requests.get(url, headers=headers, params=params).json())
    return response['key']


def unlock_pc():
    # request_password_encrypted()
    # fernet=FernetCipher(str.encode(request_key()))
    # password=fernet.decrypt(encrypted_pass)
    pyautogui.FAILSAFE = False
    pyautogui.press("a")


def run_at(wait, command):
    add_log( "im waiting " + str(wait) + "secs")
    time.sleep(wait)
    execute_command(command)


def execute_command(command):
    global log

    #   TODO both date should be utc
    global last_streaming_start, last_webcam_start
    # log+=('\n'+datetime.now().strftime("%H-%M-%S")+' -> '+"command found! ---> " + command.command)
    if command.is_scheduled:
        secs = int((datetime.utcnow() - command.scheduleDate).total_seconds())
        add_log( " need to wait " + str(secs) + "sec")
        if secs > 60:
            return
        elif secs <= -60:
            add_log( secs)
            Thread(target=run_at, args=[abs(secs), command]).start()
            return

    if command.command == "SOUND_VALUE":
        add_log( command.value)
        set_volume(int(command.value))
    elif command.command == "BRIGHTNESS_VALUE":
        set_brightness(int(command.value))
    elif command.command.split('@@@')[0] == "BRIGHTNESS_DOWN":
        for i in range(0, int(command.command.split('@@@')[1])):
            set_brightness(max(0, get_brightness()[0] - 10))
            pyautogui.sleep(0.05)
    elif command.command.split('@@@')[0] == "BRIGHTNESS_UP":
        for i in range(0, int(command.command.split('@@@')[1])):
            set_brightness(min(100, get_brightness()[0] + 10))
            pyautogui.sleep(0.05)
    elif command.command == "SLEEP":
        stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='False')
        stomp_client.ws.send(stomp)
        add_log('/app/setOnline/  FALSE!')

        suspend()
    elif command.command == "HIBERNATE":
        stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='False')
        stomp_client.ws.send(stomp)
        add_log('/app/setOnline/  FALSE!')

        hibernate()
    elif command.command == "SHUTDOWN":
        stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='False')
        stomp_client.ws.send(stomp)
        add_log('/app/setOnline/  FALSE!')
        shutdown()
    elif command.command == "LOCK":
        # global is_locked, is_locked_last
        # is_locked = True
        # is_locked_last = datetime.utcnow()
        ctypes.windll.user32.LockWorkStation()
    elif command.command == "UNLOCK":
        unlock_pc()
    elif command.command == "WIFI_ON":
        set_wifi(True)
    elif command.command == "WIFI_OFF":
        set_wifi(False)
    elif command.command == "NO_SOUND":
        mute_key()
    elif command.command.split('@@@')[0] == "SOUND_DOWN":
        for i in range(0, int(command.command.split('@@@')[1])):
            volume_down_key()
            pyautogui.sleep(0.04)
    elif command.command.split('@@@')[0] == "SOUND_UP":
        for i in range(0, int(command.command.split('@@@')[1])):
            volume_up_key()
            pyautogui.sleep(0.04)
    elif command.command == "PLAY_PAUSE":
        play_pause_key()
    elif command.command.split('@@@')[0] == "TRACK_PREVIOUS":
        for i in range(0, int(command.command.split('@@@')[1])):
            prev_trak_key()
            pyautogui.sleep(0.04)
    elif command.command.split('@@@')[0] == "TRACK_NEXT":
        for i in range(0, int(command.command.split('@@@')[1])):
            next_trak_key()
            pyautogui.sleep(0.04)
    elif "COPY_PASSWORD" in command.command:
        login = request_password_encrypted(command.command.split('@@@@@@@@@@@@')[1])
        fernet = FernetCipher(str.encode(command.command.split('@@@@@@@@@@@@')[2]))
        pyperclip.copy(fernet.decrypt(login['password']))
    elif "PASTE_PASSWORD" in command.command:
        login = request_password_encrypted(command.command.split('@@@@@@@@@@@@')[1])
        fernet = FernetCipher(str.encode(command.command.split('@@@@@@@@@@@@')[2]))
        url = fernet.decrypt(login['url'])
        url = 'http://' + url if 'http' not in url[0:5] else url
        if (fernet.decrypt(login['username']) == ' '):
            webbrowser.open(url, new=2, autoraise=True)
            return

        pyautogui.hotkey('win', 'd')
        pyautogui.sleep(0.05)
        webbrowser.open(url, new=2, autoraise=True)
        pyautogui.sleep(3)
        keys = login['args'][1:-1].split(',')
        for key in keys:
            pyautogui.press(str(key).lower().strip())
            pyautogui.sleep(0.03)
            if (str(key).lower().strip() == 'enter'):
                pyautogui.sleep(2)

        keyboard.type(fernet.decrypt(login['username']))
        pyautogui.sleep(0.05)
        pyautogui.press('tab')
        keyboard.type(fernet.decrypt(login['password']))
        pyautogui.sleep(0.05)
        pyautogui.press('enter')

    elif "SHARE_CLIPBOARD" in command.command:
        global shareClipboard
        shareClipboard = str(command.command.split('@@@')[1]).lower() == 'true'

    elif "SEND_CLIPBOARD" in command.command:
        val = command.command.split('@@@')[1]
        if len(val) <= 1:
            return
        pyperclip.copy(val)

    elif "KEYBOARD" in command.command:
        to_hold = list(filter(None, command.command.split('@@@')[1].split(':')))
        add_log( 'to_hold=' + str(to_hold))

        if (len(to_hold) == 0):
            pyautogui.hotkey(command.command.split('@@@')[2])
        if (len(to_hold) == 1):
            pyautogui.hotkey(to_hold[0], command.command.split('@@@')[2])
        if (len(to_hold) == 2):
            pyautogui.hotkey(to_hold[0], to_hold[1], command.command.split('@@@')[2])
        if (len(to_hold) == 3):
            pyautogui.hotkey(to_hold[0], to_hold[1], to_hold[2], command.command.split('@@@')[2])
        # for key in to_hold:
        #     pyautogui.keyDown(key)
        #     pyautogui.sleep(0.01)
        # log+=('\n'+datetime.now().strftime("%H-%M-%S")+' -> '+'to_press=' + command.command.split('@@@')[2])
        # pyautogui.press()
        # for key in to_hold:
        #     pyautogui.keyUp(key)
    elif "SCREENSHOOT" in command.command:
        pyautogui.screenshot().save("screenshoot",
                                    "JPEG",
                                    optimize=True,
                                    quality=10)

    elif "STREAMING_START" in command.command:
        if (not streaming_thread.is_alive()):
            streaming_thread.start()
        last_streaming_start = datetime.now()
    elif "STREAMING_STOP" in command.command:
        last_streaming_start = datetime(2000, 1, 1)
    elif "STREAMING_SPEED" in command.command:
        global STREAMING_SPEED
        STREAMING_SPEED = 2 - 1.975 * 0.01 * float(command.command.split('@@@')[1])
    elif "STREAMING_QUALITY" in command.command:
        global STREAMING_QUALITY
        STREAMING_QUALITY = 10 + 70 * 0.01 * float(command.command.split('@@@')[1])
        add_log( 'quality=' + str(STREAMING_QUALITY))

    elif "RECORD_SECONDS" in command.command:
        args = command.command.split('@@@')
        Thread(target=record_screen, args=args[1:]).start()

    elif "WEBCAM_START" in command.command:
        if not webcam_thread.is_alive():
            webcam_thread.start()
        last_webcam_start = datetime.now()
    elif "WEBCAM_STOP" in command.command:
        last_webcam_start = datetime(2000, 1, 1)
    elif "WEBCAM_SPEED" in command.command:
        global WEBCAM_SPEED
        WEBCAM_SPEED = 0.5 - 0.480 * 0.01 * float(command.command.split('@@@')[1])
    elif "WEBCAM_QUALITY" in command.command:
        global WEBCAM_QUALITY
        WEBCAM_QUALITY = 3 + 70 * 0.01 * float(command.command.split('@@@')[1])
    elif "SPEECH_TO_TEXT" in command.command:
        keyboard.type(command.command.split('@@@')[1])

    elif "LEFT_CLICK" in command.command:
        w, h = pyautogui.size()
        x = float(command.command.split('@@@')[1])
        y = float(command.command.split('@@@')[2])

        pyautogui.moveTo(x * w, y * h, duration=0.16)
        pyautogui.leftClick()
    elif "RIGHT_CLICK" in command.command:
        w, h = pyautogui.size()
        x = float(command.command.split('@@@')[1])
        y = float(command.command.split('@@@')[2])

        pyautogui.moveTo(x * w, y * h, duration=0.0)
        pyautogui.rightClick()
    elif "DOUBLE_CLICK" in command.command:
        w, h = pyautogui.size()
        x = float(command.command.split('@@@')[1])
        y = float(command.command.split('@@@')[2])

        pyautogui.moveTo(x * w, y * h, duration=0.1)
        pyautogui.doubleClick()
    elif "TASK_MANAGER" in command.command:
        data = get_open_windows_and_icons()
        send_base64(data, 'TASK_MANAGER')
    elif "WINDOW_KILL" in command.command:
        for window in open_windows:
            if window._get_window_text() == command.command.split('@@@')[1]:
                window.close()
    elif "WINDOW_FOCUS" in command.command:
        add_log( "TASK_MANAGER_FOCUS")
        for window in open_windows:
            if window._get_window_text() == command.command.split('@@@')[1]:
                window.set_focus()


def execute_commands():
    for command in commands:
        if abs((datetime.utcnow() - command.scheduleDate).total_seconds()) < 5:
            execute_command(command)
        request_end_command(command.id)


def request_end_command(id):
    url = web + '/endCommand'
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json'
    }
    params = {
        'token': token,
        'pcName': pcName,
        'id': id,
    }
    requests.post(url, headers=headers, params=params)


def get_list_commands():
    while True:
        add_log( "Polling STARTED...")
        polling2.poll(
            lambda: (datetime.now() - last_client_online).seconds > 40 or
                    request_available_commands().status_code == 200,
            step=REQUEST_AVAILABLE_COMMANDS,
            ignore_exceptions=(requests.exceptions.ConnectionError,),
            poll_forever=True)

        if (datetime.now() - last_client_online).seconds > 40:
            add_log( "Polling STOPPED... client offline!")
            global thread_get_commands_online
            thread_get_commands_online = False
            return
        else:
            add_log( "Polling STOPPED... found commands!")
            response_dict = dict(available_commands_response.json())
            if 'pc not found' in response_dict['result']:
                add_log( "pc does not exit")
                path = userpaths.get_local_appdata() + '\MrPowerManager'
                os.remove(path + '\config.dat')
                global force_exit
                force_exit = True
                exit()

            global commands
            commands = []
            for command in response_dict['commands']:
                commands.append(
                    Command(command['command'], command['id'], command['commandValue'],
                            command['commandScheduledDate']))

        execute_commands()


def request_available_commands():
    url = web + '/availableCommands'
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json'
    }
    params = {
        'token': token,
        'pcName': pcName,
    }
    global available_commands_response
    available_commands_response = requests.get(url, headers=headers, params=params)
    return available_commands_response


def start_thread_get_list_commands():
    global thread_get_commands_online
    thread_get_commands_online = True

    try:
        Thread(target=get_list_commands).start()
    except:
        start_thread_get_list_commands()


async def main():
    global log
    # event_schedule.enter(1, 1, update_status)
    # event_schedule.run()
    try:
        task1 = asyncio.create_task(update_status())

        # start_thread_get_list_commands()

        await task1
    except Exception as e:
        add_log( 'errore 2 catturato! '+ str(e))
        main()
        raise e


# ===========================================================================================
def is_system_locked():
    user32 = ctypes.windll.User32
    if user32.GetForegroundWindow() % 10 == 0:
        return True
    else:
        return False


def get_gpu(index=0):
    gpus=GPUtil.getGPUs()
    return gpus[index]


# ===========================================================================================
# ===========================================================================================

def initialize_and_go():
    global log,stomp_client
    check_sored_data_or_validate()
    stomp_client=StompClient(token,pcName,None)

    global volume, volume_interface
    start = time.time_ns()
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
    add_log( 'volume_interface set, took = ' + str(
        (time.time_ns() - start) / 1000000) + ' ms')
    add_log( ', its sound value is = ' + str(
        volume_interface.GetMasterVolumeLevel))

    # global wifi_interface
    # lines = list(filter(None, os.popen("netsh interface show interface").read().splitlines()))
    # wifi_interface = (lines[-1].split(" ")[-1])
    # add_log( 'wifi_interface = ' + wifi_interface)

    asyncio.run(main())
    # if not admin.isUserAdmin():
    #     admin.runAsAdmin()


def print_battery_status():
    batts1 = c.CIM_Battery(Caption='Portable Battery')
    for i, b in enumerate(batts1):
        add_log( 'Battery %d Design Capacity: %d mWh' % (
        i, b.DesignCapacity or 0))

    batts = t.ExecQuery('Select * from BatteryFullChargedCapacity')
    for i, b in enumerate(batts):
        add_log( 'Battery %d Fully Charged Capacity: %d mWh' %
                (i, b.FullChargedCapacity))

    batts = t.ExecQuery('Select * from BatteryStatus where Voltage > 0')
    for i, b in enumerate(batts):
        add_log( '\nBattery %d ***************' % i)
        add_log( 'Tag:               ' + str(b.Tag))
        add_log( 'Name:              ' + b.InstanceName)
        add_log( 'PowerOnline:       ' + str(b.PowerOnline))
        add_log( 'Discharging:       ' + str(b.Discharging))
        add_log( 'Charging:          ' + str(b.Charging))
        add_log( 'Voltage:           ' + str(b.Voltage))
        add_log( 'DischargeRate:     ' + str(b.DischargeRate))
        add_log( 'ChargeRate:        ' + str(b.ChargeRate))
        add_log( 'RemainingCapacity: ' + str(b.RemainingCapacity))
        add_log( 'Active:            ' + str(b.Active))
        add_log( 'Critical:          ' + str(b.Critical))


file_to_send_path = ''

var = ''
var_button = 'SendFile'
pb = ''
value_label = ''
force_block = False


def update_progress_label():
    v = 0
    if (len(file_to_send_path) > 1 and (time.time_ns() - send_start) > 100000000):
        size = os.path.getsize(filename=file_to_send_path) / 1024
        current = size * pb['value'] / 100
        time_s = (time.time_ns() - send_start) / 1000000000.0
        v = current / time_s
    return f"{pb['value']}% {round(v, 0)} kB/s" if pb['value'] > 0 else ""


def progress(val):
    if pb['value'] < 100:
        pb['value'] = val
        value_label['text'] = update_progress_label()
    # else:
    #     showinfo(message='The progress completed!')
    #     pb['value'] = 0


def on_exit(icon, item):
    if str(item) == 'Exit':
        stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='False')
        stomp_client.ws.send(stomp)
        global force_exit
        force_exit = True
        # sys.exit(1)
        os._exit(1)
    elif str(item) == 'Send file to phone [file selector]':
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename()
        if file_path == '':
            return

        # limit 500MB
        if os.path.getsize(filename=file_path) > 512000000:
            return

        with open(file_path, "rb") as file:
            base64_file = base64.b64encode(file.read()).decode("utf-8")
            send_base64(base64_file, 'FILE_FROM_SERVER:' + file_path.split('/')[-1], wait=0.015)
    elif str(item) == 'Send file to phone [drag&drop]':

        def drop(event):
            global file_to_send_path, var
            # log+=('\n'+datetime.now().strftime("%H-%M-%S")+' -> '+event.data)
            # files = str(event.data)[0:-1].split('} ')

            final_files = []
            final_file = ''

            in_bracket = False
            for letter in event.data:
                if (letter != '{'):
                    if letter == '}':
                        in_bracket = False
                        final_files.append(final_file)
                        final_file = ''
                    else:
                        if letter == ' ' and not in_bracket:
                            if len(final_file) > 1:
                                final_files.append(final_file)
                            final_file = ''
                        else:
                            final_file += letter
                else:
                    in_bracket = True
            if len(final_file) > 1:
                final_files.append(final_file)

            # log+=('\n'+datetime.now().strftime("%H-%M-%S")+' -> '+str(final_files))

            # file_to_send_path = str(files[-1])[1:]
            # formatted=''
            # for file in files:
            # formatted = str(files[-1])[1:].split('/')[-1]
            file_to_send_path = final_files[-1]
            formatted = final_files[-1].split('/')[-1]
            var.set(formatted)

        def send():
            global file_to_send_path, var_button, force_block
            if file_to_send_path != '':
                if pb['value'] > 0.01:
                    if pb['value'] != 100:
                        force_block = True
                    value_label['text'] = ''
                    var_button.set('SendFile')
                    pb['value'] = 0
                    return
                var_button.set('Stop')
                # limit 500MB
                if os.path.getsize(filename=file_to_send_path) > 512000000:
                    return
                force_block = False
                with open(file_to_send_path, "rb") as file:
                    base64_file = base64.b64encode(file.read()).decode("utf-8")

                    # string = '1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111'
                    # msg = ''
                    # for i in range(240000):
                    #     msg += string

                    Thread(target=send_base64,
                           args=[base64_file, 'FILE_FROM_SERVER:' +
                                 file_to_send_path.split('/')[-1], True, 0.012]).start()

        ws = tkdnd.Tk()
        ws.title('Drag&Drop file')
        ws.geometry('500x360')
        ws.config(bg='#fcba03')

        global var, var_button
        var = tk.StringVar()
        var_button = tk.StringVar(value='SendFile')
        tk.Label(ws, text='Path of the Folder', bg='#fcba03', font=font.Font(family='Helvetica'), ).pack(anchor=tk.NW,
                                                                                                         padx=10)
        e_box = tk.Entry(ws, textvar=var, width=80, font=font.Font(family='Helvetica', size=15))
        e_box.pack(fill=X, padx=10)
        e_box.drop_target_register(tkdnd.DND_FILES)
        e_box.dnd_bind('<<Drop>>', drop)

        lframe = tk.LabelFrame(ws, text='Instructions', bg='#fcba03', font=font.Font(family='Helvetica'))
        label = tk.Label(
            lframe,
            bg='#fcba03',
            font=font.Font(family='Helvetica', size=13),
            text='Drag and drop here \nthe files of your choice.'

        )
        label.drop_target_register(tkdnd.DND_FILES)
        label.dnd_bind('<<Drop>>', drop)
        label.pack(fill=tk.BOTH, expand=True)
        lframe.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # progressbar
        s = Style()
        s.theme_use('clam')
        s.configure("my.Horizontal.TProgressbar", background='#fcba03')

        global pb
        pb = Progressbar(
            ws,
            orient='horizontal',
            mode='determinate',
            length=370,
            value=0,
            style="my.Horizontal.TProgressbar",
        )
        # place the progressbar
        pb.pack(padx=10, pady=20)

        # label
        global value_label
        value_label = tk.Label(
            ws,
            text=update_progress_label(),
            font=font.Font(family='Helvetica', size=14),
            bg='#fcba03'
        )
        value_label.pack()

        button = tk.Button(ws, textvariable=var_button, bg='#0176AB', activebackground='#fcba03',
                           fg='#ffffff', font=font.Font(family='Helvetica', size=15), command=send)

        button.pack(pady=10)

        ws.mainloop()
    elif str(item) == 'Log':
        path = userpaths.get_local_appdata() + '\MrPowerManager\\logs\\'
        if not os.path.exists(path):
            os.makedirs(path)
        path += 'log ' + datetime.now().strftime("%Y-%m-%d %H-%M-%S") + '.txt'
        with open(path, 'w') as write:
            global log
            write.write(log)

        webbrowser.open(path)
    elif str(item) =='Restart socket':
        stomp_client.ws.close()
        t = Thread(target=stomp_client.create_connection)
        t.daemon = True
        t.start()
    elif str(item)=='Brightness + 10':
        set_brightness(min(100, get_brightness()[0] + 10))
    elif str(item)=='Brightness - 10':
        set_brightness(max(0, get_brightness()[0] - 10))
    elif str(item)=='Brightness MAX':
        set_brightness(100)
    elif str(item)=='Brightness MIN':
        set_brightness(0)


def start_tray():
    # icon_folder = os.path.join(sys._MEIPASS, 'icon')
    # icon_path=icon_folder + "\icon.ico"
    pystray.Icon(
        'MrPowerManagerServer',
        Image.open("icon.ico"),
        menu=pystray.Menu(
            pystray.MenuItem(
                'Log', on_exit
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                'Send file to phone [file selector]', on_exit
            ),
            pystray.MenuItem(
                'Send file to phone [drag&drop]', on_exit
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                'Restart socket', on_exit
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                'Brightness + 10', on_exit
            ),
            pystray.MenuItem(
                'Brightness - 10', on_exit
            ),
            pystray.MenuItem(
                'Brightness MAX', on_exit
            ),
            pystray.MenuItem(
                'Brightness MIN', on_exit
            ),
            pystray.Menu.SEPARATOR,

            pystray.MenuItem(
                'Exit', on_exit
            ),
        )
    ).run()


if __name__ == '__main__':
    log += (datetime.now().strftime("%H-%M-%S") + ' -> ' + 'starting tray thread...')
    Thread(target=start_tray).start()
    add_log( 'tray thread started')

    c=requests.get(web+ '/', headers={}, params={})

    initialize_and_go()

    # win32gui.EnumWindows(winEnumHandler, None)

# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 44100
# CHUNK = 4096
#
# # p=pyaudio.PyAudio()
# # stream = p.open(format=FORMAT,
# #                     channels=CHANNELS,
# #                     rate=RATE,
# #                     input=True,
# #                     frames_per_buffer=CHUNK)
# process2 = (
#     ffmpeg
#         .input('pipe:')
#         .output('out.aac', vcodec='libfdk_aac', crf='5')
#         .overwrite_output()
#         .run_async(pipe_stdin=True)
# )
# # frames=[]
# # for i in range(0, int(RATE/CHUNK*3)):
# #     process2.stdin.write(
# #         b''.join(data)
# #     )
# #     data=stream.read(CHUNK)
# #     frames.append(data)
#
# with open('output.wav') as f:
#     process2.stdin.write(f.
#     )

# stream.stop_stream()
# stream.close()
# p.terminate()


# wf=wave.open("output.wav",'wb')
# wf.setnchannels(CHANNELS)
# wf.setsampwidth(p.get_sample_size(FORMAT))
# wf.setframerate(RATE)
# wf.writeframes(b''.join(frames))
# wf.close()

# cam = VideoCapture(0)
# webcam_to_base64()


# except Exception as e:
#     log+=('\n'+datetime.now().strftime("%H-%M-%S")+' -> '+"errore catturato! ", e)

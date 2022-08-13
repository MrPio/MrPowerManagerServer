import asyncio
import base64
import ctypes
import json
import math
import os
import queue
import re
import sched
import time
from asyncio import sleep
from ctypes import cast, POINTER
from datetime import datetime
from pathlib import Path
from threading import Thread

import cv2
import ffmpeg
import numpy as np
import polling2
import psutil
import pyautogui
import pyperclip
import requests
import screen_brightness_control
import stomper
import userpaths
import websocket
import win32api
import win32security
import wmi
from GPUtil import GPUtil
from comtypes import CLSCTX_ALL
from cv2 import VideoCapture, imshow, waitKey, destroyWindow
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

from dropbox_api import list_files
from PIL import Image

# ===========================================================================================
# ===========================================================================================

# ws_uri = "ws://localhost:5000/chat/websocket"
from fernet import FernetCipher

ws_uri = "ws://mrpowermanager.herokuapp.com/chat/websocket"


class StompClient(object):
    NOTIFICATIONS = None
    KEEP_ALIVE = True
    IS_RUNNING = False
    DESTINATIONS = []

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
        print("The websocket connection is open.")
        StompClient.IS_RUNNING = True

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

        if self.ws is None:
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
        if len(unpacked_msg['body']) > 1:
            command = dict(json.loads(unpacked_msg['body']))
            print(str(command))
            if 'command' in command.keys():
                command = Command(
                    command['command'], int(command['id']), int(command['commandValue']),
                    command['commandScheduledDate'])
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


# ===========================================================================================
# ===========================================================================================


UPDATE_STATUS = 1
CLIENT_OFFLINE = 3
STREAMING_SPEED = 0.5
WEBCAM_SPEED = 0.5
STREAMING_QUALITY = 15
WEBCAM_QUALITY = 30
STREAMING_TIMEOUT = 12
BYTES_LIMIT = 14000
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
is_locked = False
is_locked_last = datetime(2000, month=1, day=1)
encrypted_pass = ''
last_client_online = datetime(2000, 1, 1)
last_streaming_start = datetime(2000, 1, 1)
last_webcam_start = datetime(2000, 1, 1)
wattage_entries = []
thread_get_commands_online = True

c = wmi.WMI()
t = wmi.WMI(moniker="//./root/wmi")

force_exit = False

volume_interface = None
win_ver = 11

event_schedule = sched.scheduler(time.time, time.sleep)

stomp_client = StompClient(None)
# websocket_sender = websocket.create_connection(ws_uri)

collect_wattage_in_background = True
client_online = False

base64Screen = ''
base64Webcam=''
cam = ''


async def work_offline():
    print('work_offline() start')
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
        print('wattage_entries--->', len(wattage_entries))

        if len(wattage_entries) > 1:
            print('upload_wattage_entries')
            Thread(target=upload_wattage_entries).start()

        await asyncio.sleep(240)

        if not collect_wattage_in_background or force_exit:
            return


def is_client_online():
    global last_client_online, client_online
    while True:
        if force_exit:
            return

        if list_files("/database/clients").__contains__(token + ".user"):
            if not client_online:
                print('client è andato ONLINE!')
            client_online = True
            last_client_online = datetime.now()
            time.sleep(12)
        else:
            if client_online:
                print('client è andato offline!')
            client_online = False
            time.sleep(3)


def start_up_commands():
    if request_available_commands().status_code == 200:
        print("found commands!")
        response_dict = dict(available_commands_response.json())
        if 'pc not found' in response_dict['result']:
            print("pc does not exit")
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
    global base64Screen
    path = userpaths.get_local_appdata() + '\MrPowerManager\screen'
    pyautogui.screenshot().save(path,
                                "JPEG",
                                optimize=True,
                                quality=int(STREAMING_QUALITY))
    with open(path, "rb") as image_file:
        base64Screen = base64.b64encode(image_file.read()).decode("utf-8")


def webcam_to_base64():
    global base64Webcam
    result, image = cam.read()
    if result:
        path = userpaths.get_local_appdata() + '\MrPowerManager\webcam'
        Image.fromarray(image).save(path,
                                    "JPEG",
                                    optimize=True,
                                    quality=int(WEBCAM_QUALITY))
        with open(path, "rb") as image_file:
            base64Webcam = base64.b64encode(image_file.read()).decode("utf-8")
    else:
        base64Webcam=''


def record_screen(fps='30', duration='5', quality='25', h265='True'):
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

def send_base64(data,header):
    max = int(len(data) / BYTES_LIMIT)
    for i in range(max + 1):
        if len(data) > BYTES_LIMIT:
            msg = header+'@@@' + str(i) + '@@@' + str(max) + '@@@' + data[:BYTES_LIMIT]
        else:
            msg = header+'@@@' + str(i) + '@@@' + str(max) + '@@@' + data

        if len(list(data)) > BYTES_LIMIT:
            data = data[BYTES_LIMIT:]
        stomp = stomper.send(dest="/app/sendMessage/" + token + "/" + pcName, msg=msg)
        stomp_client.ws.send(stomp)

def streaming():
    global base64Screen
    print('STREAMING started...')
    screen_to_base64()
    while True:
        if (datetime.now() - last_streaming_start).seconds > STREAMING_TIMEOUT:
            print('STREAMING stopped...')
            time.sleep(2)
        else:
            Thread(target=screen_to_base64).start()
            send_base64(base64Screen,'STREAMING')

        time.sleep(STREAMING_SPEED)

def webcam():
    global base64Webcam,cam
    print('WEBCAM started...')
    if type(cam)==str and cam=='':
        cam = VideoCapture(0)
    webcam_to_base64()
    while True:
        if (datetime.now() - last_webcam_start).seconds > STREAMING_TIMEOUT:
            print('WEBCAM stopped...')
            time.sleep(2)
        else:
            Thread(target=webcam_to_base64).start()
            send_base64(base64Webcam,'WEBCAM')

        time.sleep(WEBCAM_SPEED)


check_client_online_thread = Thread(target=is_client_online)
streaming_thread = Thread(target=streaming)
webcam_thread = Thread(target=webcam)


async def update_status():
    asyncio.create_task(work_offline())

    print('avvio check_client_online_thread()...')
    start_up_commands()
    check_client_online_thread.start()
    print('avvio update_status()...')
    while True:
        if force_exit:
            return

        if not client_online:
            if stomp_client.ws is not None and StompClient.IS_RUNNING:
                stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='False')
                stomp_client.ws.send(stomp)

                StompClient.KEEP_ALIVE = False
                stomp_client.ws.close()

            await sleep(CLIENT_OFFLINE)

        else:
            StompClient.KEEP_ALIVE = True
            if not StompClient.IS_RUNNING:
                try:
                    Thread(target=stomp_client.create_connection).start()
                    c = 0
                    while not StompClient.IS_RUNNING:
                        await sleep(0.5)
                        c += 1
                        if c > 32:
                            raise 'timeout nella connessione del socket!'


                except Exception as e:
                    print('errore 3 catturato! ', e)

            stomp = stomper.send(dest="/app/setOnline/" + token + "/" + pcName, msg='True')
            stomp_client.ws.send(stomp)

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
                   False, False, is_locked, volume, brightness, battery_perc
                , battery_left, cpu_usage, ram_usage, 50, disk_usage
                , gpu_usage, gpu_temp, battery_charge_rate, battery_discharge_rate]
            stomp = stomper.send(dest="/app/updatePcStatus/" + token + "/" + pcName,
                                 msg=''.join(str(x) + "~" for x in msg)[0:-1])
            stomp_client.ws.send(stomp)
            # print("pcStatus sent through Socket!")

            # params = {
            #     'token': token,
            #     'pcName': pcName,
            # }

            # response = requests.post(url, headers=headers, params=params, data=json.dumps(data))
            # print(response.content)


def upload_wattage_entries():
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
    print(response.content)


def get_wattage_data():
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
    battery = psutil.sensors_battery()
    global battery_perc, battery_plugged, battery_left
    battery_perc = battery.percent
    battery_plugged = battery.power_plugged
    if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft < 3600 * 10:
        battery_left = int(battery.secsleft / 60)

    global cpu_usage, ram_usage, disk_usage, gpu_usage, gpu_temp
    cpu_usage = int(psutil.cpu_percent())
    gpu = get_gpu()
    gpu_usage = int(gpu.load * 100)
    gpu_temp = int(gpu.temperature)
    ram_usage = int(psutil.virtual_memory().percent)
    disk_usage = int(psutil.disk_usage('C:').percent)

    global wifi
    lines = list(filter(None, os.popen("netsh interface show interface").read().splitlines()))
    wifi = not lines[-1].lower().__contains__("dis")
    wifi = True

    global volume
    volume = get_volume()

    global brightness
    brightness = screen_brightness_control.get_brightness()[0]

    global is_locked
    if (datetime.utcnow() - is_locked_last).total_seconds() > 12:
        is_locked = is_system_locked()


def set_volume(value):
    volume_interface.SetMasterVolumeLevel(int_to_db(value), None)


def get_volume():
    return db_to_int(volume_interface.GetMasterVolumeLevel())


def int_to_db(value):
    if value == 0:
        return -63.5
    return max(-63.5, math.log(value) * 13.7888 - 63.5)


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
    path = userpaths.get_local_appdata() + '\MrPowerManager'
    if not os.path.exists(path):
        os.makedirs(path)

    if not Path(path + '\config.dat').is_file():
        exec(open("validate_code.py").read())
    else:
        f = open(path + '\config.dat', "r")
        values = f.readline().split("!@@#")
        f.close()
        global token, pcName
        token = values[0]
        pcName = values[1]


# ================================================================================================================
# ================================================================================================================

def shutdown():
    return os.system("shutdown /s /t 1")


def restart():
    return os.system("shutdown /r /t 1")


def logout():
    return os.system("shutdown -l")


def suspend():
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
    url = web + '/login'
    headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json'
    }
    params = {
        'token': token,
    }
    response = dict(requests.get(url, headers=headers, params=params).json())
    global encrypted_pass
    for pc in response['user']['pcList']:
        if pc['name'] == pcName:
            encrypted_pass = pc['passwords'][name]


def request_key():
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
    print("im waiting " + str(wait) + "secs")
    time.sleep(wait)
    execute_command(command)


def execute_command(command):
    #   TODO both date should be utc
    global last_streaming_start,last_webcam_start
    # print("command found! ---> " + command.command)
    if command.is_scheduled:
        secs = int((datetime.utcnow() - command.scheduleDate).total_seconds())
        print(" need to wait " + str(secs) + "sec")
        if secs > 60:
            return
        elif secs <= -60:
            print(secs)
            Thread(target=run_at, args=[abs(secs), command]).start()
            return

    if command.command == "SOUND_VALUE":
        print(command.value)
        set_volume(int(command.value))
    elif command.command == "BRIGHTNESS_VALUE":
        set_brightness(int(command.value))
    elif command.command == "BRIGHTNESS_DOWN":
        set_brightness(max(0, get_brightness()[0] - 10))
    elif command.command == "BRIGHTNESS_UP":
        set_brightness(min(100, get_brightness()[0] + 10))
    elif command.command == "SLEEP":
        suspend()
    elif command.command == "HIBERNATE":
        hibernate()
    elif command.command == "SHUTDOWN":
        shutdown()
    elif command.command == "LOCK":
        global is_locked, is_locked_last
        is_locked = True
        is_locked_last = datetime.utcnow()
        ctypes.windll.user32.LockWorkStation()
    elif command.command == "UNLOCK":
        unlock_pc()
    elif command.command == "WIFI_ON":
        set_wifi(True)
    elif command.command == "WIFI_OFF":
        set_wifi(False)
    elif command.command == "NO_SOUND":
        mute_key()
    elif command.command == "SOUND_DOWN":
        volume_down_key()
    elif command.command == "SOUND_UP":
        volume_up_key()
    elif command.command == "PLAY_PAUSE":
        play_pause_key()
    elif command.command == "TRACK_PREVIOUS":
        prev_trak_key()
    elif command.command == "TRACK_NEXT":
        next_trak_key()
    elif "COPY_PASSWORD" in command.command:
        request_password_encrypted(command.command.split('@@@@@@@@@@@@')[1])
        fernet = FernetCipher(str.encode(command.command.split('@@@@@@@@@@@@')[2]))
        pyperclip.copy(fernet.decrypt(encrypted_pass))
    elif "PASTE_PASSWORD" in command.command:
        request_password_encrypted(command.command.split('@@@@@@@@@@@@')[1])
        fernet = FernetCipher(str.encode(command.command.split('@@@@@@@@@@@@')[2]))
        pyautogui.write(fernet.decrypt(encrypted_pass))
    elif "SHARE_CLIPBOARD" in command.command:
        val = command.command.split('@@@@@@@@@@@@')[1]
        if val != 'null':
            pyperclip.copy(val)
    elif "KEYBOARD" in command.command:
        to_hold = list(filter(None, command.command.split('@@@')[1].split(':')))
        print('to_hold=' + str(to_hold))

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
        # print('to_press=' + command.command.split('@@@')[2])
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
        STREAMING_SPEED = 2 - 1.70 * 0.01 * float(command.command.split('@@@')[1])
    elif "STREAMING_QUALITY" in command.command:
        global STREAMING_QUALITY
        STREAMING_QUALITY = 10 + 70 * 0.01 * float(command.command.split('@@@')[1])
        print('quality=' + str(STREAMING_QUALITY))

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
        WEBCAM_SPEED = 1.0 - 0.97 * 0.01 * float(command.command.split('@@@')[1])
    elif "WEBCAM_QUALITY" in command.command:
        global WEBCAM_QUALITY
        WEBCAM_QUALITY = 3 + 70 * 0.01 * float(command.command.split('@@@')[1])

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
        print("Polling STARTED...")
        polling2.poll(
            lambda: (datetime.now() - last_client_online).seconds > 40 or
                    request_available_commands().status_code == 200,
            step=REQUEST_AVAILABLE_COMMANDS,
            ignore_exceptions=(requests.exceptions.ConnectionError,),
            poll_forever=True)

        if (datetime.now() - last_client_online).seconds > 40:
            print("Polling STOPPED... client offline!")
            global thread_get_commands_online
            thread_get_commands_online = False
            return
        else:
            print("Polling STOPPED... found commands!")
            response_dict = dict(available_commands_response.json())
            if 'pc not found' in response_dict['result']:
                print("pc does not exit")
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
    # event_schedule.enter(1, 1, update_status)
    # event_schedule.run()
    try:
        task1 = asyncio.create_task(update_status())

        # start_thread_get_list_commands()

        await task1
    except Exception as e:
        print('errore 2 catturato! ', e)
        raise e


# ===========================================================================================
def is_system_locked():
    user32 = ctypes.windll.User32
    if user32.GetForegroundWindow() % 10 == 0:
        return True
    else:
        return False


def get_gpu(index=0):
    return GPUtil.getGPUs()[index]


# ===========================================================================================
# ===========================================================================================

def initialize_and_go():
    check_sored_data_or_validate()

    StompClient.DESTINATIONS = [
        "/server/" + re.sub('[^a-zA-Z0-9 \n.]', '_', token) + "/" + re.sub('[^a-zA-Z0-9 \n.]', '_',
                                                                           pcName) + "/commands"
    ]

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    global volume_interface, wifi_interface
    volume_interface = cast(interface, POINTER(IAudioEndpointVolume))

    lines = list(filter(None, os.popen("netsh interface show interface").read().splitlines()))
    wifi_interface = (lines[-1].split(" ")[-1])

    asyncio.run(main())
    # if not admin.isUserAdmin():
    #     admin.runAsAdmin()


def print_battery_status():
    batts1 = c.CIM_Battery(Caption='Portable Battery')
    for i, b in enumerate(batts1):
        print('Battery %d Design Capacity: %d mWh' % (i, b.DesignCapacity or 0))

    batts = t.ExecQuery('Select * from BatteryFullChargedCapacity')
    for i, b in enumerate(batts):
        print('Battery %d Fully Charged Capacity: %d mWh' %
              (i, b.FullChargedCapacity))

    batts = t.ExecQuery('Select * from BatteryStatus where Voltage > 0')
    for i, b in enumerate(batts):
        print('\nBattery %d ***************' % i)
        print('Tag:               ' + str(b.Tag))
        print('Name:              ' + b.InstanceName)
        print('PowerOnline:       ' + str(b.PowerOnline))
        print('Discharging:       ' + str(b.Discharging))
        print('Charging:          ' + str(b.Charging))
        print('Voltage:           ' + str(b.Voltage))
        print('DischargeRate:     ' + str(b.DischargeRate))
        print('ChargeRate:        ' + str(b.ChargeRate))
        print('RemainingCapacity: ' + str(b.RemainingCapacity))
        print('Active:            ' + str(b.Active))
        print('Critical:          ' + str(b.Critical))


if __name__ == '__main__':
    initialize_and_go()

    # cam = VideoCapture(0)
    # webcam_to_base64()


# except Exception as e:
#     print("errore catturato! ", e)

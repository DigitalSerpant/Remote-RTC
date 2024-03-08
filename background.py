import asyncio
import websockets
import ctypes
from ctypes import wintypes
import json
import pyautogui
import pydirectinput
import hashlib

pydirectinput.FAILSAFE = False
USER32 = ctypes.windll.user32
pyautogui.FAILSAFE = False
with open("password.txt", 'r') as file:
    existing_content = file.read()
PASSWORD = existing_content
VK_LWIN = 0x5B  # left Windows key
VK_RWIN = 0x5C  # right Windows key
KEYEVENTF_KEYDOWN = 0x0
KEYEVENTF_KEYUP = 0x2
MOUSEEVENTF_MOVE = 0x0001

# C struct redefinitions
class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("mi", MouseInput)]

# Functions for mouse movement
def moveRel(xOffset=None, yOffset=None, relative=True):
    if not relative:
        x, y = position()
        if xOffset is None:
            xOffset = 0
        if yOffset is None:
            yOffset = 0
        moveTo(x + xOffset, y + yOffset)
    else:
        extra = ctypes.c_ulong(0)
        ii_ = Input(mi=MouseInput(dx=xOffset, dy=yOffset, mouseData=0, dwFlags=MOUSEEVENTF_MOVE, time=0, dwExtraInfo=ctypes.pointer(extra)))
        ctypes.windll.user32.SendInput(1, ctypes.pointer(ii_), ctypes.sizeof(ii_))

def encrypt_string(input_string):
    sha256 = hashlib.sha256()
    sha256.update(input_string.encode('utf-8'))
    encrypted_string = sha256.hexdigest()
    return encrypted_string

def position():
    point = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y

def moveTo(x, y):
    current_x, current_y = position()
    moveRel(x - current_x, y - current_y, relative=True)

async def handle_websocket(websocket, path):
    try:
        password_attempt = await websocket.recv()  # Receive the password from the client
        if encrypt_string(password_attempt) == PASSWORD:
            print("Password accepted. Connection established.")
            async for message in websocket:
                try:
                    data = json.loads(message)
                    endpoint = data.get('endpoint', '')

                    if endpoint == '/mouse_cursor':
                        x, y = map(float, data['message'].split(','))
                        await move_cursor(x, y)
                    elif endpoint == '/mouse_down':
                        button = data.get('button', '')
                        await mouse_down(button)
                    elif endpoint == '/mouse_up':
                        button = data.get('button', '')
                        await mouse_up(button)
                    elif endpoint == '/key_event':
                        key_info = data.get('keyInfo', {})
                        await handle_key_event(key_info)
                    elif endpoint == '/mouse_scroll':
                        lines = data.get('lines', 0)
                        await mouse_scroll(lines)

                except ValueError:
                    print("Invalid message format")
        else:
            print("Incorrect password. Closing connection.    " + password_attempt)
            await websocket.close()
    except websockets.ConnectionClosedError:
        pass
    except Exception as e:
        print(f"An error occurred: {str(e)}")

async def move_cursor(x, y):
    try:
        moveRel(int(x), int(y), relative=True)
    except Exception as e:
        print(f"Error moving cursor: {str(e)}")

async def mouse_down(button):
    try:
        
        x, y = get_cursor_position()
        input_struct = Input(
            type=0,  # INPUT_MOUSE
            mi=MouseInput(
                dx=x,
                dy=y,
                mouseData=0,
                dwFlags=0x0002 if button.lower() == 'left' else 0x0008,  # MOUSEEVENTF_LEFTDOWN or MOUSEEVENTF_RIGHTDOWN
                time=0,
                dwExtraInfo=None
            )
        )
        ctypes.windll.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))

    except Exception as e:
        print(f"Error simulating mouse down: {str(e)}")


async def mouse_up(button):
    try:
        x, y = get_cursor_position()

        input_struct = Input(
            type=0,  # INPUT_MOUSE
            mi=MouseInput(
                dx=x,
                dy=y,
                mouseData=0,
                dwFlags=0x0004 if button.lower() == 'left' else 0x0010,  # MOUSEEVENTF_LEFTUP or MOUSEEVENTF_RIGHTUP
                time=0,
                dwExtraInfo=None
            )
        )
        ctypes.windll.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))

    except Exception as e:
        print(f"Error simulating mouse up: {str(e)}")

async def handle_key_event(key_info):
    try:
        key = key_info.get('key', '')
        event = key_info.get('event', '')

        key = key.replace("Arrow", "")

        if event == 'down':
            if key == 'Control':
                pydirectinput.keyDown('ctrl')
            else:
                pydirectinput.keyDown(key.lower())

        elif event == 'up':
            if key == 'Control':
                pydirectinput.keyUp('ctrl')
            else:
                pydirectinput.keyUp(key.lower())
    except Exception as e:
        print(f"Error handling key event: {str(e)}")

async def mouse_scroll(lines):
    try:
        pyautogui.scroll(lines * -7)
    except Exception as e:
        print(f"Error simulating mouse scroll: {str(e)}")

def get_cursor_position():
    point = wintypes.POINT()
    USER32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y

def set_cursor_position(x, y):
    USER32.SetCursorPos(x, y)

async def main(port):
    try:
        server = await websockets.serve(handle_websocket, "0.0.0.0", port)

        print(f"WebSocket server is running. Listening on ws://0.0.0.0:{port}")

        await server.wait_closed()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"An error occurred: {str(e)}")

port = 6969
asyncio.run(main(port))
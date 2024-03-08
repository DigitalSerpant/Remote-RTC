import asyncio
import json
import logging
import os
import subprocess
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCRtpSender
from aiortc.contrib.media import MediaStreamTrack
from av import VideoFrame
import pyautogui
import cv2
from fractions import Fraction
import ctypes
import time
import dxcam 
import hashlib
import getpass

os.environ['DXGIDebug'] = '1'
ROOT = os.path.dirname(__file__)

class POINT(ctypes.Structure):
    _fields_ = [('x', ctypes.c_int),
                ('y', ctypes.c_int)]

class CURSORINFO(ctypes.Structure):
    _fields_ = [('cbSize', ctypes.c_uint),
                ('flags', ctypes.c_uint),
                ('hCursor', ctypes.c_void_p),
                ('ptScreenPos', POINT)]

GetCursorInfo = ctypes.windll.user32.GetCursorInfo
GetCursorInfo.argtypes = [ctypes.POINTER(CURSORINFO)]

def force_codec(pc, sender, forced_codec):
    kind = forced_codec.split("/")[0]
    codecs = RTCRtpSender.getCapabilities(kind).codecs
    transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
    transceiver.setCodecPreferences(
        [codec for codec in codecs if codec.mimeType == forced_codec]
    )

def encrypt_string(input_string):
    sha256 = hashlib.sha256()
    sha256.update(input_string.encode('utf-8'))
    encrypted_string = sha256.hexdigest()
    return encrypted_string 

def save_to_file(encrypted_string, filename='password.txt'):
    with open(filename, 'w') as file:
        file.write(encrypted_string)

def is_cursor_hidden():
    info = CURSORINFO()
    info.cbSize = ctypes.sizeof(info)

    if GetCursorInfo(ctypes.byref(info)):
        return not bool(info.flags & 0x00000001) 
    else:
        return False
    
def getsecurity():
    global passwordtext  
    filename = 'password.txt'
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            existing_content = file.read()
            passwordtext = existing_content
        print(f"{filename} already exists. The encrypted password is:\n{existing_content}")
    else:
        user_input = getpass.getpass("Enter your password: ")
        checkpass = getpass.getpass("Please re-enter your password: ")
        if user_input == checkpass:
            encrypted_string = encrypt_string(user_input)
            save_to_file(encrypted_string)
            passwordtext = encrypted_string
            print(f"Password encrypted and saved to '{filename}':\n{encrypted_string}")
            
        else:
            print("The two passwords do not match. Please try again.")
            getsecurity()
getsecurity()

class DxCamTrack(MediaStreamTrack):
    kind = "video"

    camera = None

    def __init__(self):
        super().__init__()
        self.start_time = time.time()
        self.frame_rate = 61
        self.framedex = 90000
        self.previous_state = None

        if DxCamTrack.camera is None:
            DxCamTrack.camera = dxcam.create(output_idx=0, output_color="BGR")
            DxCamTrack.camera.start(target_fps=self.frame_rate, video_mode=True)
            print("Created a new DXCamera instance.")

    async def recv(self):
        try:
            img = DxCamTrack.camera.get_latest_frame()

            cursor_position = pyautogui.position()
            cursor_hidden = is_cursor_hidden()
            if cursor_hidden != self.previous_state:
                if not cursor_hidden:
                    cv2.circle(img, cursor_position, 7, (0, 0, 255), -1)

            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            frame = VideoFrame.from_ndarray(img, format="rgb24")
            elapsed_time = time.time() - self.start_time
            frame_index = int(elapsed_time * self.frame_rate)
            frame.pts = frame_index * int(self.framedex / self.frame_rate)  # Calculate RTP timestamp
            frame.time_base = Fraction(1, self.framedex)

            return frame
        except Exception as e:
            self.camera.stop()
            print(f"Error receiving frame: {str(e)}")

async def index(request):
    content = open(os.path.join(ROOT, "templates/index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)

async def offer(request):
    params = await request.json()
    password = params.get("password")
    
    if passwordtext != encrypt_string(password):
        return web.Response(status=401, text="Unauthorized")

    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    
    pc = RTCPeerConnection()
    pcs.add(pc)

    screenshot_track = DxCamTrack()
    pc.addTrack(screenshot_track)

    video_sender = pc.getSenders()[0]
    force_codec(pc, video_sender, "video/VP8")

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

pcs = set()

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

if __name__ == "__main__":
    file_path = "background.exe"
    if os.path.exists(file_path):
        subprocess.Popen([file_path])
    else:
        subprocess.Popen(["python", "background.py"])
    logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_post("/offer", offer)
    web.run_app(app, host="0.0.0.0", port=6966)

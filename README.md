
# Remote RTC

**Currently Being rewritten in C#**

Remote RTC is a low latency remote desktop application that runs on your computer and hosts it to your local network that can run on any modern browser. Remote RTC can be used to host a personal Geforce Now or Parsec. Capeable of sustating stable 60 fps on a good network connection. Tested & works best on 1920x1080

This is mostly a proof of concept.

## Build
To build Remote RTC, make sure you have [Pyinstaller](https://pyinstaller.org/en/stable/) before running 'build.bat'. To install the required libraries besides Pyinstaller, use the commands:
```bat
  pip install -r requirements.txt
```
or if that fails use: 

```bat
  pip install aiohttp aiortc av numpy pyautogui opencv-python pydirectinput dxcam websockets
```
 After completion, the compiled files main.exe and background.exe should be placed in the same directory before running main.exe. It's recommended to put 'modded libraries/vpx.py' into the codecs folder of aiortc for 60 fps rather than 30 fps. However, this will require a more demanding internet connection.


## Deployment

To run the Remote RTC first download it [here](https://github.com/DigitalSerpant/Remote-RTC/releases/download/1.0.1/Remote.RTC.1.0.1.zip). Next, simply put the two exe files in the same directory and run the main.exe and create a secure password.  If Windows asks you to allow it you your local network click Allow. To use Remote RTC, after running the main.exe go to http://localhost:6966 as the default address. If you would like to port forward this to the open internet, in the HTML change the PublicIP to your public IP like the following:

```javascript
  let PublicIP = "12.34.56.78";
```
You need to foward two ports for Remote RTC. The default ports 6966 and 6969. 6966 is the webRTC and main website while 6969 is the websocket port. I will note that you monitor must remain on unless it supports acting like its on then the monitor is off. A ways to check this is to simply turn you monitor off while watching the screen and if it stops streaming your monitor does not support being off. I do plan to add a virtual monitor driver in the future.

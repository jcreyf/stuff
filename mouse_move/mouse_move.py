# Adding a Python implementation:
#  https://pypi.org/project/PyAutoGUI/
import pyautogui as pag
import random
import time

# Move the mouse cursor 10 pixels to the right every 60 seconds and then immediately
# move back to where the cursor was.
while True:
    x, y = pag.position()
    pag.moveTo(x+10, y, duration=0.2)
    pag.moveTo(x, y)
    time.sleep(60)
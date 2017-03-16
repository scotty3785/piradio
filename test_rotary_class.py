#!/usr/bin/env python
#
# Raspberry Pi Rotary Test Encoder Class
# $Id: test_rotary_class.py,v 1.6 2016/06/29 09:43:33 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses standard rotary encoder with push switch
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#

import sys
import time
import atexit
import traceback

from rotary_class import RotaryEncoder
from test_lcd_textstar import TextStar

stderr = sys.stderr.write;

# Switch definitions
#Volume Knob
LEFT_SWITCH = 19
RIGHT_SWITCH = 13
MUTE_SWITCH = 26 

#Menu Knob
UP_SWITCH = 17
DOWN_SWITCH = 18
MENU_SWITCH = 4
DOWN_SWITCH_IF_DAC = 10



# Try to trap any exit errors 
def exit_fn():
    if not traceback.format_exc().startswith('None'):
        s=traceback.format_exc()
    sys.exit(0)

# Register
atexit.register(exit_fn)

# This is the callback routine to handle volume events
def volume_event(event):
    display_event("Volume", event)
    return

# This is the callback routine to handle tuner events
def tuner_event(event):
    display_event("Tuner", event)
    return

def display_event(name,event):
    show_lcd(name,event)
    if event == RotaryEncoder.CLOCKWISE:
        print name + " clockwise", RotaryEncoder.CLOCKWISE
    elif event == RotaryEncoder.ANTICLOCKWISE:
        print name + " anticlockwise", RotaryEncoder.ANTICLOCKWISE
    elif event == RotaryEncoder.BUTTONDOWN:
        print name + " button down", RotaryEncoder.BUTTONDOWN
    elif event == RotaryEncoder.BUTTONUP:
        print name + " button up", RotaryEncoder.BUTTONUP
    return
    
def show_lcd(name,event):
    ts.ClearScreen()
    if event == RotaryEncoder.CLOCKWISE:
        ts.write( name + " clockwise")
    elif event == RotaryEncoder.ANTICLOCKWISE:
        ts.write( name + " anticlockwise")
    elif event == RotaryEncoder.BUTTONDOWN:
        ts.write( name + " button down")
    elif event == RotaryEncoder.BUTTONUP:
        ts.write( name + " button up")

# Allow user to select board revision
revision = 2
#stderr("Are you using an old revision 1 board y/n: ")
#answer = raw_input("")
#if answer == 'y':
#   revision = 1

# If using a HiFiBerry DAC+ use GPIO 10 (Pin 19) 
down_switch = DOWN_SWITCH
#stderr("Are you using a HiFiBerry DAC+ y/n: ")
#answer = raw_input("")
#if answer == 'y':
#   down_switch = DOWN_SWITCH_IF_DAC

volumeknob = RotaryEncoder(LEFT_SWITCH,RIGHT_SWITCH,MUTE_SWITCH,volume_event,revision)
tunerknob = RotaryEncoder(UP_SWITCH,down_switch,MENU_SWITCH,tuner_event,revision)

print "Use Ctl-C to exit"

ts = TextStar('/dev/serial0',115200)
ts.ClearScreen()

while True:
    try:
        time.sleep(0.1)
    except KeyboardInterrupt:
        print "\nExit"
        sys.exit(0)

# End of test rotary encoders



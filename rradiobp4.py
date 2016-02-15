#!/usr/bin/env python
#
# Raspberry Pi Internet Radio
# using an HD44780 LCD display
# Rotary encoder version 4 x 20 character I2C LCD interface
#
# $Id: rradiobp4.py,v 1.15 2016/01/31 15:59:16 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
# 
# This program uses  Music Player Daemon 'mpd'and it's client 'mpc' 
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import os
import RPi.GPIO as GPIO
import signal
import subprocess
import sys
import time
import string
import datetime 
from time import strftime
import shutil
import atexit
import traceback

# Class imports
from radio_daemon import Daemon
from radio_class import Radio
from lcd_i2c_class import lcd_i2c
from lcd_i2c_pcf8475 import lcd_i2c_pcf8475
from log_class import Log
from rss_class import Rss
from rotary_class import RotaryEncoder

# Switch definitions
# Volume rotary encoder
LEFT_SWITCH = 14
RIGHT_SWITCH = 15
MUTE_SWITCH = 4
# Tuner rotary encoder
UP_SWITCH = 17
# DOWN_SWITCH = 18 # No longer used
MENU_SWITCH = 25

# To use GPIO 14 and 15 (Serial RX/TX)
# Remove references to /dev/ttyAMA0 from /boot/cmdline.txt and /etc/inittab 

UP = 0
DOWN = 1

CurrentStationFile = "/var/lib/radiod/current_station"
CurrentTrackFile = "/var/lib/radiod/current_track"
CurrentFile = CurrentStationFile
PlaylistsDirectory = "/var/lib/mpd/playlists/"

log = Log()
radio = Radio()
rss = Rss()
lcd = None

# Signal SIGTERM handler
def signalHandler(signal,frame):
	global lcd
	global log
	radio.execCommand("umount /media > /dev/null 2>&1")
	radio.execCommand("umount /share > /dev/null 2>&1")
	pid = os.getpid()
	log.message("Radio stopped, PID " + str(pid), log.INFO)
	lcd.line1("Radio stopped")
	lcd.line2("")
	lcd.line3("")
	lcd.line4("")
	GPIO.cleanup()
	sys.exit(0)

# Daemon class
class MyDaemon(Daemon):
	def run(self):
		global lcd
		global CurrentFile
		global volumeknob,tunerknob
		log.init('radio')

		# Setup signal handlers
		signal.signal(signal.SIGTERM,signalHandler)

		progcall = str(sys.argv)
		log.message('Radio running pid ' + str(os.getpid()), log.INFO)
		log.message("Radio " +  progcall + " daemon version " + radio.getVersion(), log.INFO)
		log.message("GPIO version " + str(GPIO.VERSION), log.INFO)

		# Load pcf8475 i2c class or Adafruit backpack
		if radio.getBackPackType() == radio.PCF8475:
			log.message("PCF8475 backpack", log.INFO)
			lcd = lcd_i2c_pcf8475()
		else:
			log.message("Adafruit backpack", log.INFO)
			lcd = lcd_i2c()


		boardrevision = radio.getBoardRevision()
		lcd.init(boardrevision)
		lcd.backlight(True)
		lcd.setWidth(20)
		lcd.line1("Radio version " + radio.getVersion())
		time.sleep(0.5)

		ipaddr = exec_cmd('hostname -I')
		myos = exec_cmd('uname -a')
		hostname = exec_cmd('hostname -s')
		log.message(myos, log.INFO)

		# Display daemon pid on the LCD
		message = "Radio pid " + str(os.getpid())
		lcd.line2(message)

		lcd.line3("Starting MPD")
		log.message("GPIO version " + str(GPIO.VERSION), log.INFO)
		lcd.line4("IP " + ipaddr)
		radio.start()
		log.message("MPD started", log.INFO)
		time.sleep(0.5)

		mpd_version = radio.execMpcCommand("version")
		log.message(mpd_version, log.INFO)
		lcd.line3(mpd_version)
		lcd.line4("GPIO version " + str(GPIO.VERSION))
		time.sleep(2.0)
		 	
		reload(lcd,radio)
		radio.play(get_stored_id(CurrentFile))
		log.message("Current ID = " + str(radio.getCurrentID()), log.INFO)
		lcd.line3("Radio Station " + str(radio.getCurrentID()))

                # Define rotary switches
                down_switch = radio.getSwitchGpio("down_switch")
                log.message("Down switch = " + str(down_switch), log.DEBUG)

		volumeknob = RotaryEncoder(LEFT_SWITCH,RIGHT_SWITCH,MUTE_SWITCH,volume_event,boardrevision)
		tunerknob = RotaryEncoder(UP_SWITCH,down_switch,MENU_SWITCH,tuner_event,boardrevision)
		log.message("Running" , log.INFO)

		# Main processing loop
		count = 0 
		toggleScrolling = True  # Toggle scrolling between Line 2 and 3
		while True:

			# See if we have had an interrupt
			switch = radio.getSwitch()
			if switch > 0:
				get_switch_states(lcd,radio,rss,volumeknob,tunerknob)

			display_mode = radio.getDisplayMode()
			
			lcd.setScrollSpeed(0.3) # Scroll speed normal
			dateFormat = radio.getDateFormat()
			todaysdate = strftime(dateFormat)

			ipaddr = exec_cmd('hostname -I')

			# Shutdown command issued
			if display_mode == radio.MODE_SHUTDOWN:
				log.message("Shutting down", log.DEBUG)
				displayShutdown(lcd)
				while True:
					time.sleep(1)

			if ipaddr is "":
				lcd.line3("No IP network")

			elif display_mode == radio.MODE_TIME:

				if radio.getReload():
					log.message("Reload ", log.DEBUG)
					reload(lcd,radio)
					radio.setReload(False)

				msg = todaysdate
				if radio.getStreaming():
					msg = msg + ' *'  
				lcd.line1(msg)
				display_current(lcd,radio,toggleScrolling)

			elif display_mode == radio.MODE_SEARCH:
				display_search(lcd,radio)

			elif display_mode == radio.MODE_SOURCE:
				display_source_select(lcd,radio)

			elif display_mode == radio.MODE_OPTIONS:
				display_options(lcd,radio)

			elif display_mode == radio.MODE_IP:
				displayInfo(lcd,ipaddr,mpd_version)

			elif display_mode == radio.MODE_RSS:
				lcd.line1(todaysdate)
				input_source = radio.getSource()
				current_id = radio.getCurrentID()
				if input_source == radio.RADIO:
					station = radio.getRadioStation() + ' (' + str(current_id) + ')'
					lcd.line2(station)
				else:
					lcd.line2("Current track:" + str(current_id))
				display_rss(lcd,rss)

			elif display_mode == radio.MODE_SLEEP:
				lcd.line1(todaysdate)
				display_sleep(lcd,radio)

			# Timer function
			checkTimer(radio)

			# Check state (pause or play)
			checkState(radio)

			# Alarm wakeup function
			if display_mode == radio.MODE_SLEEP and radio.alarmFired():
				log.message("Alarm fired", log.INFO)
				radio.unmute()
				displayWakeUpMessage(lcd)
				radio.setDisplayMode(radio.MODE_TIME)

			# Toggle line 2 & 3 scrolling
			if toggleScrolling:
				toggleScrolling = False
			else:
				toggleScrolling = True

			time.sleep(0.1)
			# End of main processing loop

	def status(self):
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if not pid:
			message = "radiod status: not running"
	    		log.message(message, log.INFO)
			print message 
		else:
			message = "radiod running pid " + str(pid)
	    		log.message(message, log.INFO)
			print message 
		return

# End of class overrides

def interrupt():
	global lcd
	global radio
	global volumeknob
	global tunerknob
	global rss
	interrupt = False
	switch = radio.getSwitch()
	if switch > 0:
		interrupt = get_switch_states(lcd,radio,rss,volumeknob,tunerknob)
		radio.setSwitch(0)

	# Rapid display of track play status
	if  radio.getSource() == radio.PLAYER:
		if radio.volumeChanged():
			displayLine4(lcd,radio,"Volume " + str(radio.getVolume()))
			time.sleep(0.5)
		else:
			lcd.line4(radio.getProgress())

	elif (radio.getTimer() and not interrupt) or radio.volumeChanged():
		displayLine4(lcd,radio,"Volume " + str(radio.getVolume()))
		interrupt = checkTimer(radio)

	if not interrupt:
		interrupt = checkState(radio) or radio.getInterrupt()

	return interrupt

def no_interrupt():
	return False

# Call back routine for the volume control knob
def volume_event(event):
	global radio
	global volumeknob
	switch = 0
	ButtonNotPressed = volumeknob.getSwitchState(MUTE_SWITCH)

	# Suppress events if volume button pressed
	if ButtonNotPressed:
		radio.incrementEvent()
		if event == RotaryEncoder.CLOCKWISE:
			switch = RIGHT_SWITCH
		elif event == RotaryEncoder.ANTICLOCKWISE:
			switch = LEFT_SWITCH

	if event ==  RotaryEncoder.BUTTONDOWN:
		switch = MUTE_SWITCH

	radio.setSwitch(switch)
	return

# Call back routine for the tuner control knob
def tuner_event(event):
	global radio
	global tunerknob
	switch = 0
	ButtonNotPressed = tunerknob.getSwitchState(MENU_SWITCH)

	# Suppress events if volume button pressed
	if ButtonNotPressed:
		radio.incrementEvent()
		if event == RotaryEncoder.CLOCKWISE:
			switch = UP_SWITCH
		elif event == RotaryEncoder.ANTICLOCKWISE:
			switch = radio.getSwitchGpio("down_switch")

	if event ==  RotaryEncoder.BUTTONDOWN:
		switch = MENU_SWITCH

	radio.setSwitch(switch)
	return


# Check switch states
def get_switch_states(lcd,radio,rss,volumeknob,tunerknob):
	interrupt = False       # Interrupt display
	switch = radio.getSwitch()
	pid = exec_cmd("cat /var/run/radiod.pid")
	display_mode = radio.getDisplayMode()
	input_source = radio.getSource()
	events = radio.getEvents()
	option = radio.getOption()
	down_switch = radio.getSwitchGpio("down_switch")

	log.message("Events=" + str(events), log.DEBUG)

	if switch == MENU_SWITCH:
		log.message("MENU switch mode=" + str(display_mode), log.DEBUG)

		if radio.muted():
			unmuteRadio(lcd,radio)
		
		display_mode = display_mode + 1

		# Skip RSS mode if not available
		if display_mode == radio.MODE_RSS:
			if rss.isAvailable() and not radio.optionChanged():
				lcd.line3("Getting RSS feed")
			else:
				display_mode = display_mode + 1

		if display_mode > radio.MODE_LAST:
			display_mode = radio.MODE_TIME

		radio.setDisplayMode(display_mode)
		log.message("New mode " + radio.getDisplayModeString()+
					"(" + str(display_mode) + ")", log.DEBUG)

		# Shutdown if menu button held for > 3 seconds
		MenuSwitch = tunerknob.getSwitchState(MENU_SWITCH)
		log.message("switch state=" + str(MenuSwitch), log.DEBUG)
		count = 15
		while MenuSwitch == 0:
			time.sleep(0.2)
			MenuSwitch = tunerknob.getSwitchState(MENU_SWITCH)
			count = count - 1
			if count < 0:
				log.message("Shutdown", log.DEBUG)
				MenuSwitch = 1
				radio.setDisplayMode(radio.MODE_SHUTDOWN)

		if radio.getUpdateLibrary():
			update_library(lcd,radio)	
			radio.setDisplayMode(radio.MODE_TIME)

		elif radio.getReload(): 
			source = radio.getSource()
			log.message("Reload " + str(source), log.INFO)
			lcd.line2("Reloading ")
			reload(lcd,radio)
			radio.setReload(False)
			radio.setDisplayMode(radio.MODE_TIME)

		elif radio.optionChanged():
			log.message("optionChanged", log.DEBUG)
			if radio.alarmActive() and not radio.getTimer() \
					and (option == radio.ALARMSETHOURS or option == radio.ALARMSETMINS):
				radio.setDisplayMode(radio.MODE_SLEEP)
				radio.mute()
			else:
				radio.setDisplayMode(radio.MODE_TIME)

			radio.optionChangedFalse()

		elif radio.loadNew():
			log.message("Load new  search=" + str(radio.getSearchIndex()), log.DEBUG)
			radio.playNew(radio.getSearchIndex())
			radio.setDisplayMode(radio.MODE_TIME)

		time.sleep(0.2)
		interrupt = True

	elif switch == UP_SWITCH:
		log.message("UP switch display_mode " + str(display_mode), log.DEBUG)

		if  display_mode != radio.MODE_SLEEP:
			if radio.muted():
				unmuteRadio(lcd,radio)

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)

			elif display_mode == radio.MODE_SEARCH:
				radio.getNext(UP)

			elif display_mode == radio.MODE_OPTIONS:
				cycle_options(radio,UP)

			else:
				radio.channelUp()

			interrupt = True
		else:
			DisplayExitMessage(lcd)

	elif switch == down_switch:
		log.message("DOWN switch display_mode " + str(display_mode), log.DEBUG)
		if  display_mode != radio.MODE_SLEEP:
			if radio.muted():
				unmuteRadio(lcd,radio)

			if display_mode == radio.MODE_SOURCE:
				radio.toggleSource()
				radio.setReload(True)

			elif display_mode == radio.MODE_SEARCH:
				radio.getNext(DOWN)

			elif display_mode == radio.MODE_OPTIONS:
				cycle_options(radio,DOWN)

			else:
				radio.channelDown()
			interrupt = True
		else:
			DisplayExitMessage(lcd)

	elif switch == LEFT_SWITCH:
		log.message("LEFT switch" ,log.DEBUG)

		if display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				toggle_option(radio,lcd,DOWN)
				interrupt = True

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				radio.findNextArtist(DOWN)
				interrupt = True

			else:
				# Set the volume by the number of rotary encoder events
				if events > 1:
					volAdjust = events/2
				else:
					volAdjust = events

				if radio.muted():
					radio.unmute()
				volume = radio.getVolume()

				while volAdjust > 0 and volume != 0:
					volume -= 1
					if volume <  0:
						volume = 0
					radio.setVolume(volume)
					displayLine4(lcd,radio,"Volume " + str(volume))
					volAdjust -= 1

		else:
			DisplayExitMessage(lcd)

	elif switch == RIGHT_SWITCH:
		log.message("RIGHT switch" ,log.DEBUG)

		if display_mode != radio.MODE_SLEEP:
			if display_mode == radio.MODE_OPTIONS:
				toggle_option(radio,lcd,UP)
				interrupt = True

			elif display_mode == radio.MODE_SEARCH and input_source == radio.PLAYER:
				radio.findNextArtist(UP)
				interrupt = True
			else:
				# Set the volume by the number of rotary encoder events
				if events > 1:
					volAdjust = events/2
				else:
					volAdjust = events
				if radio.muted():
					radio.unmute()
				volume = radio.getVolume()
				range = radio.getVolumeRange()

				while volAdjust > 0:
					volume += 1
					if volume >  range:
						volume = range
					radio.setVolume(volume)
					displayLine4(lcd,radio,"Volume " + str(volume))
					volAdjust -= 1

	elif switch == MUTE_SWITCH:
		log.message("MUTE switch" ,log.DEBUG)

		if display_mode != radio.MODE_SLEEP:
			if radio.muted():
				radio.unmute()
				radio.setDisplayMode(radio.MODE_TIME)
			else:
				radio.mute()
				displayLine4(lcd,radio,"Sound muted")
			interrupt = True
		else:
			DisplayExitMessage(lcd)

	# Reset all rotary encoder events to zero and clear switch
	radio.resetEvents()
	radio.setSwitch(0)
	return interrupt

# Sleep exit message
def DisplayExitMessage(lcd):
	lcd.line3("Press menu button to")
	lcd.line4("exit sleep mode")
	time.sleep(1)
	lcd.line3("")
	lcd.line4("")
	return

# Cycle through the options
# Only display reload the library if in PLAYER mode
def cycle_options(radio,direction):
	log.message("cycle_options " + str(direction) , log.DEBUG) 

	option = radio.getOption()

	if direction == UP:
		option += 1
	else:
		option -= 1

	# Don;t display reload if not player mode
	source = radio.getSource()
	if option == radio.RELOADLIB:
		if source != radio.PLAYER:
			if direction == UP:
				option = option+1
			else:
				option = option-1

	if option == radio.STREAMING:
		if not radio.streamingAvailable():
			if direction == UP:
				option = option+1
			else:
				option = option-1

	if option > radio.OPTION_LAST:
		option = radio.RANDOM
	elif option < 0:
		if source == radio.PLAYER:
			option = radio.OPTION_LAST
		else:
			option = radio.OPTION_LAST-1

	radio.setOption(option)
	radio.optionChangedTrue()
	return


# Toggle random mode (Certain options not allowed if RADIO)
def toggle_option(radio,lcd,direction):
	option = radio.getOption() 
	log.message("toggle_option option="+ str(option), log.DEBUG)
	events = radio.getEvents()

	if option == radio.RANDOM:
		if radio.getRandom():
			radio.randomOff()
		else:
			radio.randomOn()

	elif option == radio.CONSUME:
		if radio.getSource() == radio.PLAYER:
			if radio.getConsume():
				radio.consumeOff()
			else:
				radio.consumeOn()
		else:
			lcd.line2("Not allowed")
			time.sleep(2)

	elif option == radio.REPEAT:
		if radio.getRepeat():
			radio.repeatOff()
		else:
			radio.repeatOn()

	elif option == radio.TIMER:
		if radio.getTimer():
			if direction == UP:
				radio.incrementTimer(events/2)
				lcd.line2("Timer " + radio.getTimerString())
			else:
				radio.decrementTimer(events/2)
				lcd.line2("Timer " + radio.getTimerString())
		else:
			radio.timerOn()

	elif option == radio.ALARM:
		radio.alarmCycle(direction)

	elif option == radio.ALARMSETHOURS or option == radio.ALARMSETMINS:
		value = 1
		if option == radio.ALARMSETHOURS:
			value = 60
		if direction == UP:
			radio.incrementAlarm(value)
		else:
			radio.decrementAlarm(value)

	elif option == radio.STREAMING:
		radio.toggleStreaming()

	elif option == radio.RELOADLIB:
		if radio.getUpdateLibrary():
			radio.setUpdateLibOff()
		else:
			radio.setUpdateLibOn()

	radio.optionChangedTrue()
	return

# Update music library
def update_library(lcd,radio):
	log.message("Updating library", log.INFO)
	lcd.line1("Updating library")
	lcd.line2("Please wait")
	radio.updateLibrary()
	return

# Reload if new source selected (RADIO or PLAYER)
def reload(lcd,radio):
	lcd.line1("Loading:")

	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line2("Radio Stations")
		dirList=os.listdir(PlaylistsDirectory)
		for fname in dirList:
			if os.path.isfile(fname):
				continue
			log.message("Loading " + fname, log.DEBUG)
			lcd.line2(fname)
			time.sleep(0.1)
		radio.loadStations()

	elif source == radio.PLAYER:
		lcd.line2("Media library")
		radio.loadMedia()
		current = radio.execMpcCommand("current")
		if len(current) < 1:
			update_library(lcd,radio)
	return

# Display the RSS feed
def display_rss(lcd,rss):
	rss_line = rss.getFeed()
	lcd.setScrollSpeed(0.2) # Scroll RSS a bit faster
	lcd.scroll3(rss_line,interrupt)
	return

# Display the currently playing station or track
def display_current(lcd,radio,toggleScrolling):
	station = radio.getRadioStation()
	current_id = radio.getCurrentID()
	title = radio.getCurrentTitle()

	if len(title) < 1:
		bitrate = radio.getBitRate()
		if bitrate > 0:
			title = "Station " + str(current_id) + ' ' + str(bitrate) +'k'

	source = radio.getSource()

	# Display progress of the currently playing track
	if radio.muted():
		displayLine4(lcd,radio,"Sound muted")
	else:
		if source == radio.PLAYER:
			lcd.line4(radio.getProgress())
		else:
			displayLine4(lcd,radio,"Volume " + str(radio.getVolume()))

	if source == radio.RADIO:
		if current_id <= 0:
			lcd.line2("No stations found")
		else:
			if toggleScrolling:
				lcd.line3(title)
				lcd.scroll2(station, interrupt)
			else:
				lcd.line2(station)
	else:
		index = radio.getSearchIndex()
		playlist = radio.getPlayList()
		current_artist = radio.getCurrentArtist()
		lcd.line2(current_artist)

	# Display stream error
	if radio.gotError():
		errorStr = radio.getErrorString()
		lcd.scroll3(errorStr,interrupt)
		radio.clearError()
	else:
		leng = len(title)
		if leng > 20:
			if toggleScrolling:
				lcd.line3(title)
			else:
				lcd.scroll3(title[0:160],interrupt)
		else:
			lcd.line3(title)

	return


# Display the currently playing station or track
def display_currentXXXX(lcd,radio,toggleScrolling):
	station = radio.getRadioStation()
	title = radio.getCurrentTitle()
	if len(title) < 1:
		title = "--------------------"
	current_id = radio.getCurrentID()
	source = radio.getSource()

	if source == radio.RADIO:
		if current_id <= 0:
			lcd.line2("No stations found")
		else:
			station = station + ' (' + str(current_id) + ')'
			if toggleScrolling:
				lcd.line3(title)
				lcd.scroll2(station, interrupt)
			else:
				lcd.line2(station)
	else:
		index = radio.getSearchIndex()
		playlist = radio.getPlayList()
		current_artist = radio.getCurrentArtist()
		lcd.line2(current_artist)

	# Display stream error
	if radio.gotError():
		errorStr = radio.getErrorString()
		lcd.scroll3(errorStr,interrupt)
		radio.clearError()
	else:
		leng = len(title)
		if leng > 20:
			if toggleScrolling:
				lcd.line3(title)
			else:
				lcd.scroll3(title[0:160],interrupt)
		else:
			lcd.line3(title)

	# Display progress of the currently playing track
	if radio.muted():
		displayLine4(lcd,radio,"Sound muted")
	else:
		if source == radio.PLAYER:
			lcd.line4(radio.getProgress())
		else:
			displayLine4(lcd,radio,"Volume " + str(radio.getStoredVolume()))

	return

# Display if in sleep
def display_sleep(lcd,radio):
	message = 'Sleep mode'
	lcd.line2('')
	lcd.line3('')
	if radio.alarmActive():
		message = "Alarm " + radio.getAlarmTime()
	lcd.line4(message)

# Get the last ID stored in /var/lib/radiod
def get_stored_id(current_file):
	current_id = 5
	if os.path.isfile(current_file):
		current_id = int(exec_cmd("cat " + current_file) )
	return current_id

# Execute system command
def exec_cmd(cmd):
	p = os.popen(cmd)
	result = p.readline().rstrip('\n')
	return result

# Get list of tracks or stations
def get_mpc_list(cmd):
	list = []
	line = ""
	p = os.popen("/usr/bin/mpc " + cmd)
	while True:
		line =  p.readline().strip('\n')
		if line.__len__() < 1:
			break
		list.append(line)

	return list

# Source selection display
def display_source_select(lcd,radio):

	lcd.line1("Input Source:")
	source = radio.getSource()
	if source == radio.RADIO:
		lcd.line2("Internet Radio")
	elif source == radio.PLAYER:
		lcd.line2("Music library")
	progress = radio.getProgress()

	if radio.muted():
		lcd.line4('Sound muted')
	else:
		# Is the radio actually playing ?
		if progress.find('/0:00') > 0:
			lcd.line4("Volume " + str(radio.getVolume()))
		else:
			lcd.line4(radio.getProgress())

	return

# Display search (Station or Track)
def display_search(lcd,radio):
	index = radio.getSearchIndex()
	source = radio.getSource()
	current_id = radio.getCurrentID()
	lcd.line1("Search:" + str(index + 1))

	if source == radio.PLAYER:
		current_artist = radio.getArtistName(index)
		# Speed searches up by not scrolling
		if radio.getEvents() == 0:
			lcd.scroll2(current_artist[0:160],interrupt) 
			lcd.scroll3(radio.getTrackNameByIndex(index),interrupt) 
		else:
			lcd.line2(current_artist) 
			lcd.line3(radio.getTrackNameByIndex(index)) 
		lcd.line4(radio.getProgress())
	else:
		current_station = radio.getStationName(index)
		lcd.line3("Current station:" + str(radio.getCurrentID()))
		
		# Speed searches up by not scrolling
		if radio.getEvents() == 0:
			lcd.scroll2(current_station[0:160],interrupt) 
		else:
			lcd.line2(current_station) 
	return


def unmuteRadio(lcd,radio):
	radio.unmute()
	volume = radio.getVolume()
	lcd.line4("Volume " + str(volume))
	return

# Options menu
def display_options(lcd,radio):
	option = radio.getOption()

	if option != radio.TIMER and option != radio.ALARM \
			and option != radio.ALARMSETHOURS and option != radio.ALARMSETMINS :
		lcd.line1("Menu selection:")

	if option == radio.RANDOM:
		if radio.getRandom():
			lcd.line2("Random on")
		else:
			lcd.line2("Random off")

	elif option == radio.CONSUME:
		if radio.getConsume():
			lcd.line2("Consume on")
		else:
			lcd.line2("Consume off")

	elif option == radio.REPEAT:
		if radio.getRepeat():
			lcd.line2("Repeat on")
		else:
			lcd.line2("Repeat off")

	elif option == radio.TIMER:
		lcd.line1("Set timer function:")
		if radio.getTimer():
			lcd.line2("Timer " + radio.getTimerString())
		else:
			lcd.line2("Timer off")

	elif option == radio.ALARM:
		alarmString = "off"
		lcd.line1("Set alarm function:")
		alarmType = radio.getAlarmType()

		if alarmType == radio.ALARM_ON:
			alarmString = "on"
		elif alarmType == radio.ALARM_REPEAT:
			alarmString = "repeat"
		elif alarmType == radio.ALARM_WEEKDAYS:
			alarmString = "weekdays only"
		lcd.line2("Alarm " + alarmString)

	elif option == radio.ALARMSETHOURS:
		lcd.line1("Set alarm time:")
		lcd.line2("Alarm " + radio.getAlarmTime() + " hours")

	elif option == radio.ALARMSETMINS:
		lcd.line1("Set alarm time:")
		lcd.line2("Alarm " + radio.getAlarmTime() + " mins")

	elif option == radio.STREAMING:
		if radio.getStreaming():
			lcd.line2("Streaming on")
		else:
			lcd.line2("Streaming off")

	elif option == radio.RELOADLIB:
		if radio.getUpdateLibrary():
			lcd.line2("Update playlist: Yes")
		else:
			lcd.line2("Update playlist: No")

	if  radio.getSource() == radio.PLAYER:
		lcd.line4(radio.getProgress())

	return

# Display volume and timer
def displayLine4(lcd,radio,msg):
	message = msg
	if radio.getTimer():
		message = msg + " " + radio.getTimerString()
	if radio.alarmActive():
		message = message + ' ' + radio.getAlarmTime()
	lcd.line4(message)
	return

# Display wake up message
def displayWakeUpMessage(lcd):
	message = 'Good day'
	t = datetime.datetime.now()
	if t.hour >= 0 and t.hour < 12:
		message = 'Good morning'
	if t.hour >= 12 and t.hour < 18:
		message = 'Good afternoon'
	if t.hour >= 16 and t.hour <= 23:
		message = 'Good evening'
	lcd.line4(message)
	time.sleep(3)
	return

def displayShutdown(lcd):
	lcd.line1("Stopping radio")
	radio.execCommand("service mpd stop")
	lcd.line3(" ")
	lcd.line4(" ")
	radio.execCommand("shutdown -h now")
	lcd.line2("Shutdown issued")
	time.sleep(3)
	lcd.line1("Radio stopped")
	lcd.line2("Power off radio")
	return

def displayInfo(lcd,ipaddr,mpd_version):
	lcd.line2("Radio version " + radio.getVersion())
	lcd.line3(mpd_version)
	lcd.line4("GPIO version " + GPIO.VERSION)
	if ipaddr is "":
		lcd.line3("No IP network")
	else:
		lcd.scroll1("IP "+ ipaddr,interrupt)
	return

# Check Timer fired
def checkTimer(radio):
	interrupt = False
	if radio.fireTimer():
		log.message("Timer fired", log.INFO)
		radio.mute()
		radio.setDisplayMode(radio.MODE_SLEEP)
		interrupt = True
	return interrupt

# Check state (pause or play)
# If external client such as mpc or MPDroid issue a pause or play command
# Returns paused True if paused
def checkState(radio):
	paused = False
	display_mode = radio.getDisplayMode()
	state = radio.getState()
	radio.getVolume()

	if state == 'pause':
		paused = True
		if not radio.muted():
			if radio.alarmActive() and not radio.getTimer():
				radio.setDisplayMode(radio.MODE_SLEEP)
			radio.mute()
	elif state == 'play':
		if radio.muted():
			unmuteRadio(lcd,radio)
			radio.setDisplayMode(radio.MODE_TIME)
	return paused

### Main routine ###
if __name__ == "__main__":
	daemon = MyDaemon('/var/run/radiod.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			os.system("service mpd stop")
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'nodaemon' == sys.argv[1]:
			daemon.nodaemon()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'version' == sys.argv[1]:
			print "Version " + radio.getVersion()
		else:
			print "Unknown command: " + sys.argv[1]
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|status|version" % sys.argv[0]
		sys.exit(2)

# End of script 


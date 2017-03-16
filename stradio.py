import time
import sys

from rotary_class import RotaryEncoder
from test_lcd_textstar import TextStar
from mpd import MPDClient

# Switch definitions
#Menu Knob
UP_SWITCH = 17
DOWN_SWITCH = 18
MENU_SWITCH = 4
DOWN_SWITCH_IF_DAC = 10 

#Volume Knob
UP_SWITCH = 19
DOWN_SWITCH = 13
MENU_SWITCH = 26
DOWN_SWITCH_IF_DAC = 10

class Menu:
    """Menu class, accepts menu title and a list of menu options. 
    The getOption method returns option that should be shown
    The getSelected method returns the option selected after the button has been pressed"""
    def __init__(self,title="",options=[]):
        self.title = "*{}*".format(title[:14])
        self.options = options
        self.option_idx = 0
        self.option_selected = 0
        self.option_last = len(options) - 1
    def set_options(self,options):
        """Allow the list of options to be updated after initialisation"""
        self.options = options
        self.option_idx = 0
        self.option_selected = 0
        self.option_last = len(options) - 1
    def next(self):
        """Move to the next menu option"""
        self.option_idx += 1
        if self.option_idx > self.option_last:
            self.option_idx = 0
    def prev(self):
        """Move to the previous menu option"""
        self.option_idx -= 1
        if self.option_idx < 0:
            self.option_idx = self.option_last
    def select(self):
        """Select the current option"""
        self.option_selected = self.option_idx
        self.option_idx = 0
    def getOption(self):
        """Get the currently shown option"""
        return self.options[self.option_idx]
    def getSelected(self):
        """Get the selected option"""
        return self.options[self.option_selected]
    def getSelectedIdx(self):
        """Get the index of the selected option"""
        return self.option_selected

class Radio:
    MODE_MENU = 0
    MODE_PLAY = 1
    MODE_TUNING = 2
    MODE_POWER = 3
    def __init__(self):
        self.mpd = MPDClient()
        self.lcd = TextStar('/dev/serial0',115200)
        self.lcd.quiet = True
        self.menu_rotary = RotaryEncoder(UP_SWITCH,DOWN_SWITCH,MENU_SWITCH,self.tuning_event,2)
        
        self.connect()
        
        self.menus = ["Tuning","Power","Return"]
        self.current_menu = 0
        self.last_menu = len(self.menus)
        self.mainMenu = Menu(title='Menu', options=self.menus)

        self.playlist = ["Heart","BBC Glos","BBC R1"]
        
        self.tuningMenu = Menu(title='Tuning', options=self.playlist)
        
        self.powerMenu = Menu(title='Power', options=["Return","Power Off"])

        self.mode = self.MODE_PLAY

        self.display()
        
    def connect(self):
        try:
            self.mpd.connect("localhost",6600)
        except:
            self.mpd.close()
            self.mpd.connect("localhost",6600)
            
    
    def start_playlist(self):
        self.mpd.play()
        #self.update_lcd()
            
    def loop(self):
        while True:
            try:
                time.sleep(0.1)
                #self.update()
            except KeyboardInterrupt:
                self.lcd.write('Done')
                self._exit()

                
    def _exit(self):
        print("\nExit")
        self.mpd.stop()
        sys.exit(0)
                
    def tuning_event(self,evt):
        if self.mode == self.MODE_MENU:
            if evt == RotaryEncoder.CLOCKWISE:
                self.mainMenu.next()
            elif evt == RotaryEncoder.ANTICLOCKWISE:
                self.mainMenu.prev()
            elif evt == RotaryEncoder.BUTTONDOWN:
                self.mainMenu.select()
                self.selectMenu()
                
        elif self.mode == self.MODE_PLAY:
            if evt == RotaryEncoder.BUTTONDOWN:
                self.mode = self.MODE_MENU
                self.current_menu = 0

        elif self.mode == self.MODE_TUNING:
            if evt == RotaryEncoder.BUTTONDOWN:
                self.tuningMenu.select()
                new_id = self.tuningMenu.getSelectedIdx()
                self.mpd.play(new_id)
                self.mode = self.MODE_PLAY
            elif evt == RotaryEncoder.CLOCKWISE:
                self.tuningMenu.next()
            elif evt == RotaryEncoder.ANTICLOCKWISE:
                self.tuningMenu.prev()
                    
        elif self.mode == self.MODE_POWER:
            if evt == RotaryEncoder.CLOCKWISE:
                self.powerMenu.next()
            elif evt == RotaryEncoder.ANTICLOCKWISE:
                self.powerMenu.prev()
            elif evt == RotaryEncoder.BUTTONDOWN:
                self.powerMenu.select()
                if self.powerMenu.getSelected() == "Power Off":
                    #self.master.destroy()
                    self._exit()
                else:
                    self.mode = self.MODE_PLAY
                
        self.display()

    def selectMenu(self):
        #currentOption = self.menus[self.current_menu]
        currentOption = self.mainMenu.getSelected()
        if currentOption == "Tuning":
            self.playlist = self.mpd.playlistinfo()
            playlist = [item['name'] for item in self.playlist]
            self.tuningMenu.set_options(playlist)
            self.mode = self.MODE_TUNING
        elif currentOption == "Return":
            self.mode = self.MODE_PLAY
        elif currentOption == "Power":
            self.mode = self.MODE_POWER
            #self.master.destroy()
        
    def volume_event(self,evt):
        print("Volume:",evt)
        self.lcd.line1("Volume:%s" % evt)

    def display(self):
        if self.mode == self.MODE_MENU:
            self.display_menu()
        elif self.mode == self.MODE_PLAY:
            self.display_play()
        elif self.mode == self.MODE_TUNING:
            self.display_tuning()
        elif self.mode == self.MODE_POWER:
            self.display_power()
            
    def display_power(self):
        self.lcd.line1(self.powerMenu.title)
        self.lcd.line2(self.powerMenu.getOption())        

    def display_menu(self):
        self.lcd.line1(self.mainMenu.title)
        self.lcd.line2(self.mainMenu.getOption())

    def display_tuning(self):
        self.lcd.line1(self.tuningMenu.title)
        self.lcd.line2(self.tuningMenu.getOption())

    def display_play(self):
        #getCurPlaylist = self.tuningMenu.getSelected()
        getCurPlaylist = self.mpd.currentsong()['name']
        self.lcd.line1("*Playing*")
        self.lcd.line2(getCurPlaylist)
            
if __name__ == '__main__':
    r = Radio()
    #r.connect()
    r.start_playlist()
    r.loop()

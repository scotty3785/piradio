try:
    import tkinter as tk
except:
    import Tkinter as tk

import time

from dial_widget import RotaryEncoder
from lcd_widget import LCD
        
    
class App(tk.Frame):
    MODE_MENU = 0
    MODE_PLAY = 1
    MODE_TUNING = 2
    def __init__(self,master=None,**kw):
        tk.Frame.__init__(self,master=master,**kw)
        self.master = master
        self.lcd = LCD(self)
        self.lcd.grid(row=0,column=1,columnspan=2)
        RotaryEncoder(self,self.tuning_event).grid(row=1,column=1)
        RotaryEncoder(self,self.volume_event).grid(row=1,column=2)

        self.menus = ["Tuning","Power","Exit"]
        self.current_menu = 0
        self.last_menu = len(self.menus)

        self.playlist_idx = 0
        self.playlist_tuning_idx = 0
        self.playlist = ["Heart","BBC Glos","BBC R1"]

        self.mode = self.MODE_PLAY

        self.display()
        
    def tuning_event(self,evt):
        #print("Tuning:",evt)
        #self.lcd.line1("Tuning:%s" % evt)
        if self.mode == self.MODE_MENU:
            if evt == RotaryEncoder.CLOCKWISE:
                self.nextMenu()
            elif evt == RotaryEncoder.ANTICLOCKWISE:
                self.prevMenu()
            elif evt == RotaryEncoder.BUTTONDOWN:
                self.selectMenu()
        elif self.mode == self.MODE_PLAY:
            if evt == RotaryEncoder.BUTTONDOWN:
                self.mode = self.MODE_MENU

        elif self.mode == self.MODE_TUNING:
            if evt == RotaryEncoder.BUTTONDOWN:
                self.playlist_idx = self.playlist_tuning_idx
                self.mode = self.MODE_PLAY
            elif evt == RotaryEncoder.CLOCKWISE:
                self.playlist_tuning_idx += 1
                if self.playlist_tuning_idx >= len(self.playlist):
                    self.playlist_tuning_idx = 0
            elif evt == RotaryEncoder.ANTICLOCKWISE:
                print("Back")
                self.playlist_tuning_idx -= 1
                if self.playlist_tuning_idx < 0:
                    self.playlist_tuning_idx = len(self.playlist) - 1
        self.display()

    def nextMenu(self):
        self.current_menu += 1
        if self.current_menu >= self.last_menu:
            self.current_menu = 0

    def prevMenu(self):
        self.current_menu -= 1
        if self.current_menu < 0:
            self.current_menu = self.last_menu - 1

    def selectMenu(self):
        currentOption = self.menus[self.current_menu]
        if currentOption == "Tuning":
            self.mode = self.MODE_TUNING
        elif currentOption == "Exit":
            self.mode = self.MODE_PLAY
        elif currentOption == "Power":
            #self.mode = self.MODE_PLAY
            self.master.destroy()
        
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

    def display_menu(self):
        getOption = self.menus[self.current_menu]
        self.lcd.line1("*Menu*")
        self.lcd.line2(getOption)

    def display_tuning(self):
        getOption = self.menus[self.current_menu]
        getSelPlaylist = self.playlist[self.playlist_tuning_idx]
        self.lcd.line1("*Tuning*")
        self.lcd.line2(getSelPlaylist)

    def display_play(self):
        getCurPlaylist = self.playlist[self.playlist_idx]
        self.lcd.line1("*Playing*")
        self.lcd.line2(getCurPlaylist)
        

if __name__ == '__main__':
    root = tk.Tk()
    App(root).grid()
    root.mainloop()

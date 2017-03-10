try:
    import tkinter as tk
except:
    import Tkinter as tk

import time

class LCD(tk.Frame):
    def __init__(self,master=None,**kw):
        tk.Frame.__init__(self,master=master,**kw)
        self['borderwidth'] = 2
        self['relief'] = tk.RAISED
        self.line1str = tk.StringVar()
        self.line1str.set(" "*16)
        self.line1obj = tk.Label(self,textvariable=self.line1str,font=("Courier",12),anchor=tk.W)
        self.line1obj.grid()
        self.line2str = tk.StringVar()
        self.line2str.set(" "*16)
        self.line2obj = tk.Label(self,textvariable=self.line2str,font=("Courier",12),anchor=tk.W)
        self.line2obj.grid()
        
    def line1(self,text):
        self.line1str.set(text[:16].center(16," "))
        
    def line2(self,text):
        self.line2str.set(text[:16].center(16," "))
        
    
class App(tk.Frame):
    def __init__(self,master=None,**kw):
        tk.Frame.__init__(self,master=master,**kw)
        lcd = LCD(self)
        lcd.grid()
        lcd.line1("Hello World")
        lcd.line2("Hi")
        

if __name__ == '__main__':
    root = tk.Tk()
    App(root).grid()
    root.mainloop()

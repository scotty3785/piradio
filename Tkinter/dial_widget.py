try:
    import tkinter as tk
except:
    import Tkinter as tk

import time

class RotaryEncoder(tk.Frame):
    CLOCKWISE=1
    ANTICLOCKWISE=2
    BUTTONDOWN=3
    BUTTONUP=4
    def __init__(self,master=None,callback=None,**kw):
        if not callback:
            callback=self.event_default
        self.callback = callback
        tk.Frame.__init__(self,master=master,**kw)
        self['borderwidth'] = 2
        self['relief'] = tk.RAISED
        btn1cmd = lambda x = self.ANTICLOCKWISE: callback(x)
        btn1 = tk.Button(self,text='<',command=btn1cmd)
        btn1.grid(column=0,row=0)
        
        btn2down = lambda x = self.BUTTONDOWN: callback(x)
        btn2up = lambda x = self.BUTTONUP: callback(x)
        btn2 = tk.Button(self,text='*')
        btn2.bind("<Button-1>",self.button_down)
        btn2.bind("<ButtonRelease-1>",self.button_up)
        btn2.grid(column=1,row=0)
        
        btn3cmd = lambda x = self.CLOCKWISE: callback(x)
        btn3 = tk.Button(self,text='>',command=btn3cmd)
        btn3.grid(column=2,row=0)
    def button_down(self,e):
        self.callback(self.BUTTONDOWN)
    def button_up(self,e):
        self.callback(self.BUTTONUP)
        
    def event_default(self,evt):
        print(evt)
        
    
class App(tk.Frame):
    def __init__(self,master=None,**kw):
        tk.Frame.__init__(self,master=master,**kw)
        dial1 = RotaryEncoder(master=self,callback=self.event)
        dial1.grid()
    def event(self,evt):
        print(evt)
        

if __name__ == '__main__':
    root = tk.Tk()
    App(root).grid()
    root.mainloop()

import display
from machine import PWM, RTC
import utime
import time
import uasyncio as asyncio

def rgb(r,g,b): #invese color
        return((0xFF-b<<16) + (0xFF-g<<8) + (0xFF-r))

class GuiException(Exception):
    pass


class MicroGUI(display.TFT): 
    #define some colors
    RED=rgb(255,0,0)
    GREEN=rgb(0,255,0)
    BLUE=rgb(0,0,255)
    YELLOW=rgb(255,255,0)
    ORANGE=rgb(255,165,0)
    WHITE=rgb(255,255,255)
    BLACK=rgb(0,0,0)
    GRAY=rgb(128,128,128)
    LIGHTGRAY=rgb(211,211,211)
    halign_const=[0,display.TFT.CENTER,display.TFT.RIGHT]
    valign_const=[0,display.TFT.CENTER,display.TFT.BOTTOM]
    
    def __init__(self):
        super().__init__()
        self.root=Widget([0,0,320,240])
        self.touched_widget=None
        self.touch_calibration=(500,3500,500,3500)
        self.initiated=0
        #self.movable=False
    
   
    @property
    def height(self):
        return self.screensize()[1]
    
    @property
    def width(self):
        return self.screensize()[0]

    def init(self, *args, **kwargs) :
        if 'backl_pin' in kwargs: #interference with TFT, need to remove the parameter from **kwargs dict
            self._backl=PWM(kwargs['backl_pin'])
            self._backl.duty(100)
            del kwargs['backl_pin']
        kwargs.setdefault('rot',super().LANDSCAPE)
        super().init(*args, **kwargs)
        self.rot=kwargs['rot']
        self.touch_start=None
        self.touch_current=None
        self.debounce=0
        self.initiated=1
        loop = asyncio.get_event_loop()
        loop.create_task(self.handle_touch())


    def  deinit(self):
        super().deinit()
        self.initiated=False
        #todo: led


    def clearwin(self):
        w,h=self.winsize()
        self.rect(0,0,w,h,self.get_bg(), self.get_bg())

    async def handle_touch(self):
        while self.initiated:
            t,x, y=self.gettouch()
            if t and self.touch_start is None: #touch_down
                #if self.debounce<1: #false positive are rare, no debounce
                #    self.debounce+=1
                #else:
                    print('touch at ({},{})'.format(x,y))
                    self.touch_start=x,y
                    self.touch_current=x,y
                    self.touched_widget,self.touch_window =self.root.on_touch((x,y), (0,0,self.width, self.height), self)
                    self.debounce=0                
            elif t and self.touch_start is not None:#touch_move
                self.touch_current=(x,y)
                #if self.touched_widget.is_movable: #this is set by the widget at touch_down
                #self.touched_widget.on_move((x-self.touch_window[0], y-self.touch_window[1]), self.touch_window)
                self.touched_widget.on_move(self.touch_current, self.touch_window, self)
            elif not t and self.touch_start is not None:#touch release
                if self.debounce<1:
                    self.debounce+=1
                else:
                    print('release at ({},{})'.format(*self.touch_current))
                    #self.movable=False
                    self.touched_widget.on_release(self.touch_current, self.touch_window, self)
                    self.touch_start=None
                    self.touch_current=None
                    self.debounce=0    
            await asyncio.sleep(0.05)  


    def backlight(self, *arg):
        return self._backl.duty(*arg) 

    def orient(self, rot=None):
        if rot is not None:
            super().orient(rot)
            self.rot=rot
        return self.rot

    def calibrate_touch(self):
        raise NotImplementedError
        #todo:calibration

    def gettouch(self,raw=False):
        cal=self.touch_calibration
        res=self.screensize()
        t,y,x=super().gettouch(raw=True)
        if raw:
            return(t,x,y)
        if not t or x<cal[0] or x>cal[1] or y<cal[2] or y>cal[3]: #maybe better return extremes
            return False,0,0
        #do calibration
        x=((x-cal[0])/(cal[1]-cal[0]))*res[0]
        y=((y-cal[2])/(cal[3]-cal[2]))*res[1]
        if self.orient() in [super().PORTRAIT,super().PORTRAIT_FLIP]: 
            (x,y)=(y,x)
        if self.orient() in [super().LANDSCAPE_FLIP,super().PORTRAIT_FLIP]:
            y=res[1]-y
        return(t,int(x),int(y))

    def draw(self):
        self.root.draw(self, (0,0,self.width, self.height) )
    
    def mainloop(self):
        self.draw()
        #start async loop for touch
        loop = asyncio.get_event_loop()
        try: 
            loop.run_forever()
        except Exception as e:
            self.clear()
            self.text(self.CENTER, self.CENTER, '{}'.format(e))
            raise e

    #def refresh(self):
        #refresh the screen
    #    self.screen.



class Widget:
    def __init__(self, bg=MicroGUI.BLACK,fg=MicroGUI.WHITE):
        self.bg=bg
        self.fg=fg
        self.is_visible=False

    def draw(self,screen, win):
        #print('draw {} at {}'.format(self,win))
        if screen is not None:
            self.screen=screen
        if win is not None:
            self.win=win
        self.is_visible=True
        self.screen.setwin(*self.win)
        self.screen.set_bg(self.bg)
        self.screen.set_fg(self.fg)
        #self.screen.clearwin()
        
    def deactivate(self):
        self.is_visible=False

    def on_touch(self,pos, win, screen):        
        return self, win
    def on_move(self, pos, win, screen):
        pass
    def on_release(self, pos, win, screen):
        print('unhandled release on {} at {}'.format(self, pos))
        pass

class Frame(Widget):
    def __init__(self,  bg=MicroGUI.BLUE,fg=MicroGUI.WHITE, side=0):
        super().__init__( bg,fg)
        self.widgets=[]        
        self.sizes=[]
        self.side=side#todo: this is not considered 
    
    def pack(self, widget, size=1):
        self.widgets.append(widget)
        self.sizes.append(size)
        

    def draw(self,screen=None, win=None):
        super().draw(screen, win)

        #self.screen.clearwin()
        if len(self.widgets)==0:
            return
        if self.side==0:
            step=(self.win[3]-self.win[1])/sum(self.sizes)
            offset=self.win[1] 
        elif self.side==1:
            step=(self.win[2]-self.win[0])/sum(self.sizes)
            offset=self.win[0] 
        else: raise NotImplementedError

        for w,s in zip(self.widgets, self.sizes):
            if self.side==0:
                widget_win=(self.win[0], int(offset),self.win[2],int(offset+step*s)) 
            elif self.side==1:
                widget_win=(int(offset),self.win[1],int(offset+step*s),self.win[3]) 
            else: raise NotImplementedError
            w.draw(self.screen, widget_win)
            offset+=step*s
    def deactivate(self):
        self.is_visible=False
        for w in self.widgets:
            w.deactivate()
    
    def _get_rel_widget_wd(self,pos_rel):#pos_rel is between 0 and 1
        total=sum(self.sizes)
        i=0
        for idx,s in enumerate(self.sizes):
            i+=(s/total)
            if i>= pos_rel:
                return idx,i-s/total, i 
        raise GuiException('Frame widget in {} at relative position {} not found'.format(self, pos_rel) )

    def on_touch(self,pos, win, screen):    
        if self.side==0:#top
            if pos[1]>win[3]:
                raise GuiException('touch outside window in {}, touch at pos {} with window defined as {}'.format(self,pos, win))            
            idx,start, end=self._get_rel_widget_wd((pos[1]-win[1])/(win[3]-win[1]))            
            height=win[3]-win[1]
            new_win=(win[0], win[1]+int(start*height), win[2], win[1]+int(end*height))
        elif self.side==1:#left
            if pos[0]>win[2]:
                raise GuiException('touch outside window in {}, touch at pos {} with window defined as {}'.format(self,pos, win))      
            idx,start, end=self._get_rel_widget_wd((pos[0]-win[0])/(win[2]-win[0]))
            width=win[2]-win[0]
            new_win=(win[0]+int(start*width), win[1], win[0]+int(end*width), win[3])
        else: 
            return NotImplementedError        
        return self.widgets[idx].on_touch(pos, new_win, screen)

class Menue(Widget):
    def __init__(self, title_size, side=0,callback=None):
        super().__init__()
        self.active=0
        self.title_size=title_size
        self.side=side #0=top, 1=left, (todo: 2=bottom, 3=right not implemented so far)
        self.callback=callback #gets called uppon page change
        self.pages=[]
    
    def get_page(self,title):
        for p in self.pages:
            if p.title==title:
                return p
        raise GuiException('page "{}" not found'.format(title))

    def add_page(self, title,title_bg=MicroGUI.BLUE,title_fg=MicroGUI.WHITE,bg=MicroGUI.BLACK,fg=MicroGUI.WHITE,side=0):
        self.pages.append(MenuePage(title,title_bg,title_fg,bg,fg,  side))
        return self.pages[-1]
    
    def on_touch(self, pos, win, screen):        
        if self.side==0:#top
            if pos[1]-win[1]<self.title_size:
                return self, win#(win[0], win[1], win[2], win[1]+self.title_size)
            else:
                return self.pages[self.active].on_touch(pos, (win[0], win[1]+self.title_size, win[2], win[3]), screen)
        elif self.side==1:#left
            if pos[0]-win[0]<self.title_size:
                return self, win#(win[0], win[1], win[0]+self.title_size, win[1])
            else:
                return self.pages[self.active].on_touch(pos, (win[0]+self.title_size, win[1], win[2], win[3]), screen)
        else: 
            return NotImplementedError

    def on_release(self, pos, win, screen):
        print('release in menue, prev page = '+self.pages[self.active].title)
        selected= self.active
        
        if self.side==0:#top
            if pos[1]-win[1]<self.title_size:
                #determine widget
                selected=int((pos[0]-win[0])/(win[2]-win[0]+1) *len(self.pages))
        elif self.side==1:#left
            if pos[0]-win[0]<self.title_size:
                #determine widget
                selected=int((pos[1]-win[1])/(win[3]-win[1]+1)*len(self.pages))
        else: raise NotImplementedError
        if selected!= self.active:
            print('selected '+self.pages[selected].title)
            self.pages[self.active].deactivate()
            self.active=selected
            self.draw(screen,win)
            if self.callback is not None:
                self.callback()

    def draw(self,screen=None, win=None):
        super().draw(screen, win)
        #draw header
        if len(self.pages) ==0:
            raise GuiException('Attempt to draw menue without defining pages')
        if self.side==0:#top 
            self.screen.setwin(self.win[0],self.win[1],self.win[2],self.title_size+self.win[1])
            step=(self.win[2]-self.win[0])/len(self.pages)
            offset=self.win[0]
        elif self.side==1:#left 
            self.screen.setwin(self.win[0],self.win[1],self.win[0]+self.title_size,self.win[3])
            step=(self.win[3]-self.win[1])/len(self.pages)
            offset=self.win[1]
        else:
            raise NotImplementedError
        
        screen.set_bg(self.pages[self.active].title_bg)
        screen.set_fg(self.pages[self.active].title_fg)
        screen.clearwin()
        
        for i,p in enumerate(self.pages):
            if self.side==0:
                screen.setwin(int(offset),win[1],int(offset+step),self.title_size+win[1])
            elif self.side==1:
                screen.setwin(win[0], int(offset), win[0]+self.title_size, int(offset+step))
            screen.text(screen.CENTER, screen.CENTER,p.title)
            if i==self.active:#underline active
                length=screen.textWidth(p.title)   
                if self.side==0:
                    line_x=int((step-length)/2 )
                    line_y=int((self.title_size+screen.fontSize()[1])/2+2)
                elif self.side==1:
                    line_x=int((self.title_size-length)/2 )
                    line_y=int((step+screen.fontSize()[1])/2+2)
                screen.line(line_x,line_y,line_x+length,line_y)       
            offset+=step     
        if self.side==0:    
            self.pages[self.active].draw(screen,(win[0],win[1]+self.title_size,win[2],win[3]))
        elif self.side==1:
            self.pages[self.active].draw(screen, (win[0]+self.title_size,win[1],win[2],win[3]))

class MenuePage(Frame):
    def __init__(self, title, title_bg, title_fg,bg=MicroGUI.BLUE,fg=MicroGUI.WHITE, side=0):
        super().__init__( bg,fg,side)
        self.title=title
        self.title_bg=title_bg
        self.title_fg=title_fg
        
class Label(Widget):    
    def __init__(self,text,decoration='{}',halign=1,valign=1):
        super().__init__()
        self.halign=halign
        self.valign=valign
        if isinstance(text,Var):
            text.widgets.append(self)
        else:
            text=Var(text, self)
        self.text=text
        self.decoration=decoration
    
    def draw(self,screen=None, win=None):
        super().draw(screen, win)
        self.screen.clearwin()
        self.screen.text(self.screen.halign_const[self.halign],self.screen.valign_const[self.valign],self.decoration.format(self.text.val))

class Button(Label):
    def __init__(self, text, command,margin,halign=1,valign=1):
        #todo: margins, minsize, maxsize
        super().__init__(text,halign,valign)
        self.command=command #must be callable

    #def on_touch(self, pos) change color

    def on_release(self, pos, win, screen):#touch and release on same widget
        #if pos is within win
        self.command()
    
class Slider(Widget): 
    def __init__(self,  value,horizontal=True, min=0, max=100, command=None, bg=MicroGUI.BLACK,fg=MicroGUI.LIGHTGRAY, active_fg=MicroGUI.BLUE, bar_wd=4,ball_r=10 , align=1, mar=15):
        super().__init__()
        if isinstance(value,Var):
            value.widgets.append(self)
        else:
            value=Var(int(value), self)
        self.value=value #current 
        self.horizontal=horizontal 
        self.min=min
        self.max=max
        self.command=command
        self.bg=bg
        self.fg=fg
        self.active_fg=active_fg
        self.bar_wd=bar_wd
        self.ball_r=ball_r
        self.mar=mar
        self.align=align

    def set_val(self,value, screen, win):
        self.value=value
        win=None #where do we get the window from?
        self.draw(screen, win)
    
    def on_touch(self,pos, win, screen):     
        self.on_move(pos, win, screen)   
        return self, win

    def on_move(self,pos, win, screen):        
        if self.horizontal:
            pos_rel=(pos[0]-win[0]-self.mar)/(win[2]-win[0]-2*self.mar)
        else:
            pos_rel=1-(pos[1]-win[1]-self.mar)/(win[3]-win[1]-2*self.mar)
        if pos_rel<0:
            pos_rel=0
        elif pos_rel>1:
            pos_rel=1
        self.value.val=int(self.min+pos_rel*(self.max-self.min))
        print ('new value {}'.format(self.value.val))
    
    def on_release(self, pos, win,screen):
        if self.command is not None:
            self.command(self.value.val)

    def draw(self, screen=None,win=None):
        super().draw(screen, win)
        
        self.screen.clearwin()
        val_rel=(self.value.val-self.min)/(self.max-self.min)
        if self.value.val>self.min:
                fg=bg=self.active_fg
        else:
            fg=self.fg
            bg=self.bg
        if self.horizontal:#left to right
            len=self.win[2]-self.win[0]-2*self.mar
            y=int((self.win[3]-self.win[1]-self.bar_wd)/2)
            self.screen.rect(self.mar, y, int(val_rel*len), self.bar_wd, self.active_fg,self.active_fg)
            self.screen.rect(int(self.mar+val_rel*len), y, int((1-val_rel)*len), self.bar_wd, self.fg,self.fg)            
            self.screen.circle(int(self.mar+val_rel*len),int((self.win[3]-self.win[1])/2),self.ball_r, fg, bg)
        else: #bottom to top
            len=self.win[3]-self.win[1]-2*self.mar
            x=int((self.win[2]-self.win[0]-self.bar_wd)/2)
            self.screen.rect(x,self.mar,  self.bar_wd, int((1-val_rel)*len),self.fg,self.fg)
            self.screen.rect(x,int(self.mar+(1-val_rel)*len), self.bar_wd,int(val_rel*len),  self.active_fg,self.active_fg)
            
            self.screen.circle(int((self.win[2]-self.win[0])/2),int(self.mar+(1-val_rel)*len),self.ball_r, fg, bg)

        


class CheckBox(Widget):
    pass

class RadioButton(Widget):
    pass

class Switch(CheckBox):
    pass

class Chart(Widget):
    pass

class DynamicWidget(Widget):
    def __init__(self):
        super().__init__()
        self.is_active=False
        
    def activate(self, screen,win, interval=1):
        self.is_active=True
        self.is_visible=True
        loop = asyncio.get_event_loop()
        loop.create_task(self.mainloop(screen,win, interval)) 
    
    async def mainloop(self,screen, win, interval):
        while self.is_active and self.is_visible:
            self.update(screen,win)
            await asyncio.sleep(interval)
        self.is_active=False

    def update(self, screen, win):
        #do something
        #print('dynamic widget update is not implemented')
        self.draw(screen, win)

class Clock(DynamicWidget):
    def __init__(self, halign=1, valign=1):
        super().__init__()
        self.halign=halign
        self.valign=valign
        RTC().ntp_sync(server="hr.pool.ntp.org", tz="CET-1CEST")

    
    def draw(self,screen=None, win=None):
        super().draw(screen, win)
        if not self.is_active:
            self.activate(screen, win)
        self.screen.clearwin()
        now=utime.localtime()
        text='{2}.{1:02d}.{0} - {3}:{4:02d}:{5:02d} Uhr'.format(*now)
        self.screen.text(self.screen.halign_const[self.halign],self.screen.valign_const[self.valign],text)


class FotoFrame(Widget):
    pass

class Var:
    def __init__(self, val, widget=None):
        self.__val=val
        self.widgets=[]
        if isinstance(widget, Widget):
            self.widgets.append(widget)
        

    @property
    def val(self):
        return self.__val
    
    @val.setter
    def val(self, val):
        self.__val=val
        for w in self.widgets:
            if w.is_visible:
                w.draw()


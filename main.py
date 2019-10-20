try:
    import uasyncio as asyncio
except ImportError:
    import upip
    print('installing asyncio')
    upip.install('micropython-uasyncio', '.')
    upip.install('micropython-uasyncio.synchro', '.')
    upip.install('micropython-uasyncio.queues', '.')
    import uasyncio as asyncio
    
import time, math
from machine import SPI, PWM, Pin
from time import sleep
import microgui as gui

screen = gui.MicroGUI()
screen.init(screen.ILI9488, width=240, height=320, 
    miso=19, mosi=23, clk=18, cs=5, dc=21, tcs=0,rst_pin=4, backl_pin=22, bgr=False,
    hastouch=screen.TOUCH_XPT,backl_on=1, speed=40000000, splash=False, rot=screen.LANDSCAPE_FLIP)

#example for the GUI layout

top_menue=gui.Menue(60, side=1)
screen.root=top_menue
licht=top_menue.add_page(title='Licht', title_fg=screen.BLACK, title_bg=screen.YELLOW)
licht_menue=gui.Menue(60, side=0)
licht.pack(licht_menue)
musik=top_menue.add_page(title='Musik', title_fg=screen.WHITE, title_bg=screen.RED)
musik.pack(gui.Label('hier steuert man die anlage'))
wetter=top_menue.add_page(title='Wetter', title_fg=screen.WHITE, title_bg=screen.BLUE)
wetter.pack(gui.Label('bestimmt bald wieder gut'))
uhr=top_menue.add_page(title='Uhr', title_fg=screen.BLACK, title_bg=screen.GREEN)
uhr.pack(gui.Clock())
settings=top_menue.add_page(title='Settings', title_fg=screen.BLACK, title_bg=screen.YELLOW)
settings.pack(gui.Label('Hintergrundbeleuchtung'))
settings.pack(gui.Frame(side=1))
bgled=gui.Var(100)
settings.widgets[-1].pack(gui.Slider(bgled,min=1, command=screen.backlight), size=5)
settings.widgets[-1].pack(gui.Label(bgled, decoration='{}%'))
settings.pack(gui.Label('weitere Einstellungen'), size=4)
fotos=top_menue.add_page(title='Fotos', title_fg=screen.WHITE, title_bg=screen.RED)
fotos.pack(gui.Label('Fotos'))
wz=licht_menue.add_page(title='Wohnzi.', side=0, title_fg=screen.BLACK, title_bg=screen.YELLOW)
lichter=[]
for l in range(2):
    lf=gui.Frame(side=1)
    wz.pack(lf)
    lval=gui.Var(0)
    lf.pack(gui.Label(l+1, decoration='L{}: '))
    lf.pack(gui.Slider(lval), size=4)
    lf.pack(gui.Label(lval, decoration='{}%'))

sz=licht_menue.add_page(title='Schlafzi.', side=1,title_fg=screen.BLACK,title_bg=screen.YELLOW)
sz.pack(gui.Label('Schlafzimmer'))
sz.pack(gui.Label('2. Label'))

bz=licht_menue.add_page(title='Bastelzi.', title_fg=screen.BLACK, title_bg=screen.YELLOW)
#z.pack(gui.Label('Bastelzimmer'))
bz.pack(gui.Menue(60,side=1))
submenue=bz.widgets[0]
for i in range(3):
    page=submenue.add_page(title= 'Licht {}'.format(i+1), title_bg=screen.RED,side=1)
    #page.pack(gui.Label('Licht {} Steuerung'.format(i+1)))
    for l in range(2):
        lf=gui.Frame(side=0)
        page.pack(lf)
        lval=gui.Var(0)
        lf.pack(gui.Label(l+1, decoration='L{}: '))
        lf.pack(gui.Slider(lval, horizontal=False), size=4)
        lf.pack(gui.Label(lval, decoration='{}%'))
screen.mainloop()


from kivymd.app import MDApp
from kivymd.uix.navigationdrawer import MDNavigationLayout
from kivy_garden.graph import MeshLinePlot
from kivy.clock import Clock
from serial import Serial
from threading import Thread
import time
import math

class CH():
    
    def __init__(self, color, list_pos):
        self.list_pos = list_pos
        self.color = color
        self.plot = MeshLinePlot(color=self.color)
        self.times = []
        self.meas = []
        
    def reset(self):
        self.times = []
        self.meas = []
        
    def update(self, lista):
        self.times.append(float(lista[0]))
        self.meas.append(-int(lista[self.list_pos]) * 20.48 / 65535 + 10.24)
        self.points = [(x,y) for x, y in zip(self.times, self.meas)]
        self.plot.points = self.points


class CHV():
    
    def __init__(self, color, list_pos, multiplicador=1):
        self.list_pos = list_pos
        self.color = color
        self.plot = MeshLinePlot(color=self.color)
        self.times = []
        self.meas = []
        self.multiplicador = multiplicador
        
    def reset(self):
        self.times = []
        self.meas = []
        
    def update(self, lista):
        self.times.append(float(lista[0]))
        self.meas.append(float(lista[self.list_pos]) * self.multiplicador)
        self.points = [(x,y) for x, y in zip(self.times, self.meas)]
        self.plot.points = self.points
        
 
        
colors = [[1,0,0,1], [0,1,0,1], [0,0,1,1], [1,1,1,1],
          [1,1,0,1], [1,0,1,1], [0,1,1,1], [0,0.5,0,1],
          [0.5,0,0,1]]
          
dvolts = {'temp': CHV(colors[8], 1, 1),
          'PS': CHV(colors[0], 11, 0.1875*16.7288/1000),
          'refV': CHV(colors[1], 13, 0.0625/1000),
          'minus12V': CHV(colors[2], 12, -0.1875*2.647/1000),
          '5V': CHV(colors[3], 10, 0.1875/1000)}
          
dchs = {'ch0': CH(colors[0], 2), 'ch1': CH(colors[1], 3),
        'ch2': CH(colors[2], 4), 'ch3': CH(colors[3], 5),
        'ch4': CH(colors[4], 6), 'ch5': CH(colors[5], 7),
        'ch6': CH(colors[6], 8), 'ch7': CH(colors[7], 9)}

def sender():

    global stop_thread
    myfile = open('rawdata/emulatormeasurmentslong.csv')
    lines = myfile.readlines()
    myfile.close()
    serial_sender = Serial('/dev/pts/2', 115200, timeout=1)
    time_start = time.time()
    
    for line in lines:
        #print ('%s,%s' %(time.time() - time_start, line.strip()))
        serial_sender.write(('%s,%s' %(time.time() - time_start, line)).encode())
        time.sleep(0.05)
        if stop_thread:
            break

    serial_sender.close()
    print ('End of sending')


class MainApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'LightBlue'
        self.theme_cls.primay_hue = '200'
        self.title = 'Blue Physics v.10.0'
        self.icon = 'images/logoonlyspheretransparent.png'
        self.mygraph = self.root.ids.mygraph
        for ch in dchs.values():
            self.mygraph.add_plot(ch.plot)


    def start(self):
        global stop_thread
        self.mygraph.xmax = 60
        self.mygraph.ymax = 10
        self.mygraph.ymin = 0
        for ch in dchs.values():
            ch.reset()
        stop_thread = False
        self.sender_thread = Thread(target=sender)
        self.sender_thread.daemon = True
        self.sender_thread.start()
        self.ser = Serial('/dev/pts/3', 115200, timeout=1)
        Clock.schedule_interval(self.update, 0.01)


    def stop(self):
        global stop_thread
        Clock.unschedule(self.update)
        stop_thread = True
        self.sender_thread.join()
        print('sender_thread kiled')


    def update(self, dt):
        if self.ser.in_waiting:
            full_line = self.ser.read(self.ser.in_waiting).decode().strip()
            full_lines = full_line.split('\n')
            all_llines = [line.split(',') for line in full_lines]
            for lline in all_llines:
                if len(lline) != 14:
                    print ('error one line: ', len(lline))
                for ch in dchs.values():
                    ch.update(lline)

        
            if float(all_llines[-1][0]) > 60:
                self.mygraph.xmax = float(all_llines[-1][0])
            


    def callback(self):
        print ('oido')



MainApp().run()

from kivymd.app import MDApp
from kivy.factory import Factory
from kivymd.uix.bottomsheet import MDCustomBottomSheet
from kivy.utils import get_color_from_hex
from kivymd.color_definitions import colors
from kivy_garden.graph import Graph, MeshLinePlot
from kivy.clock import Clock
from serial import Serial
from threading import Thread
import time
import math

class MyGraph(Graph):
    pass

class CH():
    
    def __init__(self, color, list_pos):
        self.list_pos = list_pos
        self.name = 'ch%s' %(list_pos - 2)
        self.checkbox = 'chb%s' %(list_pos - 2)
        self.color = color
        self.plot = MeshLinePlot(color=get_color_from_hex(self.color))
        self.times = []
        self.meas = []
        self.meastoplot = []
        
    def reset(self):
        self.times = []
        self.meas = []
        self.meastoplot = []

    def firstupdate(self, lista):
        timetoadd = float(lista[0])
        valuetoadd = int(lista[self.list_pos])
        valuetoplot = -valuetoadd * 20.48 / 65535 + 10.24
        self.times.append(timetoadd)
        self.meas.append(valuetoadd)
        self.meastoplot.append(valuetoplot)
        self.points = [(x,y) for x, y in zip(self.times, self.meastoplot)]
        self.plot.points = self.points
        self.graph.ymax = valuetoplot + 1
        self.graph.ymin = valuetoplot - 1


    def update(self, lista):
        timetoadd = float(lista[0])
        valuetoadd = int(lista[self.list_pos])
        valuetoplot = -valuetoadd * 20.48 / 65535 + 10.24
        self.times.append(timetoadd)
        self.meas.append(valuetoadd)
        self.meastoplot.append(valuetoplot)
        self.points = [(x,y) for x, y in zip(self.times, self.meastoplot)]
        self.plot.points = self.points
        if valuetoplot > self.graph.ymax:
            self.graph.ymax = valuetoplot + 1
        if valuetoplot < self.graph.ymin:
            self.graph.ymin = valuetoplot - 1
        if timetoadd > 60:
            self.graph.xmax = timetoadd


class CHV(CH):

    def __init__(self, color, list_pos, multiplicador=1):
        CH.__init__(self, color, list_pos)
        self.multiplicador = multiplicador

    def firstupdate(self, lista):
        timetoadd = float(lista[0])
        valuetoadd = int(lista[self.list_pos])
        valuetoplot = valuetoadd * self.multiplicador
        self.times.append(timetoadd)
        self.meas.append(valuetoadd)
        self.meastoplot.append(valuetoplot)
        self.points = [(x,y) for x, y in zip(self.times, self.meastoplot)]
        self.plot.points = self.points
        self.graph.ymax = valuetoplot + 1
        self.graph.ymin = valuetoplot - 1

    def update(self, lista):
        timetoadd = float(lista[0])
        valuetoadd = int(lista[self.list_pos])
        valuetoplot = valuetoadd * self.multiplicador
        self.times.append(timetoadd)
        self.meas.append(valuetoadd)
        self.meastoplot.append(valuetoplot)
        self.points = [(x,y) for x, y in zip(self.times, self.meastoplot)]
        self.plot.points = self.points
        if valuetoplot > self.graph.ymax:
            self.graph.ymax = valuetoplot + 1
        if valuetoplot < self.graph.ymin:
            self.graph.ymin = valuetoplot - 1
        if timetoadd > 60:
            self.graph.xmax = timetoadd



mcolors = [colors['Gray']['300'],
           colors['Cyan']['A200'],
           colors['Orange']['A400'],
           colors['Purple']['A400'],
           colors['Teal']['A400'],
           colors['Blue']['A400'],
           colors['Yellow']['A200'],
           colors['Red']['A400'],
           colors['Red']['900']]
          
dvolts = {'Temp': CHV(mcolors[8], 1, 1),
          'PS': CHV(mcolors[1], 11, 0.1875*16.7288/1000),
          'refV': CHV(mcolors[2], 13, 0.0625/1000),
          '-12V': CHV(mcolors[3], 12, -0.1875*2.647/1000),
          '5V': CHV(mcolors[4], 10, 0.1875/1000)}
          
dchs = {'ch0': CH(mcolors[0], 2), 'ch1': CH(mcolors[1], 3),
        'ch2': CH(mcolors[2], 4), 'ch3': CH(mcolors[3], 5),
        'ch4': CH(mcolors[4], 6), 'ch5': CH(mcolors[5], 7),
        'ch6': CH(mcolors[6], 8), 'ch7': CH(mcolors[7], 9)}

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
        time.sleep(0.3)
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
        self.graphchs = MyGraph()
        self.graphvolts = {'Temp':MyGraph(), 'PS':MyGraph(),
                           'refV':MyGraph(), '5V':MyGraph(),
                           '-12V':MyGraph()}
        for key in self.graphvolts.keys():
            self.graphvolts[key].add_plot(dvolts[key].plot)
            dvolts[key].graph = self.graphvolts[key]
        dvolts['Temp'].graph.ylabel = 'Temp (C)'
        self.measlayout = self.root.ids.measurescreenlayout
        self.measlayout.add_widget(self.graphchs)
        for ch in dchs.values():
            self.graphchs.add_plot(ch.plot)
            ch.graph = self.graphchs
        self.contentsheet = Factory.ContentCustomSheet()


    def start(self):
        global stop_thread
        self.graphchs.xmax = 60
        for ch in dchs.values():
            ch.reset()
        for chv in dvolts.values():
            chv.reset()
        stop_thread = False
        self.sender_thread = Thread(target=sender)
        self.sender_thread.daemon = True
        self.sender_thread.start()
        self.ser = Serial('/dev/pts/3', 115200, timeout=1)
        self.firstupdate()
        Clock.schedule_interval(self.update, 0.01)


    def stop(self):
        global stop_thread
        Clock.unschedule(self.update)
        stop_thread = True
        self.sender_thread.join()
        self.ser.close()
        print('sender_thread kiled')


    def firstupdate(self):
        lline = self.ser.readline().decode().strip().split(',')
        for i in range(10):
            lline = self.ser.readline().decode().strip().split(',')
            if len(lline) == 14:
                break
            else:
                print('error line', lline)
        for ch in dchs.values():
            ch.firstupdate(lline)
        for chv in dvolts.values():
            chv.firstupdate(lline)

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
                for chv in dvolts.values():
                    chv.update(lline)


    def bottomsheet(self):
        self.custom_sheet = MDCustomBottomSheet(screen=self.contentsheet,
                                                radius_from='top')
        self.custom_sheet.open()


    def addremoveplot(self, intext, checkbox, value):
        if value:
            self.graphchs.add_plot(dchs[intext].plot)
        else:
            self.graphchs.remove_plot(dchs[intext].plot)


    def addremovegraph(self, intext, checkbox, value):
        print (intext, checkbox, value)
        if intext != 'None':
            if value:
                self.measlayout.add_widget(self.graphvolts[intext])
            else:
                self.measlayout.remove_widget(self.graphvolts[intext])


    def callback(self):
        print ('oido')



MainApp().run()

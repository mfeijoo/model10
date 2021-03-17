#!/usr/bin/env python3
from kivymd.app import MDApp
from kivy.factory import Factory
from kivymd.uix.bottomsheet import MDCustomBottomSheet
from kivy.utils import get_color_from_hex
from kivymd.color_definitions import colors
from kivy_garden.graph import Graph, MeshLinePlot
from kivy.clock import Clock
from serial import Serial
import serial.tools.list_ports
from threading import Thread
import time
import math
import pandas as pd

class MyGraph(Graph):
    pass


mcolors = [colors['Gray']['300'],
           colors['Cyan']['A200'],
           colors['Orange']['A400'],
           colors['Purple']['A400'],
           colors['Teal']['A400'],
           colors['Blue']['A400'],
           colors['Yellow']['A200'],
           colors['Red']['A400'],
           colors['Red']['900']]
          
        
number_of_channels = 2

lchs = [{'name':'ch%s' %i,
         'meas':[], 
         'color':mcolors[i], 
         'plot': MeshLinePlot(color=get_color_from_hex(mcolors[i]))} for i in range(number_of_channels)]


def receiver():
    global stop_thread, times
    times = []
    counts = []
    temps = []
    v5s = []
    PSs = []
    vminus15s = []
    vrefs = []
    for dch in lchs:
        dch['meas'] = []
    device = list(serial.tools.list_ports.grep('Adafruit ItsyBitsy M4'))[0].device
    ser = serial.Serial(device, 115200, timeout=1)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.write(b't')
    
    while not(stop_thread):
        if ser.in_waiting:
            inbytes = ser.read(22)
            count = int.from_bytes(inbytes[:4], 'big')
            mytime = int.from_bytes(inbytes[4:8], 'big')
            temp = int.from_bytes(inbytes[8:10], 'big')
            lmeas = [int.from_bytes(inbytes[10+2*i:12+2*i], 'big') for i in range(number_of_channels)]
            v5 = int.from_bytes(inbytes[14:16], 'big')
            PS = int.from_bytes(inbytes[16:18], 'big')
            vminus15 = int.from_bytes(inbytes[18:20], 'big')
            vref = int.from_bytes(inbytes[20:22], 'big')
            times.append(mytime)
            counts.append(count)
            temps.append(temp)
            v5s.append(v5)
            vminus15s.append(vminus15)
            vrefs.append(vref)
            
            for meas, dch in zip(lmeas, lchs):
                dch['meas'].append(meas)
            
            print (count,
                   mytime,
                   (temp & 0xFFF)/16,
                   '%.4f' %(lmeas[0] * -24.576/65535 + 12.288),
                   '%.4f' %(lmeas[1] * -24.576/65535 + 12.288),
                   '%.4f' %(v5 * 0.1875/1000),
                   '%.4f' %(PS * 0.1875*16.39658/1000),
                   '%.4f' %(vminus15 * 0.1875*-4.6887/1000),
                   '%.4f' %(vref * 0.0625/1000))
    ser.close()
    df1 = pd.DataFrame({'time':times,'test':counts, 'temp':temps,
                         '5V':v5s, '-15V':vminus15s, 'vRef': vrefs})
    df2 = pd.DataFrame({'ch%sc' %i:lchs[i]['meas'] for i in range(number_of_channels)})
    df = pd.concat([df1, df2], axis=1)
    df.to_csv('rawdata/default.csv')

#emulator
'''def sender():

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
    print ('End of sending')'''


class MainApp(MDApp):

    def build(self):
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'LightBlue'
        self.theme_cls.primay_hue = '200'
        self.title = 'Blue Physics v.10.0'
        self.icon = 'images/logoonlyspheretransparent.png'
        self.graphchs = MyGraph()
        self.measlayout = self.root.ids.measurescreenlayout
        self.measlayout.add_widget(self.graphchs)
        
        for dch in lchs:
            self.graphchs.add_plot(dch['plot'])
            
        self.contentsheet = Factory.ContentCustomSheet()


    def start(self):

        global stop_thread
 
        #emulator
        #self.sender_thread = Thread(target=sender)
        #self.sender_thread.daemon = True
        #self.sender_thread.start()
        
        stop_thread = False
        self.root.ids.checkboxlevel1.disabled = True
        self.root.ids.checkboxlevel2.disabled = True
        self.root.ids.checkboxlevel3.disabled = True
        self.root.ids.checkboxlevel4.disabled = True
        self.receiver_thread = Thread(target=receiver)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()
        
        self.event1 = Clock.schedule_interval(self.updategraphs, 0.5)

        #emulator
        #self.ser = Serial('/dev/pts/5', 115200, timeout=1)


    def stop(self):
        #emulator
        global stop_thread
        self.root.ids.checkboxlevel1.disabled = False
        self.root.ids.checkboxlevel2.disabled = False
        self.root.ids.checkboxlevel3.disabled = False
        self.root.ids.checkboxlevel4.disabled = False

        #emulator
        stop_thread = True
        #self.sender_thread.join()
        
        Clock.unschedule(self.event1)
    
        #emulator
        #print('sender_thread kiled')

    def updategraphs(self, dt):
        self.graphchs.xmax = times[-1]/1000000
        self.graphchs.xmin = self.graphchs.xmax - 1
        for dch in lchs:
            pointsnow = [(x/1000000, y * -24.576/65535 + 12.288) for (x,y) in zip(times[-741::30], dch['meas'][-741::30])]
            dch['plot'].points = pointsnow


    def bottomsheet(self):
        self.custom_sheet = MDCustomBottomSheet(screen=self.contentsheet,
                                                radius_from='top')
        self.custom_sheet.open()


    def addremoveplot(self, intext, checkbox, value):
        if value:
            self.graphchs.add_plot(lchs[int(intext[-1])]['plot'])
        else:
            self.graphchs.remove_plot(lchs[int(intext[-1])]['plot'])


    def addremovegraph(self, intext, checkbox, value):
        print (intext, checkbox, value)
        if intext != 'None':
            if value:
                self.measlayout.add_widget(self.graphvolts[intext])
            else:
                self.measlayout.remove_widget(self.graphvolts[intext])


    def callback(self):
        print ('oido')
        
    def onofflevel(self, intext, switch):
        print ('Rango:', intext[-1])
        device = list(serial.tools.list_ports.grep('Adafruit ItsyBitsy M4'))[0].device
        ser = serial.Serial(device, 115200, timeout=1)
        ser.write(('c%s,' %intext[-1]).encode())
        ser.close()



MainApp().run()

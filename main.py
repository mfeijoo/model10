#!/usr/bin/env python3
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivymd.app import MDApp
from kivy.graphics import Line, Rectangle, Color
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
import numpy as np
import pandas as pd


class MyGraph(Graph):


    def __init__(self, *args, **kwargs):
        super(MyGraph, self).__init__(*args, **kwargs)


    def on_touch_down(self, touch):
        super(MyGraph, self).on_touch_down(touch)
        
        if not self.collide_point(*touch.pos):
            return
            
            
        if touch.button == 'left':
            self.origx = touch.x
            self.origy = touch.y - 10
            
            with self.canvas:
                Color(1,0,0,0.5)
                self.rect = Line(rectangle = (self.origx, self.origy, 0, 0))
            
        if touch.button == 'right':
            self.xmax = self.xmaxorig
            self.xmin = self.xminorig
            self.ymax = self.ymaxorig
            self.ymin = self.yminorig
            
        if touch.is_mouse_scrolling:
            currentxdist = self.xmax - self.xmin
            currentydist = self.ymax - self.ymin
            zoom = 0.05
            if touch.button == 'scrolldown':
                self.xmax = self.xmax + currentxdist*zoom
                self.xmin = self.xmin - currentxdist*zoom
                self.ymax = self.ymax + currentydist*zoom
                self.ymin = self.ymin - currentydist*zoom
            if touch.button == 'scrollup':
                self.xmax = self.xmax - currentxdist*zoom
                self.xmin = self.xmin + currentxdist*zoom
                self.ymax = self.ymax - currentydist*zoom
                self.ymin = self.ymin + currentydist*zoom
   
            
    def on_touch_move(self, touch):
        
        if not self.collide_point(*touch.pos):
            return
        
        if touch.button == 'left':
            self.rect.rectangle =  (self.origx, self.origy, touch.x - self.origx, touch.y - self.origy)
        
        
    def on_touch_up(self, touch):
        
        if not self.collide_point(*touch.pos):
            return
        
        if touch.button == 'left':
            self.canvas.remove(self.rect)
            (self.xmin, self.ymin) = self.to_data(self.origx, touch.y)
            (self.xmax, self.ymax) = self.to_data(touch.x, self.origy)




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

#Function to clean up pulses
#Also to add two consecutive pulses
#in case to reseve capacitor
#input a raw data ndarray of times x
#and raw data of ndarray measurements ys
def cleanpulses(x, ys):
        #pulses clean up
        #find ch with maximum
        chwithmax = np.argmax(np.max(ys, axis=0))
        #find pulses
        #Find the maximum value at not pulse (visualizing 1.10)
        maxvalueatnolight = 1.7
        pulses = ys[:,chwithmax] > maxvalueatnolight
        #shift pulses down
        pulsesshift1 = np.append(np.array([False]), pulses[:-1])
        #find where two pulses coincide
        secondcoincides = pulses & pulsesshift1
        #number_of_pulses_coinciding = secondcoincides.sum()
        #Make a copy of the original array of measurements and call it
        #second pulses
        achsc = ys.copy()
        #Put zeros in all values of that copy that don't have a
        #coincide pulse
        achsc[~secondcoincides] = 0
        #Shift that new array to move the values of the second coincides
        #to match the first coincide
        achscs = np.row_stack((achsc[1:], np.zeros(number_of_channels)))
        #sum the second coincide with the first coincide only AND
        #eliminate the second coincides rows. It creates an array of
        #only the pulses and with the two pulses coinciding added
        #added together. This is called a1nc
        achnc = (ys + achscs)[~secondcoincides]
        #Find the maximum value at not pulse (visualizing 1.10)
        #Find wehre we have only pulses
        onlypulses = achnc[:,chwithmax] > maxvalueatnolight
        #We can now calculate the number of pulses
        #number_of_pulses = onlypulses.sum()
        #Now we can find the value before and after each pulse and
        achbeforepulse = np.row_stack((achnc[1:], np.zeros(number_of_channels)))
        achafterpulse = np.row_stack((np.zeros(number_of_channels), achnc[:-1]))
        #We subtract the value of each pulse with the avarge of the value
        #before and after. It will give you the value of the increase of
        #each pulse
        nachnc = np.abs(achnc - (achbeforepulse + achafterpulse)/2)
        #We put zeros in each value that are not pulses
        nachnc[~onlypulses]=0
        #Calculate the totaldoses
        #totaldoses = nachnc.sum() #array
        #Calculate the times without coincidences
        xnc = x[~secondcoincides]
        return xnc, nachnc


def receiver():
    global la
    #da = np.zeros((1, 7+number_of_channels), dtype=int)
    la = []
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
            v5 = int.from_bytes(inbytes[10:12], 'big')
            PS = int.from_bytes(inbytes[12:14], 'big')
            vminus15 = int.from_bytes(inbytes[14:16], 'big')
            vref = int.from_bytes(inbytes[16:18], 'big')
            lmeas = [int.from_bytes(inbytes[18+2*i:20+2*i], 'big') for i in range(number_of_channels)]
            
            la.append([count, mytime, temp, v5, PS, vminus15, vref] + lmeas)
            #atoadd = np.array([[count, mytime, temp, v5, PS, vminus15, vref] + lmeas])
            #da = np.append(da, atoadd, axis=0)
            
            
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
    df = pd.DataFrame(la, columns=['counts', 'time', 'temp', '5V', 'PS', '-15V', 'ref'] + ['ch%sc' %i for i in range(number_of_channels)])
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
        self.graphvolts = {'Temp': MyGraph(ylabel = 'Temp. (C)',
                                           ymin = 22,
                                           ymax = 30),
                           'PS': MyGraph(ylabel='PS (V)',
                                         ymin=50,
                                         ymax=65),
                           '5V': MyGraph(ylabel='5V (V)',
                                         ymin=4,
                                         ymax=6),
                           '-15V': MyGraph(ylabel='-15V (V)',
                                           ymin=-16,
                                           ymax=-14),
                           'refV': MyGraph(ylabel='ref. (V)',
                                           ymin=0,
                                           ymax=2)}
        self.measlayout = self.root.ids.measurescreenlayout
        self.measlayout.add_widget(self.graphchs)
        # Lista ch plots
        self.lchplots = [MeshLinePlot(color=get_color_from_hex(mcolors[i])) for i in range(number_of_channels)]
        for plot in self.lchplots:
            self.graphchs.add_plot(plot)
        self.tempplot = MeshLinePlot(color=get_color_from_hex(mcolors[8]))
        self.PSplot = MeshLinePlot(color=get_color_from_hex(mcolors[1]))
        self.v5Vplot = MeshLinePlot(color=get_color_from_hex(mcolors[4]))
        self.minus15Vplot = MeshLinePlot(color=get_color_from_hex(mcolors[3]))
        self.refVplot = MeshLinePlot(color=get_color_from_hex(mcolors[2]))
        self.graphvolts['Temp'].add_plot(self.tempplot)
        self.graphvolts['PS'].add_plot(self.PSplot)
        self.graphvolts['5V'].add_plot(self.v5Vplot)
        self.graphvolts['-15V'].add_plot(self.minus15Vplot)
        self.graphvolts['refV'].add_plot(self.refVplot)
            
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
        time.sleep(0.5)
        
            
        self.plotpulses = self.contentsheet.ids.mypulsescheckbox.active
        
        if (not self.plotpulses):
            self.graphchs.xmin = 0
            self.graphchs.xmax = 60
            self.graphchs.x_ticks_major = 10
            self.graphchs.x_ticks_minor = 5
            self.graphchs.ymin = -10
            self.graphchs.ymax = 400
            self.graphchs.y_ticks_major = 100
            self.graphchs.y_ticks_minor = 10
            self.acum = np.zeros((1, 1+number_of_channels))
            self.event1 = Clock.schedule_interval(self.updategraphs, 0.3)
        else:
            self.graphchs.xmin = 0
            self.graphchs.xmax = 0.5
            self.graphchs.ymin = -6
            self.graphchs.ymax = 6
            self.graphchs.y_ticks_major = 1
            self.graphchs.y_ticks_minor = 10
            self.plotcounter = 0
            self.event1 = Clock.schedule_interval(self.updategraphpulses, 0.3)

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
        
        self.graphchs.xmaxorig = self.graphchs.xmax
        self.graphchs.xminorig = self.graphchs.xmin
        self.graphchs.ymaxorig = self.graphchs.ymax
        self.graphchs.yminorig = self.graphchs.ymin

        

    def updategraphs(self, dt):
        an = np.array(la[-429:])
        means = an[:,1:7].mean()
        x = an[:,1]/1000000
        ys = an[:,7:] * -24.576/65535 + 12.288
        xn, ysn = cleanpulses(x, ys)
        tnow = x[0]
        if self.graphchs.xmax < tnow:
            self.graphchs.xmax = float(tnow)
            #self.graphchs.xmin = float(timescumnow) - 60
        #datacum = ys.sum(axis=0)
        datacum = ysn.sum(axis=0)
        datatoadd = np.append(tnow, datacum)
        print(datatoadd)
        self.acum = np.vstack((self.acum, datatoadd))
        self.lchplots[0].points = self.acum[1:,[0,1]]
        self.lchplots[1].points = self.acum[1:,[0,2]]


    def updategraphpulses(self, dt):
        an = np.array(la[-429:])
        x = (an[:,0]/1000000)
        PS = an[:,4] * 0.1875*16.39658/1000
        ys = an[:,7:] * -24.576/65535 + 12.288
        xnc, nachnc = cleanpulses(x, ys)
        ann = np.column_stack((x, ys))
        #ann = np.column_stack((xnc, nachnc))
        self.graphchs.xmin = float(x[0])
        self.graphchs.xmax = float(x[-1])
        #self.lchplots[0].points = ann[:,[0,1]]
        #self.lchplots[1].points = ann[:,[0,2]]
        #print(PS[0])

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
        #print (intext, checkbox, value)
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

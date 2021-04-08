#!/usr/bin/env python3
#import os
#os.environ["KCFG_KIVY_LOG_LEVEL"] = 'error'
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
import numpy as np
import pandas as pd


class MyGraph(Graph):


    def __init__(self, *args, **kwargs):
        super(MyGraph, self).__init__(*args, **kwargs)
        self.xmaxorig = self.xmax
        self.xminorig = self.xmin
        self.ymaxorig = self.ymax
        self.yminorig = self.ymin
        self.font_size = '10sp'
        self.precision = '%.3f'


    def on_touch_down(self, touch):
        
        if not self.collide_point(*touch.pos):
            return
            
            
        if touch.button == 'left':
            touch.grab(self)
            self.origx = touch.x
            self.origy = touch.y
            (self.xminnow, self.ymaxnow) = self.to_data(touch.x, touch.y)
            #print(self.to_data(self.origx, self.origy))
            
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
            if touch.button == 'scrollup':
                self.xmax = self.xmax + currentxdist*zoom
                self.xmin = self.xmin - currentxdist*zoom
                self.ymax = self.ymax + currentydist*zoom
                self.ymin = self.ymin - currentydist*zoom
            if touch.button == 'scrolldown':
                self.xmax = self.xmax - currentxdist*zoom
                self.xmin = self.xmin + currentxdist*zoom
                self.ymax = self.ymax - currentydist*zoom
                self.ymin = self.ymin + currentydist*zoom
        return True
   
            
    def on_touch_move(self, touch):
        
        if not self.collide_point(*touch.pos):
            return
        
        if touch.button == 'left':
            self.rect.rectangle =  (self.origx, self.origy, touch.x - self.origx, touch.y - self.origy)
        
        
    def on_touch_up(self, touch):
        
        if touch.grab_current is self:
        
            if touch.button == 'left':
                (self. xmaxnow, self.yminnow) = self.to_data(touch.x, touch.y)
                self.xmin = self.xminnow
                self.xmax = self.xmaxnow
                self.ymin = self.yminnow
                self.ymax = self.ymaxnow
                self.canvas.remove(self.rect)
                #print(self.xmaxnow, self.yminnow)
                #print ('xmin, xmax, ymin, ymax', self.xmin, self.xmax, self.ymin, self.ymax)
            touch.ungrab(self)
            return True




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


arrmultip = np.array([1,
                      1/1000000,
                      1,
                      0.1875/1000,
                      0.1875*16.4372/1000,
                      0.1875*-4.6887/1000,
                      0.1875/1000,
                      -24.576/65535,
                      -24.576/65535])
arrsum = np.array([0]*7+[12.288]*number_of_channels)

#Function to clean up pulses
#Also to add two consecutive pulses
#in case to reseve capacitor
#input a raw data ndarray of times x
#and raw data of ndarray measurements ys
def cleanpulses(arr, maxvalueatnolight):
        x = arr[:,:7]
        ys = arr[:,7:]
        #pulses clean up
        #find ch with maximum
        chwithmax = np.argmax(np.max(ys, axis=0))
        #find pulses
        #Find the maximum value at not pulse (visualizing 1.10)
        #maxvalueatnolight = 1.7
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
        return np.column_stack((xnc, nachnc))


def receiver():
    da = b''
    count = 0
    device = list(serial.tools.list_ports.grep('Adafruit ItsyBitsy M4'))[0].device
    ser = serial.Serial(device, 57600, xonxoff=False, timeout=3)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.write(b't') #restart counting

    while not(stop_thread):
        if ser.in_waiting:
            inbytes = ser.read(ser.in_waiting)
            print (count)
            da += inbytes
            count += 1
            '''count = int.from_bytes(inbytes[:4], 'big')
            inbytes = ser.read(22)
            print(ser.in_waiting)
            #line = ser.readline()
            count = int.from_bytes(inbytes[:4], 'big')
            mytime = int.from_bytes(inbytes[4:8], 'big')
            temp = int.from_bytes(inbytes[8:10], 'big')
            v5 = int.from_bytes(inbytes[10:12], 'big')
            PS = int.from_bytes(inbytes[12:14], 'big')
            vminus15 = int.from_bytes(inbytes[14:16], 'big')
            vref = int.from_bytes(inbytes[16:18], 'big')
            lmeas = [int.from_bytes(inbytes[18+2*i:20+2*i], 'big') for i in range(number_of_channels)]
            
            la.append([count, mytime, temp, v5, PS, vminus15, vref] + lmeas)
            #atoadd = np.array([[count, mytime, temp, v5, PS, vminus15, vref] + lmeas])'''
            #da = np.append(da, atoadd, axis=0)

            '''print (count,
                   mytime,
                   (temp & 0xFFF)/16,
                   '%.4f' %(v5 * 0.1875/1000),
                   '%.4f' %(PS * 0.1875*16.4372/1000),
                   '%.4f' %(vminus15 * 0.1875*-4.6887/1000),
                   '%.4f' %(vref * 0.1875/1000),
                   '%.4f' %(lmeas[0] * -24.576/65535 + 12.288),
                   '%.4f' %(lmeas[1] * -24.576/65535 + 12.288))'''

    #ser.close()
    #df = pd.DataFrame(la, columns=['counts', 'time', 'ctemp', 'c5V', 'cPS', 'cminus15V', 'cref'] + ['ch%sc' %i for i in range(number_of_channels)])
    #df.to_csv('rawdata/default.csv')
    aall = np.ndarray((len(da)//22,22), np.int8, da)
    np.savetxt('rawdata/default.csv', aall, delimiter=',')
    print (aall[-1])
    print ('shape', aall.shape)
    

#emulator
'''def sender():

    global stop_thread
    myfile = open('rawdata/emulatormeasurmentslong.csv')
    lines = myfile.readlines()
    myfile.close()
    serial_sender = Serial('/dev/pts/2', 57600, timeout=1)
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
        self.graphchs = MyGraph(ylabel = 'Volts (V)')
        self.graphtemp = MyGraph(ylabel = 'Temp. (C)',
                                 ymin = 24,
                                 ymax = 26,
                                 y_ticks_major = 0.1,
                                 y_ticks_minor = 5)
        self.graphPS = MyGraph(ylabel='PS (V)',
                               ymin = 56.55,
                               ymax = 56.75,
                               y_ticks_major = 0.05,
                               y_ticks_minor = 5)
        self.graph5V = MyGraph(ylabel='5V (V)')
        self.graphminus15V = MyGraph(ylabel='-15V (V)')
        self.graphrefV = MyGraph(ylabel='ref. (V)',
                                 ymin = 1.27,
                                 ymax = 1.26,
                                 y_ticks_major = 0.01,
                                 y_ticks_minor = 5)
        self.measlayout = self.root.ids.measurescreenlayout
        self.measlayout.add_widget(self.graphchs)
        #List of all the graphs
        #useful to change xmin xmax ymin ymax all at once
        self.allgraphs = [self.graphtemp, self.graph5V, self.graphPS, self.graphminus15V, self.graphrefV, self.graphchs]
        #Dictionary with all the graphs voltages
        #needed for switching graphs
        self.graphvolts = {'Temp':self.graphtemp, 'PS':self.graphPS,
                           'refV':self.graphrefV, '-15V':self.graphminus15V,
                           '5V': self.graph5V}
        # Lista ch plots
        self.lchplots = [MeshLinePlot(color=get_color_from_hex(mcolors[i])) for i in range(number_of_channels)]
        for plot in self.lchplots:
            self.graphchs.add_plot(plot)
        self.tempplot = MeshLinePlot(color=get_color_from_hex(mcolors[8]))
        self.PSplot = MeshLinePlot(color=get_color_from_hex(mcolors[1]))
        self.v5Vplot = MeshLinePlot(color=get_color_from_hex(mcolors[4]))
        self.minus15Vplot = MeshLinePlot(color=get_color_from_hex(mcolors[3]))
        self.refVplot = MeshLinePlot(color=get_color_from_hex(mcolors[2]))
        #Lista al plots
        self.allplots = [self.tempplot, self.v5Vplot, self.PSplot, self.minus15Vplot, self.refVplot] + self.lchplots
        self.graphtemp.add_plot(self.tempplot)
        self.graphPS.add_plot(self.PSplot)
        self.graph5V.add_plot(self.v5Vplot)
        self.graphminus15V.add_plot(self.minus15Vplot)
        self.graphrefV.add_plot(self.refVplot)

        self.contentsheet = Factory.ContentCustomSheet()
        

#This is a fuction to be executed before standard measuring
#to calculate baselines and initial margins of graphs
#It is supposed to be excuted before light signal or Linac is received
    def beforemeasuring(self):
        labefore = []
        device = list(serial.tools.list_ports.grep('Adafruit ItsyBitsy M4'))[0].device
        serbefore = serial.Serial(device, 57600, timeout=1)
        serbefore.reset_input_buffer()
        serbefore.reset_output_buffer()
        serbefore.write(b't')
        
        while len(labefore) < 429 * 3:
            if serbefore.in_waiting:
                inbytes = serbefore.read(22)
                count = int.from_bytes(inbytes[:4], 'big')
                mytime = int.from_bytes(inbytes[4:8], 'big')
                temp = int.from_bytes(inbytes[8:10], 'big')
                v5 = int.from_bytes(inbytes[10:12], 'big')
                PS = int.from_bytes(inbytes[12:14], 'big')
                vminus15 = int.from_bytes(inbytes[14:16], 'big')
                vref = int.from_bytes(inbytes[16:18], 'big')
                lmeas = [int.from_bytes(inbytes[18+2*i:20+2*i], 'big') for i in range(number_of_channels)]
                
                labefore.append([count, mytime, temp, v5, PS, vminus15, vref] + lmeas)
        
        serbefore.close()
        listofchsc = ['ch%sc' %i for i in range(number_of_channels)]
        listofchsv = ['ch%sV' %i for i in range(number_of_channels)]
        dfb = pd.DataFrame(labefore, columns=['counts', 'time', 'temp', 'c5V', 'cPS', 'cminus15V', 'cref'] + listofchsc)
        dfb['tempC'] = (dfb.temp & 0xFFF) / 16
        dfb[listofchsv] = dfb.loc[:,listofchsc] * -24.576 / 65535 + 12.288
        dfb['v5V'] = dfb.c5V * 0.1875 / 1000
        dfb['vPS'] = dfb.cPS * 0.1875 * 16.39658 / 1000
        dfb['vminus15V'] = dfb.cminus15V * 0.1875 * -4.6887 / 1000
        dfb['vref'] = dfb.cref * 0.0625 / 1000
        
        #set the maximum signal of dark current without light
        #to findout the pulses
        #max value is going to be set up with a buffer of 5%
        maxchs = dfb.loc[10:,listofchsv].max().max()
        self.maxvalueatnolight = maxchs + 0.05 * abs(maxchs)
        
        #new zerovalue for channels at not ligth
        #This will be used to reset the zero value of the measurements
        self.newminvalueatnolight = dfb.loc[10:,listofchsv].min().min()
        
        #set the maximuns and minimuns of graphs
        self.graphchs.ymax = float(maxchs + 0.005 * abs(maxchs))
        minchs = dfb.loc[10:,listofchsv].min().min()
        self.graphchs.ymin = float(minchs - 0.005 * abs(minchs))
        maxtemp = dfb.loc[10:,'tempC'].max()
        self.graphtemp.ymax = float(maxtemp + 0.005 * abs(maxtemp))
        mintemp = dfb.loc[10:,'tempC'].min()
        self.graphtemp.ymin = float(mintemp - 0.005 * abs(mintemp))
        maxPS = dfb.loc[10:,'vPS'].max()
        self.graphPS.ymax = float(maxPS + 0.003 * abs(maxPS))
        minPS = dfb.loc[10:,'vPS'].min()
        self.graphPS.ymin = float(minPS + 0.001 * abs(minPS))
        max5V = dfb.loc[10:,'v5V'].max()
        self.graph5V.ymax = float(max5V + 0.005 * abs(max5V))
        min5V = dfb.loc[10:,'v5V'].min()
        self.graph5V.ymin = float(min5V - 0.005 * abs(min5V))
        maxminus15V = dfb.loc[10:,'vminus15V'].max()
        self.graphminus15V.ymax = float(maxminus15V + 0.005 * abs(maxminus15V))
        minminus15V = dfb.loc[10:,'vminus15V'].min()
        self.graphminus15V.ymin = float(minminus15V - 0.005 * abs(minminus15V))
        #maxrefV = dfb.loc[10:,'vref'].max()
        #self.graphrefV.ymax = float(maxrefV + 0.005 * abs(maxrefV))
        #minrefV = dfb.loc[10:,'vref'].min()
        #self.graphrefV.ymin = float(minrefV - 0.005 * abs(minrefV))
        
        

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
        
        #Routine to execute before measuring
        #This is to calculate base lines and initial plot margins
        self.beforemeasuring()
        
        self.receiver_thread = Thread(target=receiver)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()
        time.sleep(0.5)
        
            
        self.plotpulses = self.contentsheet.ids.mypulsescheckbox.active
        
        if (not self.plotpulses):
            for graph in self.allgraphs:
                graph.xmin = 0
                graph.xmax = 60
            self.graphchs.ymin = -10
            self.graphchs.ymax = 1000
            self.acum = np.zeros((1, 7+number_of_channels))
            #self.event1 = Clock.schedule_interval(self.updategraphs, 0.3)
        else:
            self.graphchs.ymin = -12
            self.graphchs.ymax = 12
            self.plotcounter = 0
            #self.event1 = Clock.schedule_interval(self.updategraphpulses, 0.3)

        #emulator
        #self.ser = Serial('/dev/pts/5', 57600, timeout=1)


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
        
        #Clock.unschedule(self.event1)
    
        #emulator
        #print('sender_thread kiled')
        
        for graph in self.allgraphs:
            graph.xmaxorig = graph.xmax
            graph.xminorig = graph.xmin
            graph.ymaxorig = graph.ymax
            graph.yminorig = graph.ymin

        

    def updategraphs(self, dt):
        an = np.array(la[-300:])
        tempnow = ((an[:,2] & 0xFFF) / 16).mean()
        anv = an * arrmultip + arrsum
        if self.contentsheet.ids.mycleanpulses.active:
            anv = cleanpulses(anv, self.maxvalueatnolight)
        countnow = anv[0,0]
        tnow = anv[0,1]
        datacum = anv[:,7:].sum(axis=0)
        voltcum = anv[:,3:7].mean(axis=0)
        datatoadd = np.hstack((countnow, tnow, tempnow, voltcum, datacum))
        self.acum = np.vstack((self.acum, datatoadd))
        if tnow > 60:
            for graph in self.allgraphs:
                graph.xmax = float(tnow) 
        self.tempplot.points = self.acum[1:, [1,2]]
        self.v5Vplot.points = self.acum[1:, [1,3]]
        self.PSplot.points = self.acum[1:, [1,4]]
        self.minus15Vplot.points = self.acum[1:, [1,5]]
        self.refVplot.points = self.acum[1:, [1,6]]
        for i in range(number_of_channels):
            self.lchplots[i].points = self.acum[1:,[1,7+i]]

    def updategraphpulses(self, dt):
        an = np.array(la[-300:])
        anv = an * arrmultip + arrsum
        if self.contentsheet.ids.mycleanpulses.active:
            anv = cleanpulses(anv, self.maxvalueatnolight)
        for graph in self.allgraphs:
            graph.xmin = float(anv[0,1])
            graph.xmax = float(anv[-1,1])
        self.tempplot.points = (an[:, [1,2]] & 0xFFF) / 16
        self.v5Vplot.points = anv[:, [1,3]]
        self.PSplot.points = anv[:, [1,4]]
        self.minus15Vplot.points = anv[:, [1,5]]
        self.refVplot.points = anv[:, [1,6]]
        for i in range(number_of_channels):
            self.lchplots[i].points = anv[:,[1,7+i]]
        #print ('Last measurement: ', anv[-1,:].round(3))
        print('PS =',anv[:,4].mean().round(3), 'V')
        #print ('max value at no light: ', self.maxvalueatnolight)

    def bottomsheet(self):
        self.custom_sheet = MDCustomBottomSheet(screen=self.contentsheet,
                                                radius_from='top')
        self.custom_sheet.open()


    def addremoveplot(self, intext, checkbox, value):
        if value:
            self.graphchs.add_plot(self.lchplots[int(intext[-1])])
        else:
            self.graphchs.remove_plot(self.lchplots[int(intext[-1])])


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
        ser = serial.Serial(device, 57600, timeout=1)
        ser.write(('c%s,' %intext[-1]).encode())
        ser.close()



MainApp().run()

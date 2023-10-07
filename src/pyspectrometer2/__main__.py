#!/usr/bin/env python3

'''
PySpectrometer2 Les Wright 2022
https://www.youtube.com/leslaboratory
https://github.com/leswright1977

This project is a follow on from: https://github.com/leswright1977/PySpectrometer

This is a more advanced, but more flexible version of the original program. Tk
Has been dropped as the GUI to allow fullscreen mode on Raspberry Pi systems and
the iterface is designed to fit 800*480 screens, which seem to be a common
resolutin for RPi LCD's, paving the way for the creation of a stand alone
benchtop instrument.

Whats new:
Higher resolution (800px wide graph)
3 row pixel averaging of sensor data
Fullscreen option for the Spectrometer graph
3rd order polymonial fit of calibration data for accurate measurement.
Improved graph labelling
Labelled measurement cursors
Optional waterfall display for recording spectra changes over time.
Key Bindings for all operations

All old features have been kept, including peak hold, peak detect, Savitsky
Golay filter, and the ability to save graphs as png and data as CSV.

For instructions please consult the readme!

'''


import cv2
import numpy as np

from .exceptions import CalibrationError

from .spectrometer import Spectrometer
from .interactivity import SpectrometerInteractivity
from .specFunctions import wavelength_to_rgb,savitzky_golay,peakIndexes
from . import cli,record,ui,video

args = cli.args()
font=cv2.FONT_HERSHEY_SIMPLEX

capture = video.Capture.initialize(args.device,args.width,args.height,args.fps)
calibration = record.Calibration(capture.width)
print(capture)
spectrometer = Spectrometer(calibration)

class App():
    def __init__(self,s: Spectrometer):
        self.s = s
        self.overlay: ui.Overlay = None
        self.waterfall = np.zeros([s.graphHeight,capture.width,3],dtype=np.uint8)
        self.waterfall.fill(0) #fill black


    def update_spectrum_window(self, frame, saveMsg):
        #blank image for Graph
        graph = np.zeros([self.s.graphHeight,capture.width,3],dtype=np.uint8)
        graph.fill(255) #fill white

        #Display a graticule calibrated with cal data
        textoffset = 12
        #vertial lines every whole 10nm
        for position in self.s.tens:
            cv2.line(graph,(position,15),(position,self.s.graphHeight),(200,200,200),1)

        #vertical lines every whole 50nm
        for positiondata in self.s.fifties:
            cv2.line(graph,(positiondata[0],15),(positiondata[0],self.s.graphHeight),(0,0,0),1)
            cv2.putText(graph,str(positiondata[1])+'nm',(positiondata[0]-textoffset,12),font,0.4,(0,0,0),1, cv2.LINE_AA)

        #horizontal lines
        for i in range (self.s.graphHeight):
            if i>=64:
                if i%64==0: #suppress the first line then draw the rest...
                    cv2.line(graph,(0,i),(capture.width,i),(100,100,100),1)

        #Now process the intensity data and display it
        #intensity = []

        cropped = capture.cropped_preview(frame)
        bwimage = cv2.cvtColor(cropped,cv2.COLOR_BGR2GRAY)
        sample_count = 3
        self.s.sample_intensity(bwimage, sample_count=sample_count)
        #Draw the intensity data :-)
        #first filter if not holding peaks!

        if not self.s.holdpeaks:
            self.s.intensity = savitzky_golay(self.s.intensity,17,self.s.savpoly)
            self.s.intensity = np.array(self.s.intensity)
            self.s.intensity = self.s.intensity.astype(int)
            holdmsg = "Holdpeaks OFF"
        else:
            holdmsg = "Holdpeaks ON"


        #now draw the intensity data....
        index=0
        for i in self.s.intensity:
            rgb = wavelength_to_rgb(round(self.s.calibration.wavelengthData[index]))#derive the color from the wvalenthData array
            r = rgb[0]
            g = rgb[1]
            b = rgb[2]
            #or some reason origin is top left.
            cv2.line(graph, (index,self.s.graphHeight), (index,self.s.graphHeight-i), (b,g,r), 1)
            cv2.line(graph, (index,319-i), (index,self.s.graphHeight-i), (0,0,0), 1,cv2.LINE_AA)
            index+=1


        #find peaks and label them
        textoffset = 12
        thresh = int(self.s.thresh) #make sure the data is int.
        indexes = peakIndexes(self.s.intensity, thres=thresh/max(self.s.intensity), min_dist=self.s.mindist)
        #print(indexes)
        for i in indexes:
            height = self.s.intensity[i]
            height = 310-height
            wavelength = round(self.s.calibration.wavelengthData[i],1)
            cv2.rectangle(graph,((i-textoffset)-2,height),((i-textoffset)+60,height-15),(0,255,255),-1)
            cv2.rectangle(graph,((i-textoffset)-2,height),((i-textoffset)+60,height-15),(0,0,0),1)
            cv2.putText(graph,str(wavelength)+'nm',(i-textoffset,height-3),font,0.4,(0,0,0),1, cv2.LINE_AA)
            #flagpoles
            cv2.line(graph,(i,height),(i,height+10),(0,0,0),1)

        #stack the images and display the spectrum
        self.s.spectrum_vertical = np.vstack((ui.background,cropped, graph))

        self.overlay = ui.Overlay(self.s.spectrum_vertical,
                            capture.width,
                            message_height=self.s.messageHeight,
                            preview_height=self.s.previewHeight)

        #listen for click on plot window
        cv2.setMouseCallback(self.s.spectrograph_title,self.overlay.handle_mouse)

        self.overlay.draw_divisions()
        self.overlay.draw_sample_boundry(self.s.sample_start,self.s.sample_stop)
        calmsg1, calmsg3 = self.s.calibration.status()
        self.overlay.label('cal1',calmsg1)
        self.overlay.label('cal3',calmsg3)
        self.overlay.label('fps', f"Framerate: {capture.fps}")
        self.overlay.label('save', saveMsg)
        self.overlay.label('hold', holdmsg)
        self.overlay.label('savpoly', f"Savgol Filter: {self.s.savpoly}")
        self.overlay.label('label_width', f"Label Peak Width: {self.s.mindist}")
        self.overlay.label('label_threshold', f"Label Threshold: {thresh}")

        if self.s.measure:
            self.overlay.show_cursor()
            self.overlay.show_measure(wavelengthData=self.s.calibration.wavelengthData)
        elif self.s.recPixels:
            self.overlay.show_cursor()
            self.overlay.show_measure()
            self.overlay.show_calibration_choices()

        cv2.imshow(self.s.spectrograph_title,self.s.spectrum_vertical)

    def update_waterfall_window(self,frame):
        #data is smoothed at this point!!!!!!
        #create an empty array for the data
        wdata = np.zeros([1,capture.width,3],dtype=np.uint8)
        index=0
        for i in self.s.intensity:
            rgb = wavelength_to_rgb(round(self.s.calibration.wavelengthData[index]))#derive the color from the wavelenthData array
            luminosity = self.s.intensity[index]/255
            b = int(round(rgb[0]*luminosity))
            g = int(round(rgb[1]*luminosity))
            r = int(round(rgb[2]*luminosity))
            #print(b,g,r)
            #wdata[0,index]=(r,g,b) #fix me!!! how do we deal with this data??
            wdata[0,index]=(r,g,b)
            index+=1
        self.waterfall = np.insert(self.waterfall, 0, wdata, axis=0) #insert line to beginning of array
        self.waterfall = self.waterfall[:-1].copy() #remove last element from array

        hsv = cv2.cvtColor(self.waterfall, cv2.COLOR_BGR2HSV)

        #stack the images and display the waterfall
        cropped = capture.cropped_preview(frame)
        self.s.waterfall_vertical = np.vstack((ui.background,cropped, self.waterfall))
        #dividing lines...
        cv2.line(self.s.waterfall_vertical,(0,80),(capture.width,80),(255,255,255),1)
        cv2.line(self.s.waterfall_vertical,(0,160),(capture.width,160),(255,255,255),1)
        #Draw this stuff over the top of the image!
        #Display a graticule calibrated with cal data
        textoffset = 12

        #vertical lines every whole 50nm
        for positiondata in self.s.fifties:
            for i in range(162,480):
                if i%20 == 0:
                    cv2.line(self.s.waterfall_vertical,(positiondata[0],i),(positiondata[0],i+1),(0,0,0),2)
                    cv2.line(self.s.waterfall_vertical,(positiondata[0],i),(positiondata[0],i+1),(255,255,255),1)
            cv2.putText(self.s.waterfall_vertical,str(positiondata[1])+'nm',(positiondata[0]-textoffset,475),font,0.4,(0,0,0),2, cv2.LINE_AA)
            cv2.putText(self.s.waterfall_vertical,str(positiondata[1])+'nm',(positiondata[0]-textoffset,475),font,0.4,(255,255,255),1, cv2.LINE_AA)


        #cv2.putText(self.s.waterfall_vertical,calmsg1,(490,15),font,0.4,(0,255,255),1, cv2.LINE_AA)
        #cv2.putText(self.s.waterfall_vertical,calmsg3,(490,51),font,0.4,(0,255,255),1, cv2.LINE_AA)
        #cv2.putText(self.s.waterfall_vertical,saveMsg,(490,69),font,0.4,(0,255,255),1, cv2.LINE_AA)
        #cv2.putText(self.s.waterfall_vertical,holdmsg,(640,15),font,0.4,(0,255,255),1, cv2.LINE_AA)

        cv2.imshow(self.s.waterfall_title,self.s.waterfall_vertical)





def main(s: Spectrometer):
    if args.fullscreen:
        print("Fullscreen Spectrometer enabled")
    if args.waterfall:
        print("Waterfall display enabled")

    s.intensity = [0] * capture.width #array for intensity data...full of zeroes


    if args.waterfall:
        #waterfall first so spectrum is on top
        cv2.namedWindow(s.waterfall_title,cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow(s.waterfall_title,capture.width,s.stackHeight)
        cv2.moveWindow(s.waterfall_title,200,200);

    if args.fullscreen:
        cv2.namedWindow(s.spectrograph_title,cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(s.spectrograph_title,cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    else:
        cv2.namedWindow(s.spectrograph_title,cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow(s.spectrograph_title,capture.width,s.stackHeight)
        cv2.moveWindow(s.spectrograph_title,0,0);

    saveMsg = "No data saved"

    app = App(s)
    while(capture.isOpened()):
        # Capture frame-by-frame
        success, frame = capture.read()
        if not success:
            break

        if args.flip:
            FLIP_ABOUT_X_AXIS = 0
            FLIP_ABOUT_Y_AXIS = 1
            frame = cv2.flip(frame,flipCode=FLIP_ABOUT_Y_AXIS)

        app.update_spectrum_window(frame=frame,saveMsg=saveMsg)

        if args.waterfall:
            app.update_waterfall_window(frame=frame)


        keyPress = cv2.waitKey(1)
        if keyPress == ord('q'):
            break
        si = SpectrometerInteractivity(spectrometer,capture,app.overlay)
        si.handle_keypress(keyPress,args)

        #https://stackoverflow.com/a/45564409
        #handle window close
        if cv2.getWindowProperty(s.spectrograph_title,cv2.WND_PROP_VISIBLE) < 1:
            break
        if cv2.getWindowProperty(s.waterfall_title,cv2.WND_PROP_VISIBLE) < 1:
            break


    #Everything done, release the vid
    capture.release()

    cv2.destroyAllWindows()


main(s=spectrometer)
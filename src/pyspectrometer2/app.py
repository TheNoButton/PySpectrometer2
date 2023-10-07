from pyspectrometer2 import ui, video
from pyspectrometer2.interactivity import SpectrometerInteractivity
from pyspectrometer2.specFunctions import peakIndexes, savitzky_golay, wavelength_to_rgb
from pyspectrometer2.spectrometer import Spectrometer

import cv2
import numpy as np


class App:
    #window
    graphHeight: int = 320
    previewHeight: int = 80
    messageHeight: int = 80
    spectrograph_title: str = 'PySpectrometer 2 - Spectrograph'
    waterfall_title: str = 'PySpectrometer 2 - Waterfall'
    font=cv2.FONT_HERSHEY_SIMPLEX


    def __init__(self,s: Spectrometer, capture: video.Capture, fullscreen=False, waterfall=False, flip=False):
        self.s = s
        self.overlay: ui.Overlay = None
        self.history = np.zeros([self.graphHeight,s.calibration.width,3],dtype=np.uint8)
        self.history.fill(0) #fill black
        self.capture = capture
        self.saveMsg = "No saves"

        #preferences
        self.fullscreen = fullscreen
        self.waterfall = waterfall
        self.flip = flip

        #modes and views
        self.holdpeaks: bool = False #are we holding peaks?
        self.measure: bool = False #are we measuring?
        self.recPixels: bool = False #are we measuring pixels and recording clicks?

    def run(self):
        self.setup_windows()
        self.update_windows()

    def close_event(self):
        titles = [self.spectrograph_title]
        if self.waterfall:
            titles.append(self.waterfall_title)
        for title in titles:
            if cv2.getWindowProperty(title,cv2.WND_PROP_VISIBLE) < 1:
                return True
        return False


    @property
    def stackHeight(self):
       #height of the displayed CV window
       return self.graphHeight+self.previewHeight+self.messageHeight

    def update_windows(self):
        while(self.capture.isOpened()):
            # Capture frame-by-frame
            success, frame = self.capture.read()
            if not success:
                break

            if self.flip:
                FLIP_ABOUT_X_AXIS = 0
                FLIP_ABOUT_Y_AXIS = 1
                frame = cv2.flip(frame,flipCode=FLIP_ABOUT_Y_AXIS)

            self.update_spectrum_window(frame=frame)

            if self.waterfall:
                self.update_waterfall_window(frame=frame)


            keyPress = cv2.waitKey(1)
            if keyPress == ord('q'):
                break
            if self.close_event():
                break
            si = SpectrometerInteractivity(self)
            si.handle_keypress(keyPress)


        #Everything done, release the vid
        self.capture.release()
        cv2.destroyAllWindows()

    def setup_windows(self):
        if self.waterfall:
            #waterfall first so spectrum is on top
            cv2.namedWindow(self.waterfall_title,cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow(self.waterfall_title,self.capture.width,self.stackHeight)
            cv2.moveWindow(self.waterfall_title,200,200)

        if self.fullscreen:
            cv2.namedWindow(self.spectrograph_title,cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(self.spectrograph_title,cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
        else:
            cv2.namedWindow(self.spectrograph_title,cv2.WINDOW_GUI_NORMAL)
            cv2.resizeWindow(self.spectrograph_title,self.capture.width,self.stackHeight)
            cv2.moveWindow(self.spectrograph_title,0,0)


    def update_spectrum_window(self, frame):
        #blank image for Graph
        graph = np.zeros([self.graphHeight,self.capture.width,3],dtype=np.uint8)
        graph.fill(255) #fill white

        #Display a graticule calibrated with cal data
        textoffset = 12
        #vertial lines every whole 10nm
        for position in self.s.tens:
            cv2.line(graph,(position,15),(position,self.graphHeight),(200,200,200),1)

        #vertical lines every whole 50nm
        for positiondata in self.s.fifties:
            cv2.line(graph,(positiondata[0],15),(positiondata[0],self.graphHeight),(0,0,0),1)
            cv2.putText(graph,str(positiondata[1])+'nm',(positiondata[0]-textoffset,12),self.font,0.4,(0,0,0),1, cv2.LINE_AA)

        #horizontal lines
        for i in range (self.graphHeight):
            if i>=64:
                if i%64==0: #suppress the first line then draw the rest...
                    cv2.line(graph,(0,i),(self.capture.width,i),(100,100,100),1)

        #Now process the intensity data and display it
        #intensity = []

        cropped = self.capture.cropped_preview(frame)
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
            cv2.line(graph, (index,self.graphHeight), (index,self.graphHeight-i), (b,g,r), 1)
            cv2.line(graph, (index,319-i), (index,self.graphHeight-i), (0,0,0), 1,cv2.LINE_AA)
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
            cv2.putText(graph,str(wavelength)+'nm',(i-textoffset,height-3),self.font,0.4,(0,0,0),1, cv2.LINE_AA)
            #flagpoles
            cv2.line(graph,(i,height),(i,height+10),(0,0,0),1)

        #stack the images and display the spectrum
        self.s.spectrum_vertical = np.vstack((ui.background,cropped, graph))

        self.overlay = ui.Overlay(self.s.spectrum_vertical,
                            self.capture.width,
                            message_height=self.messageHeight,
                            preview_height=self.previewHeight)

        #listen for click on plot window
        cv2.setMouseCallback(self.spectrograph_title,self.overlay.handle_mouse)

        self.overlay.draw_divisions()
        self.overlay.draw_sample_boundry(self.s.sample_start,self.s.sample_stop)
        calmsg1, calmsg3 = self.s.calibration.status()
        self.overlay.label('cal1',calmsg1)
        self.overlay.label('cal3',calmsg3)
        self.overlay.label('fps', f"Framerate: {self.capture.fps}")
        self.overlay.label('save', self.saveMsg)
        self.overlay.label('hold', holdmsg)
        self.overlay.label('savpoly', f"Savgol Filter: {self.s.savpoly}")
        self.overlay.label('label_width', f"Label Peak Width: {self.s.mindist}")
        self.overlay.label('label_threshold', f"Label Threshold: {thresh}")

        if self.measure:
            self.overlay.show_cursor()
            self.overlay.show_measure(wavelengthData=self.s.calibration.wavelengthData)
        elif self.recPixels:
            self.overlay.show_cursor()
            self.overlay.show_measure()
            self.overlay.show_calibration_choices()

        cv2.imshow(self.spectrograph_title,self.s.spectrum_vertical)

    def update_waterfall_window(self,frame):
        #data is smoothed at this point!!!!!!
        #create an empty array for the data
        wdata = np.zeros([1,self.capture.width,3],dtype=np.uint8)
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
        self.history = np.insert(self.history, 0, wdata, axis=0) #insert line to beginning of array
        self.history = self.history[:-1].copy() #remove last element from array

        hsv = cv2.cvtColor(self.history, cv2.COLOR_BGR2HSV)

        #stack the images and display the waterfall
        cropped = self.capture.cropped_preview(frame)
        self.s.waterfall_vertical = np.vstack((ui.background,cropped, self.history))
        #dividing lines...
        cv2.line(self.s.waterfall_vertical,(0,80),(self.capture.width,80),(255,255,255),1)
        cv2.line(self.s.waterfall_vertical,(0,160),(self.capture.width,160),(255,255,255),1)
        #Draw this stuff over the top of the image!
        #Display a graticule calibrated with cal data
        textoffset = 12

        #vertical lines every whole 50nm
        for positiondata in self.s.fifties:
            for i in range(162,480):
                if i%20 == 0:
                    cv2.line(self.s.waterfall_vertical,(positiondata[0],i),(positiondata[0],i+1),(0,0,0),2)
                    cv2.line(self.s.waterfall_vertical,(positiondata[0],i),(positiondata[0],i+1),(255,255,255),1)
            cv2.putText(self.s.waterfall_vertical,str(positiondata[1])+'nm',(positiondata[0]-textoffset,475),self.font,0.4,(0,0,0),2, cv2.LINE_AA)
            cv2.putText(self.s.waterfall_vertical,str(positiondata[1])+'nm',(positiondata[0]-textoffset,475),self.font,0.4,(255,255,255),1, cv2.LINE_AA)


        #cv2.putText(self.s.waterfall_vertical,calmsg1,(490,15),font,0.4,(0,255,255),1, cv2.LINE_AA)
        #cv2.putText(self.s.waterfall_vertical,calmsg3,(490,51),font,0.4,(0,255,255),1, cv2.LINE_AA)
        #cv2.putText(self.s.waterfall_vertical,saveMsg,(490,69),font,0.4,(0,255,255),1, cv2.LINE_AA)
        #cv2.putText(self.s.waterfall_vertical,holdmsg,(640,15),font,0.4,(0,255,255),1, cv2.LINE_AA)

        cv2.imshow(self.waterfall_title,self.s.waterfall_vertical)
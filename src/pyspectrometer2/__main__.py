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

from . import Spectrometer
from . import cli
from . import ui
from . import video
from .record import readcal, snapshot, writecal
from .specFunctions import wavelength_to_rgb,savitzky_golay,peakIndexes,generateGraticule

args = cli.args()
spectrometer = Spectrometer()

def main(s: Spectrometer):
    if args.fullscreen:
        print("Fullscreen Spectrometer enabled")
    if args.waterfall:
        print("Waterfall display enabled")
        

    s.start_video_capture(args.device,args.width,args.height,args.fps)
    s.intensity = [0] * s.capture.width #array for intensity data...full of zeroes


    if args.waterfall:
        #waterfall first so spectrum is on top
        cv2.namedWindow(s.waterfall_title,cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow(s.waterfall_title,s.capture.width,s.stackHeight)
        cv2.moveWindow(s.waterfall_title,200,200);

    if args.fullscreen:
        cv2.namedWindow(s.spectrograph_title,cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(s.spectrograph_title,cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    else:
        cv2.namedWindow(s.spectrograph_title,cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow(s.spectrograph_title,s.capture.width,s.stackHeight)
        cv2.moveWindow(s.spectrograph_title,0,0);





    font=cv2.FONT_HERSHEY_SIMPLEX




    #messages
    msg1 = ""
    saveMsg = "No data saved"

    #blank image for Waterfall
    waterfall = np.zeros([s.graphHeight,s.capture.width,3],dtype=np.uint8)
    waterfall.fill(0) #fill black

    #Go grab the computed calibration data
    caldata = readcal(s.capture.width)
    s.wavelengthData = caldata[0]
    calmsg1 = caldata[1]
    calmsg2 = caldata[2]
    calmsg3 = caldata[3]

    #generate the craticule data
    graticuleData = generateGraticule(s.wavelengthData)
    tens = (graticuleData[0])
    fifties = (graticuleData[1])

    while(s.capture.isOpened()):
        # Capture frame-by-frame
        success, frame = s.capture.read()
        if not success:
            break

        if args.flip:
            FLIP_ABOUT_X_AXIS = 0
            FLIP_ABOUT_Y_AXIS = 1
            frame = cv2.flip(frame,flipCode=FLIP_ABOUT_Y_AXIS)

        y=int((s.capture.height/2)+s.vertical_crop_origin_offset) #origin of the vertical crop
        #y=200  #origin of the vert crop
        x=0     #origin of the horiz crop
        h=s.previewHeight   #height of the crop
        w=s.capture.width #width of the crop
        cropped = frame[y:y+h, x:x+w]
        bwimage = cv2.cvtColor(cropped,cv2.COLOR_BGR2GRAY)
        rows,cols = bwimage.shape
        halfway =int(rows/2)
        #show our line on the original image
        #now a 4px wide region
        cv2.line(cropped,(0,halfway-2),(s.capture.width,halfway-2),(255,255,255),1)
        cv2.line(cropped,(0,halfway+2),(s.capture.width,halfway+2),(255,255,255),1)


        #blank image for Graph
        graph = np.zeros([s.graphHeight,s.capture.width,3],dtype=np.uint8)
        graph.fill(255) #fill white

        #Display a graticule calibrated with cal data
        textoffset = 12
        #vertial lines every whole 10nm
        for position in tens:
            cv2.line(graph,(position,15),(position,s.graphHeight),(200,200,200),1)

        #vertical lines every whole 50nm
        for positiondata in fifties:
            cv2.line(graph,(positiondata[0],15),(positiondata[0],s.graphHeight),(0,0,0),1)
            cv2.putText(graph,str(positiondata[1])+'nm',(positiondata[0]-textoffset,12),font,0.4,(0,0,0),1, cv2.LINE_AA)

        #horizontal lines
        for i in range (s.graphHeight):
            if i>=64:
                if i%64==0: #suppress the first line then draw the rest...
                    cv2.line(graph,(0,i),(s.capture.width,i),(100,100,100),1)
        
        #Now process the intensity data and display it
        #intensity = []
        for i in range(cols):
            #data = bwimage[halfway,i] #pull the pixel data from the halfway mark   
            #print(type(data)) #numpy.uint8
            #average the data of 3 rows of pixels:
            dataminus1 = bwimage[halfway-1,i]
            datazero = bwimage[halfway,i] #pull the pixel data from the halfway mark
            dataplus1 = bwimage[halfway+1,i]
            data = (int(dataminus1)+int(datazero)+int(dataplus1))/3
            data = np.uint8(data)
                    
            
            if s.holdpeaks:
                if data > s.intensity[i]:
                    s.intensity[i] = data
            else:
                s.intensity[i] = data

        if args.waterfall:
            #waterfall....
            #data is smoothed at this point!!!!!!
            #create an empty array for the data
            wdata = np.zeros([1,s.capture.width,3],dtype=np.uint8)
            index=0
            for i in s.intensity:
                rgb = wavelength_to_rgb(round(s.wavelengthData[index]))#derive the color from the wavelenthData array
                luminosity = s.intensity[index]/255
                b = int(round(rgb[0]*luminosity))
                g = int(round(rgb[1]*luminosity))
                r = int(round(rgb[2]*luminosity))
                #print(b,g,r)
                #wdata[0,index]=(r,g,b) #fix me!!! how do we deal with this data??
                wdata[0,index]=(r,g,b)
                index+=1
            waterfall = np.insert(waterfall, 0, wdata, axis=0) #insert line to beginning of array
            waterfall = waterfall[:-1].copy() #remove last element from array

            hsv = cv2.cvtColor(waterfall, cv2.COLOR_BGR2HSV)



        #Draw the intensity data :-)
        #first filter if not holding peaks!
        
        if not s.holdpeaks:
            s.intensity = savitzky_golay(s.intensity,17,s.savpoly)
            s.intensity = np.array(s.intensity)
            s.intensity = s.intensity.astype(int)
            holdmsg = "Holdpeaks OFF" 
        else:
            holdmsg = "Holdpeaks ON"
            
        
        #now draw the intensity data....
        index=0
        for i in s.intensity:
            rgb = wavelength_to_rgb(round(s.wavelengthData[index]))#derive the color from the wvalenthData array
            r = rgb[0]
            g = rgb[1]
            b = rgb[2]
            #or some reason origin is top left.
            cv2.line(graph, (index,s.graphHeight), (index,s.graphHeight-i), (b,g,r), 1)
            cv2.line(graph, (index,319-i), (index,s.graphHeight-i), (0,0,0), 1,cv2.LINE_AA)
            index+=1


        #find peaks and label them
        textoffset = 12
        thresh = int(s.thresh) #make sure the data is int.
        indexes = peakIndexes(s.intensity, thres=thresh/max(s.intensity), min_dist=s.mindist)
        #print(indexes)
        for i in indexes:
            height = s.intensity[i]
            height = 310-height
            wavelength = round(s.wavelengthData[i],1)
            cv2.rectangle(graph,((i-textoffset)-2,height),((i-textoffset)+60,height-15),(0,255,255),-1)
            cv2.rectangle(graph,((i-textoffset)-2,height),((i-textoffset)+60,height-15),(0,0,0),1)
            cv2.putText(graph,str(wavelength)+'nm',(i-textoffset,height-3),font,0.4,(0,0,0),1, cv2.LINE_AA)
            #flagpoles
            cv2.line(graph,(i,height),(i,height+10),(0,0,0),1)

        #stack the images and display the spectrum  
        s.spectrum_vertical = np.vstack((ui.background,cropped, graph))

        s.overlay = ui.Overlay(s.spectrum_vertical,
                            s.capture.width,
                            message_height=s.messageHeight,
                            preview_height=s.previewHeight)

        #listen for click on plot window
        cv2.setMouseCallback(s.spectrograph_title,s.overlay.handle_mouse)

        s.overlay.draw_divisions()
        s.overlay.label('cal1',calmsg1)
        s.overlay.label('cal3',calmsg3)
        s.overlay.label('fps', f"Framerate: {s.capture.fps}")
        s.overlay.label('save', saveMsg)
        s.overlay.label('hold', holdmsg)
        s.overlay.label('savpoly', f"Savgol Filter: {s.savpoly}")
        s.overlay.label('label_width', f"Label Peak Width: {s.mindist}")
        s.overlay.label('label_threshold', f"Label Threshold: {thresh}")

        if s.measure:
            s.overlay.show_cursor()
            s.overlay.show_measure(wavelengthData=s.wavelengthData)
        elif s.recPixels:
            s.overlay.show_cursor()
            s.overlay.show_measure()
            s.overlay.show_calibration_choices()

        cv2.imshow(s.spectrograph_title,s.spectrum_vertical)

        if args.waterfall:
            #stack the images and display the waterfall 
            s.waterfall_vertical = np.vstack((ui.background,cropped, waterfall))
            #dividing lines...
            cv2.line(s.waterfall_vertical,(0,80),(s.capture.width,80),(255,255,255),1)
            cv2.line(s.waterfall_vertical,(0,160),(s.capture.width,160),(255,255,255),1)
            #Draw this stuff over the top of the image!
            #Display a graticule calibrated with cal data
            textoffset = 12

            #vertical lines every whole 50nm
            for positiondata in fifties:
                for i in range(162,480):
                    if i%20 == 0:
                        cv2.line(s.waterfall_vertical,(positiondata[0],i),(positiondata[0],i+1),(0,0,0),2)
                        cv2.line(s.waterfall_vertical,(positiondata[0],i),(positiondata[0],i+1),(255,255,255),1)
                cv2.putText(s.waterfall_vertical,str(positiondata[1])+'nm',(positiondata[0]-textoffset,475),font,0.4,(0,0,0),2, cv2.LINE_AA)
                cv2.putText(s.waterfall_vertical,str(positiondata[1])+'nm',(positiondata[0]-textoffset,475),font,0.4,(255,255,255),1, cv2.LINE_AA)

            cv2.putText(s.waterfall_vertical,calmsg1,(490,15),font,0.4,(0,255,255),1, cv2.LINE_AA)
            cv2.putText(s.waterfall_vertical,calmsg2,(490,33),font,0.4,(0,255,255),1, cv2.LINE_AA)
            cv2.putText(s.waterfall_vertical,calmsg3,(490,51),font,0.4,(0,255,255),1, cv2.LINE_AA)
            cv2.putText(s.waterfall_vertical,saveMsg,(490,69),font,0.4,(0,255,255),1, cv2.LINE_AA)

            cv2.putText(s.waterfall_vertical,holdmsg,(640,15),font,0.4,(0,255,255),1, cv2.LINE_AA)

            cv2.imshow(s.waterfall_title,s.waterfall_vertical)


        keyPress = cv2.waitKey(1)
        if keyPress == ord('q'):
            break
        s.handle_keypress(keyPress,args)

        #https://stackoverflow.com/a/45564409
        #handle window close
        if cv2.getWindowProperty(s.spectrograph_title,cv2.WND_PROP_VISIBLE) < 1:
            break
    
    #Everything done, release the vid
    s.capture.release()

    cv2.destroyAllWindows()


main(s=spectrometer)
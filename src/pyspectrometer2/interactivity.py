from dataclasses import dataclass
from warnings import warn

from .record import Calibration
from . import record
from .ui import Overlay
from .video import Capture
from .spectrometer import Spectrometer
from .specFunctions import generateGraticule

class SpectrometerInteractivity:

    def __init__(self, s: Spectrometer, capture: Capture, overlay: Overlay):
         self.s = s
         self.overlay = overlay
         self.capture = capture

    def handle_keypress(self,keyPress,args):
        if keyPress == -1:
             return

        if keyPress == 84:
            #down arrow
            self.capture.adjust_crop_offset(-1)
        elif keyPress == 82:
            #up arrow
            self.capture.adjust_crop_offset(1)
        elif keyPress == ord('h'):
            self.s.holdpeaks = not self.s.holdpeaks
        elif keyPress == ord("s"):
            #package up the data!
            graphdata = []
            graphdata.append(self.s.calibration.wavelengthData)
            graphdata.append(self.s.intensity)
            if args.waterfall:
                savedata = []
                savedata.append(self.s.spectrum_vertical)
                savedata.append(graphdata)
                savedata.append(self.s.waterfall_vertical)
            else:
                savedata = []
                savedata.append(self.s.spectrum_vertical)
                savedata.append(graphdata)
            saveMsg = record.snapshot(savedata,waterfall=args.waterfall)
        elif keyPress == ord("c"):
            clickArray = [(c.x,c.y) for c in self.overlay.clicks]
            calcomplete = self.s.calibration.writecal(clickArray)
            if calcomplete:
                #overwrite wavelength data
                #Go grab the computed calibration data
                self.s.calibration = Calibration(self.s.capture.width)
                #overwrite graticule data
                self.s.graticuleData = generateGraticule(self.calibration.wavelengthData)
                self.overlay.clear_claibration_clicks()
        elif keyPress == ord("x"):
            self.overlay.clear_claibration_clicks()
        elif keyPress == ord("m"):
            self.s.recPixels = False #turn off recpixels!
            self.s.measure = not self.s.measure
        elif keyPress == ord("p"):
            self.s.measure = False #turn off measure!
            self.s.recPixels = not self.s.recPixels
            self.overlay.clear_claibration_clicks()
        elif keyPress == ord("o"):#sav up
                self.s.savpoly+=1
                if self.s.savpoly >=15:
                    self.s.savpoly=15
        elif keyPress == ord("l"):#sav down
                self.s.savpoly-=1
                if self.s.savpoly <=0:
                    self.s.savpoly=0
        elif keyPress == ord("i"):#Peak width up
                self.s.mindist+=1
                if self.s.mindist >=100:
                    self.s.mindist=100
        elif keyPress == ord("k"):#Peak Width down
                self.s.mindist-=1
                if self.s.mindist <=0:
                    self.s.mindist=0
        elif keyPress == ord("u"):#label thresh up
                self.s.thresh+=1
                if self.s.thresh >=100:
                    self.s.thresh=100
        elif keyPress == ord("j"):#label thresh down
                self.s.thresh-=1
                if self.s.thresh <=0:
                    self.s.thresh=0
        else:
             warn(f"Unknown keypress: {keyPress}")
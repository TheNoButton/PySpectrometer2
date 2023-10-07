from dataclasses import dataclass
from warnings import warn

from .record import Calibration
from . import record
from .ui import Overlay
from .video import Capture
from .specFunctions import generateGraticule

class SpectrometerInteractivity:

    def __init__(self, app):
         self.app = app

    def handle_keypress(self,keyPress):
        if keyPress == -1:
             return

        if keyPress == 84:
            #down arrow
            self.app.capture.adjust_crop_offset(-1)
        elif keyPress == 82:
            #up arrow
            self.app.capture.adjust_crop_offset(1)
        elif keyPress == ord('h'):
            self.app.holdpeaks = not self.app.holdpeaks
        elif keyPress == ord("s"):
            #package up the data!
            graphdata = []
            graphdata.append(self.app.s.calibration.wavelengthData)
            graphdata.append(self.app.s.intensity)
            savedata = [ self.app.s.spectrum_vertical, graphdata]
            if self.app.waterfall:
                savedata.append(self.app.s.waterfall_vertical)
            self.app.saveMsg = record.snapshot(savedata,waterfall=self.app.waterfall)
        elif keyPress == ord("c"):
            clickArray = [(c.x,c.y) for c in self.app.overlay.clicks]
            calcomplete = self.app.s.calibration.writecal(clickArray)
            if calcomplete:
                #overwrite wavelength data
                #Go grab the computed calibration data
                self.app.s.calibration = Calibration(self.app.capture.width)
                #overwrite graticule data
                self.app.s.graticuleData = generateGraticule(self.app.s.calibration.wavelengthData)
                self.app.overlay.clear_claibration_clicks()
        elif keyPress == ord("x"):
            self.app.overlay.clear_claibration_clicks()
        elif keyPress == ord("m"):
            self.app.recPixels = False #turn off recpixels!
            self.app.measure = not self.app.measure
        elif keyPress == ord("p"):
            self.app.measure = False #turn off measure!
            self.app.recPixels = not self.app.recPixels
            self.app.overlay.clear_claibration_clicks()
        elif keyPress == ord("o"):#sav up
                self.app.s.savpoly+=1
                if self.app.s.savpoly >=15:
                    self.app.s.savpoly=15
        elif keyPress == ord("l"):#sav down
                self.app.s.savpoly-=1
                if self.app.s.savpoly <=0:
                    self.app.s.savpoly=0
        elif keyPress == ord("i"):#Peak width up
                self.app.s.mindist+=1
                if self.app.s.mindist >=100:
                    self.app.s.mindist=100
        elif keyPress == ord("k"):#Peak Width down
                self.app.s.mindist-=1
                if self.app.s.mindist <=0:
                    self.app.s.mindist=0
        elif keyPress == ord("u"):#label thresh up
                self.app.s.thresh+=1
                if self.app.s.thresh >=100:
                    self.app.s.thresh=100
        elif keyPress == ord("j"):#label thresh down
                self.app.s.thresh-=1
                if self.app.s.thresh <=0:
                    self.app.s.thresh=0
        else:
             warn(f"Unknown keypress: {keyPress}")
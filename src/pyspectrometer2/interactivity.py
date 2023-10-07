from dataclasses import dataclass

from .record import Calibration
from . import record
from .specFunctions import generateGraticule

@dataclass
class SpectrometerInteractivity:
    def handle_keypress(self,keyPress,args):
        if keyPress == 84:
            #down arrow
            self.vertical_crop_origin_offset -= 1
        elif keyPress == 82:
            #up arrow
            self.vertical_crop_origin_offset += 1
        elif keyPress == ord('h'):
            self.holdpeaks = not self.holdpeaks
        elif keyPress == ord("s"):
            #package up the data!
            graphdata = []
            graphdata.append(self.wavelengthData)
            graphdata.append(self.intensity)
            if args.waterfall:
                savedata = []
                savedata.append(self.spectrum_vertical)
                savedata.append(graphdata)
                savedata.append(self.waterfall_vertical)
            else:
                savedata = []
                savedata.append(self.spectrum_vertical)
                savedata.append(graphdata)
            saveMsg = record.snapshot(savedata,waterfall=args.waterfall)
        elif keyPress == ord("c"):
            clickArray = [(c.x,c.y) for c in self.overlay.clicks]
            calcomplete = self.calibration.writecal(clickArray)
            if calcomplete:
                #overwrite wavelength data
                #Go grab the computed calibration data
                self.calibration = Calibration(self.capture.width)
                #overwrite graticule data
                graticuleData = generateGraticule(self.calibration.wavelengthData)
                tens = (graticuleData[0])
                fifties = (graticuleData[1])
                self.overlay.clear_claibration_clicks()
        elif keyPress == ord("x"):
            self.overlay.clear_claibration_clicks()
        elif keyPress == ord("m"):
            self.recPixels = False #turn off recpixels!
            self.measure = not self.measure
        elif keyPress == ord("p"):
            self.measure = False #turn off measure!
            self.recPixels = not self.recPixels
            self.overlay.clear_claibration_clicks()
        elif keyPress == ord("o"):#sav up
                self.savpoly+=1
                if self.savpoly >=15:
                    self.savpoly=15
        elif keyPress == ord("l"):#sav down
                self.savpoly-=1
                if self.savpoly <=0:
                    self.savpoly=0
        elif keyPress == ord("i"):#Peak width up
                self.mindist+=1
                if self.mindist >=100:
                    self.mindist=100
        elif keyPress == ord("k"):#Peak Width down
                self.mindist-=1
                if self.mindist <=0:
                    self.mindist=0
        elif keyPress == ord("u"):#label thresh up
                self.thresh+=1
                if self.thresh >=100:
                    self.thresh=100
        elif keyPress == ord("j"):#label thresh down
                self.thresh-=1
                if self.thresh <=0:
                    self.thresh=0
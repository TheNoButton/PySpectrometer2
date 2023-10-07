from dataclasses import dataclass
from warnings import warn
import cv2
import time

import numpy as np

from .exceptions import CalibrationError

def snapshot(savedata,waterfall=False):
    now = time.strftime("%Y%m%d--%H%M%S")
    timenow = time.strftime("%H:%M:%S")
    imdata1 = savedata[0]
    graphdata = savedata[1]
    if waterfall:
        imdata2 = savedata[2]
        cv2.imwrite("waterfall-" + now + ".png",imdata2)
    cv2.imwrite("spectrum-" + now + ".png",imdata1)
    #print(graphdata[0]) #wavelengths
    #print(graphdata[1]) #intensities
    f = open("Spectrum-"+now+'.csv','w')
    f.write('Wavelength,Intensity\r\n')
    for x in zip(graphdata[0],graphdata[1]):
        f.write(str(x[0])+','+str(x[1])+'\r\n')
    f.close()
    message = "Last Save: "+timenow
    return(message)

@dataclass
class Calibration():
    width: int
    pixels: list[int] = None
    wavelengths: list[int] = None

    def __post_init__(self):
        self.wavelengthData = []
        self.readcal()
        self.map_px_wavelength()

    def status(self):
        if not self.pixels:
            return "UNCALIBRATED!", "Perform Calibration!"
        if len(self.pixels) == 3:
            return "Calibrated!", "2nd Order Polyfit"
        return "Calibrated!!", "3rd Order Polyfit"

    def map_px_wavelength(self):
        #create an array for the data...

        pixels = self.pixels
        wavelengths = self.wavelengths
        if not self.pixels:
            #blind guess placeholders
            pixels = [0,400,800]
            wavelengths = [380,560,750]
            warn("Using placeholder calibration data")
        
        if (len(self.pixels) == 3):
            print("Calculating second order polynomial...")
            coefficients = np.poly1d(np.polyfit(self.pixels, self.wavelengths, 2))
            print(coefficients)
            C1 = coefficients[2]
            C2 = coefficients[1]
            C3 = coefficients[0]
            print("Generating Wavelength Data!\n\n")
            for pixel in range(self.width):
                wavelength=((C1*pixel**2)+(C2*pixel)+C3)
                wavelength = round(wavelength,6) #because seriously!
                self.wavelengthData.append(wavelength)
            print("Done! Note that calibration with only 3 wavelengths will not be accurate!")
            warn("Note that calibration with only 3 wavelengths will not be accurate!")

        if (len(self.pixels) > 3):
            print("Calculating third order polynomial...")
            coefficients = np.poly1d(np.polyfit(self.pixels, self.wavelengths, 3))
            print(coefficients)
            #note this pulls out extremely precise numbers.
            #this causes slight differences in vals then when we compute manual, but hey ho, more precision
            #that said, we waste that precision later, but tbh, we wouldn't get that kind of precision in
            #the real world anyway! 1/10 of a nm is more than adequate!
            C1 = coefficients[3]
            C2 = coefficients[2]
            C3 = coefficients[1]
            C4 = coefficients[0]
            '''
            print(C1)
            print(C2)
            print(C3)
            print(C4)
            '''
            print("Generating Wavelength Data!\n\n")
            for pixel in range(self.width):
                wavelength=((C1*pixel**3)+(C2*pixel**2)+(C3*pixel)+C4)
                wavelength = round(wavelength,6)
                self.wavelengthData.append(wavelength)

            #final job, we need to compare all the recorded wavelenths with predicted wavelengths
            #and note the deviation!
            #do something if it is too big!
            predicted = []
            #iterate over the original pixelnumber array and predict results
            for i in self.pixels:
                px = i
                y=((C1*px**3)+(C2*px**2)+(C3*px)+C4)
                predicted.append(y)

            #calculate 2 squared of the result
            #if this is close to 1 we are all good!
            corr_matrix = np.corrcoef(self.wavelengths, predicted)
            corr = corr_matrix[0,1]
            R_sq = corr**2

            print("R-Squared="+str(R_sq))

    def readcal(self,filename='caldata.txt'):
        #read in the calibration points
        #compute second or third order polynimial, and generate wavelength array!
        #Les Wright 28 Sept 2022

        print("Loading calibration data...")
        with open(filename, 'r') as file:
            self.pixels = [int(i) for i in next(file).split(',')]
            self.wavelengths = [float(f) for f in next(file).split(',')]

        if len(self.pixels) != len(self.wavelengths):
            raise CalibrationError(f"Invalid calbration {len(self.pixels)=} != {len(self.wavelengths)=}")
        if (len(self.pixels) < 3):
            raise CalibrationError(f"Invalid calbration {len(self.pixels)=} < 3")


def writecal(clickArray):
    calcomplete = False
    pxdata = []
    wldata = []
    print("Enter known wavelengths for observed pixels!")
    for i in clickArray:
        pixel = i[0]
        wavelength = input("Enter wavelength for: "+str(pixel)+"px:")
        pxdata.append(pixel)
        wldata.append(wavelength)
    #This try except serves two purposes
    #first I want to write data to the caldata.txt file without quotes
    #second it validates the data in as far as no strings were entered 
    try:
        wldata = [float(x) for x in wldata]
    except:
        print("Only ints or decimals are allowed!")
        print("Calibration aborted!")

    pxdata = ','.join(map(str, pxdata)) #convert array to string
    wldata = ','.join(map(str, wldata)) #convert array to string
    f = open('caldata.txt','w')
    f.write(pxdata+'\r\n')
    f.write(wldata+'\r\n')
    print("Calibration Data Written!")
    calcomplete = True
    return calcomplete
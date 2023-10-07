import cv2
import time

import numpy as np

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


def readcal(width):
    #read in the calibration points
    #compute second or third order polynimial, and generate wavelength array!
    #Les Wright 28 Sept 2022
    errors = 0
    message = 0 #variable to store returned message data
    try:
        print("Loading calibration data...")
        file = open('caldata.txt', 'r')
    except:
        errors = 1

    try:
        #read both the pixel numbers and wavelengths into two arrays.
        lines = file.readlines()
        line0 = lines[0].strip() #strip newline
        pixels = line0.split(',') #split on ,
        pixels = [int(i) for i in pixels] #convert list of strings to ints
        line1 = lines[1].strip()
        wavelengths = line1.split(',')
        wavelengths = [float(i) for i in wavelengths]#convert list of strings to floats
    except:
        errors = 1

    try:
        if (len(pixels) != len(wavelengths)):
            #The Calibration points are of unequal length!
            errors = 1
        if (len(pixels) < 3):
            #The Cal data contains less than 3 pixels!
            errors = 1
        if (len(wavelengths) < 3):
            #The Cal data contains less than 3 wavelengths!
            errors = 1
    except:
        errors = 1

    if errors == 1:
        print("Loading of Calibration data failed (missing caldata.txt or corrupted data!")
        print("Loading placeholder data...")
        print("You MUST perform a Calibration to use this software!\n\n")
        center = width // 2
        pixels = [0,center,width]
        wavelengths = [380,560,750]


    #create an array for the data...
    wavelengthData = []

    if (len(pixels) == 3):
        print("Calculating second order polynomial...")
        coefficients = np.poly1d(np.polyfit(pixels, wavelengths, 2))
        print(coefficients)
        C1 = coefficients[2]
        C2 = coefficients[1]
        C3 = coefficients[0]
        print("Generating Wavelength Data!\n\n")
        for pixel in range(width):
            wavelength=((C1*pixel**2)+(C2*pixel)+C3)
            wavelength = round(wavelength,6) #because seriously!
            wavelengthData.append(wavelength)
        print("Done! Note that calibration with only 3 wavelengths will not be accurate!")
        if errors == 1:
            message = 0 #return message zero(errors)
        else:
            message = 1 #return message only 3 wavelength cal secodn order poly (Inaccurate)

    if (len(pixels) > 3):
        print("Calculating third order polynomial...")
        coefficients = np.poly1d(np.polyfit(pixels, wavelengths, 3))
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
        for pixel in range(width):
            wavelength=((C1*pixel**3)+(C2*pixel**2)+(C3*pixel)+C4)
            wavelength = round(wavelength,6)
            wavelengthData.append(wavelength)

        #final job, we need to compare all the recorded wavelenths with predicted wavelengths
        #and note the deviation!
        #do something if it is too big!
        predicted = []
        #iterate over the original pixelnumber array and predict results
        for i in pixels:
            px = i
            y=((C1*px**3)+(C2*px**2)+(C3*px)+C4)
            predicted.append(y)

        #calculate 2 squared of the result
        #if this is close to 1 we are all good!
        corr_matrix = np.corrcoef(wavelengths, predicted)
        corr = corr_matrix[0,1]
        R_sq = corr**2

        print("R-Squared="+str(R_sq))

        message = 2 #Multiwavelength cal, 3rd order poly


    if message == 0:
        calmsg1 = "UNCALIBRATED!"
        calmsg2 = "Defaults loaded"
        calmsg3 = "Perform Calibration!"
    if message == 1:
        calmsg1 = "Calibrated!!"
        calmsg2 = "Using 3 cal points"
        calmsg3 = "2nd Order Polyfit"
    if message == 2:
        calmsg1 = "Calibrated!!!"
        calmsg2 = "Using > 3 cal points"
        calmsg3 = "3rd Order Polyfit"

    returndata = []
    returndata.append(wavelengthData)
    returndata.append(calmsg1)
    returndata.append(calmsg2)
    returndata.append(calmsg3)
    return returndata


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
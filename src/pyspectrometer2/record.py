import cv2
import time

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
'''
PySpectrometer2 Les Wright 2022
https://www.youtube.com/leslaboratory
https://github.com/leswright1977

This project is a follow on from: https://github.com/leswright1977/PySpectrometer 

This is a more advanced, but more flexible version of the original program. Tk Has been dropped as the GUI to allow fullscreen mode on Raspberry Pi systems and the iterface is designed to fit 800*480 screens, which seem to be a common resolutin for RPi LCD's, paving the way for the creation of a stand alone benchtop instrument.

Whats new:
Higher reolution (800px wide graph)
3 row pixel averaging of sensor data
Fullscreen option for the Spectrometer graph
3rd order polymonial fit of calibration data for accurate measurement.
Improved graph labelling
Labelled measurement cursors
Optional waterfall display for recording spectra changes over time.
Key Bindings for all operations

All old features have been kept, including peak hold, peak detect, Savitsky Golay filter, and the ability to save graphs as png and data as CSV.

For instructions please consult the readme!

Future work:
It is planned to add in GPIO support, to allow the use of buttons and knobs to control the Spectrometer.
'''


import numpy as np
import time

def wavelength_to_rgb(nm):
		#from: Chris Webb https://www.codedrome.com/exploring-the-visible-spectrum-in-python/
		#returns RGB vals for a given wavelength
		gamma = 0.8
		max_intensity = 255
		factor = 0
		rgb = {"R": 0, "G": 0, "B": 0}
		if 380 <= nm <= 439:
			rgb["R"] = -(nm - 440) / (440 - 380)
			rgb["G"] = 0.0
			rgb["B"] = 1.0
		elif 440 <= nm <= 489:
			rgb["R"] = 0.0
			rgb["G"] = (nm - 440) / (490 - 440)
			rgb["B"] = 1.0
		elif 490 <= nm <= 509:
			rgb["R"] = 0.0
			rgb["G"] = 1.0
			rgb["B"] = -(nm - 510) / (510 - 490)
		elif 510 <= nm <= 579:
			rgb["R"] = (nm - 510) / (580 - 510)
			rgb["G"] = 1.0
			rgb["B"] = 0.0
		elif 580 <= nm <= 644:
			rgb["R"] = 1.0
			rgb["G"] = -(nm - 645) / (645 - 580)
			rgb["B"] = 0.0
		elif 645 <= nm <= 780:
			rgb["R"] = 1.0
			rgb["G"] = 0.0
			rgb["B"] = 0.0
		if 380 <= nm <= 419:
			factor = 0.3 + 0.7 * (nm - 380) / (420 - 380)
		elif 420 <= nm <= 700:
			factor = 1.0
		elif 701 <= nm <= 780:
			factor = 0.3 + 0.7 * (780 - nm) / (780 - 700)
		if rgb["R"] > 0:
			rgb["R"] = int(max_intensity * ((rgb["R"] * factor) ** gamma))
		else:
			rgb["R"] = 0
		if rgb["G"] > 0:
			rgb["G"] = int(max_intensity * ((rgb["G"] * factor) ** gamma))
		else:
			rgb["G"] = 0
		if rgb["B"] > 0:
			rgb["B"] = int(max_intensity * ((rgb["B"] * factor) ** gamma))
		else:
			rgb["B"] = 0
		#display no color as gray
		if(rgb["R"]+rgb["G"]+rgb["B"]) == 0:
			rgb["R"] = 155
			rgb["G"] = 155
			rgb["B"] = 155
		return (rgb["R"], rgb["G"], rgb["B"])


def savitzky_golay(y, window_size, order, deriv=0, rate=1):
	#scipy
	#From: https://scipy.github.io/old-wiki/pages/Cookbook/SavitzkyGolay
	'''
	Copyright (c) 2001-2002 Enthought, Inc. 2003-2022, SciPy Developers.
	All rights reserved.

	Redistribution and use in source and binary forms, with or without
	modification, are permitted provided that the following conditions
	are met:

	1. Redistributions of source code must retain the above copyright
	   notice, this list of conditions and the following disclaimer.

	2. Redistributions in binary form must reproduce the above
	   copyright notice, this list of conditions and the following
	   disclaimer in the documentation and/or other materials provided
	   with the distribution.

	3. Neither the name of the copyright holder nor the names of its
	   contributors may be used to endorse or promote products derived
	   from this software without specific prior written permission.

	THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
	"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
	LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
	A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
	OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
	SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
	LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
	DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
	THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
	(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
	OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
	'''
	import numpy as np
	from math import factorial
	try:
		window_size = np.abs(int(window_size))
		order = np.abs(int(order))
	except ValueError:
		raise ValueError("window_size and order have to be of type int")
	if window_size % 2 != 1 or window_size < 1:
		raise TypeError("window_size size must be a positive odd number")
	if window_size < order + 2:
		raise TypeError("window_size is too small for the polynomials order")
	order_range = range(order+1)
	half_window = (window_size -1) // 2
	# precompute coefficients
	b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
	m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
	# pad the signal at the extremes with
	# values taken from the signal itself
	firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
	lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
	y = np.concatenate((firstvals, y, lastvals))
	return np.convolve( m[::-1], y, mode='valid')

def peakIndexes(y, thres=0.3, min_dist=1, thres_abs=False):
	#from peakutils
	#from https://bitbucket.org/lucashnegri/peakutils/raw/f48d65a9b55f61fb65f368b75a2c53cbce132a0c/peakutils/peak.py
	'''
	The MIT License (MIT)

	Copyright (c) 2014-2022 Lucas Hermann Negri

	Permission is hereby granted, free of charge, to any person obtaining a copy
	of this software and associated documentation files (the "Software"), to deal
	in the Software without restriction, including without limitation the rights
	to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
	copies of the Software, and to permit persons to whom the Software is
	furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in
	all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
	FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
	AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
	LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
	OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
	THE SOFTWARE.
	'''
	if isinstance(y, np.ndarray) and np.issubdtype(y.dtype, np.unsignedinteger):
		raise ValueError("y must be signed")

	if not thres_abs:
		thres = thres * (np.max(y) - np.min(y)) + np.min(y)

	min_dist = int(min_dist)

	# compute first order difference
	dy = np.diff(y)

	# propagate left and right values successively to fill all plateau pixels (0-value)
	zeros, = np.where(dy == 0)

	# check if the signal is totally flat
	if len(zeros) == len(y) - 1:
		return np.array([])

	if len(zeros):
		# compute first order difference of zero indexes
		zeros_diff = np.diff(zeros)
		# check when zeros are not chained together
		zeros_diff_not_one, = np.add(np.where(zeros_diff != 1), 1)
		# make an array of the chained zero indexes
		zero_plateaus = np.split(zeros, zeros_diff_not_one)

		# fix if leftmost value in dy is zero
		if zero_plateaus[0][0] == 0:
			dy[zero_plateaus[0]] = dy[zero_plateaus[0][-1] + 1]
			zero_plateaus.pop(0)

		# fix if rightmost value of dy is zero
		if len(zero_plateaus) and zero_plateaus[-1][-1] == len(dy) - 1:
			dy[zero_plateaus[-1]] = dy[zero_plateaus[-1][0] - 1]
			zero_plateaus.pop(-1)

		# for each chain of zero indexes
		for plateau in zero_plateaus:
			median = np.median(plateau)
			# set leftmost values to leftmost non zero values
			dy[plateau[plateau < median]] = dy[plateau[0] - 1]
			# set rightmost and middle values to rightmost non zero values
			dy[plateau[plateau >= median]] = dy[plateau[-1] + 1]

	# find the peaks by using the first order difference
	peaks = np.where(
		(np.hstack([dy, 0.0]) < 0.0)
		& (np.hstack([0.0, dy]) > 0.0)
		& (np.greater(y, thres))
	)[0]

	# handle multiple peaks, respecting the minimum distance
	if peaks.size > 1 and min_dist > 1:
		highest = peaks[np.argsort(y[peaks])][::-1]
		rem = np.ones(y.size, dtype=bool)
		rem[peaks] = False

		for peak in highest:
			if not rem[peak]:
				sl = slice(max(0, peak - min_dist), peak + min_dist + 1)
				rem[sl] = True
				rem[peak] = False

		peaks = np.arange(y.size)[~rem]

	return peaks	


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

def generateGraticule(wavelengthData):
	low = wavelengthData[0] #get lowet number in list
	high = wavelengthData[len(wavelengthData)-1] #get highest number
	#round and int these numbers so we have our range of numbers to look at
	#give a margin of 10 at each end for good measure
	low = int(round(low))-10
	high = int(round(high))+10
	#print('...')
	#print(low)
	#print(high)
	#print('...')
	returndata = []
	#find positions of every whole 10nm
	tens = []
	for i in range(low,high):
		if (i%10==0):
			#position contains pixelnumber and wavelength
			position = min(enumerate(wavelengthData), key=lambda x: abs(i - x[1]))
			#If the difference between the target and result is <9 show the line
			#(otherwise depending on the scale we get dozens of number either end that are close to the target)
			if abs(i-position[1]) <1: 
				#print(i)
				#print(position)
				tens.append(position[0])
	returndata.append(tens)
	fifties = []
	for i in range(low,high):
		if (i%50==0):
			#position contains pixelnumber and wavelength
			position = min(enumerate(wavelengthData), key=lambda x: abs(i - x[1]))
			#If the difference between the target and result is <1 show the line
			#(otherwise depending on the scale we get dozens of number either end that are close to the target)
			if abs(i-position[1]) <1: 
				labelpos = position[0]
				labeltxt = int(round(position[1]))
				labeldata = [labelpos,labeltxt]
				fifties.append(labeldata)
	returndata.append(fifties)
	return returndata























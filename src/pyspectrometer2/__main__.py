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

from pyspectrometer2.app import App

from .exceptions import CalibrationError

from .spectrometer import Spectrometer
from . import cli,record,video

args = cli.args()


def main():
    capture = video.Capture.initialize(args.device,args.width,args.height,args.fps)
    print(capture)
    if capture.width != args.width:
        raise RuntimeError(f"Unable to open device /dev/video{args.device} with width={args.width}.")

    calibration = record.Calibration(capture.width)
    s = Spectrometer(calibration)

    if args.fullscreen:
        print("Fullscreen Spectrometer enabled")
    if args.waterfall:
        print("Waterfall display enabled")
    app = App(s,
        capture=capture,
        fullscreen=args.fullscreen,
        waterfall=args.waterfall,
        flip=args.flip)
    app.run()

main()
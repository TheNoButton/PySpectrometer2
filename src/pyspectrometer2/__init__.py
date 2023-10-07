from dataclasses import dataclass,field
from .interactivity import SpectrometerInteractivity
from . import video
from .record import Calibration
from .specFunctions import generateGraticule

@dataclass
class Spectrometer(SpectrometerInteractivity):
    #window
    graphHeight: int = 320
    previewHeight: int = 80
    messageHeight: int = 80
    spectrograph_title: str = 'PySpectrometer 2 - Spectrograph'
    waterfall_title: str = 'PySpectrometer 2 - Waterfall'

    #modes and views
    holdpeaks: bool = False #are we holding peaks?
    measure: bool = False #are we measuring?
    recPixels: bool = False #are we measuring pixels and recording clicks?
    showWaterfall: bool = False

    #calibration
    calibration: Calibration = None
    vertical_crop_origin_offset: int = 0
    graticuleData: list = None

    #settings for peak detect
    savpoly: int = 7 #savgol filter polynomial max val 15
    mindist: int = 50 #minumum distance between peaks max val 100
    thresh: int = 20 #Threshold max val 100

    def __post_init__(self):
        self.intensity = []
        self.capture = None

    def start_video_capture(self,device,width,height,fps):
        self.capture = video.Capture.initialize(device,width,height,fps)
        self.calibration = Calibration(self.capture.width)
        self.graticuleData = generateGraticule(self.calibration.wavelengthData)
        print(self.capture)

    @property
    def stackHeight(self):
       #height of the displayed CV window
       return self.graphHeight+self.previewHeight+self.messageHeight

    @property
    def tens(self):
        return self.graticuleData[0]

    @property
    def fifties(self):
        return self.graticuleData[1]
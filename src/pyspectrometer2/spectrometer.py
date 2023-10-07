
from dataclasses import dataclass

import numpy as np

from . import video
from .record import Calibration
from .specFunctions import nm_labels

@dataclass
class Spectrometer:
    calibration: Calibration = None

    #settings for peak detect
    savpoly: int = 7 #savgol filter polynomial max val 15
    mindist: int = 50 #minumum distance between peaks max val 100
    thresh: int = 20 #Threshold max val 100
    holdpeaks: bool = False

    def __post_init__(self):
        self.intensity = [0] * self.calibration.width #array for intensity data...full of zeroes

    @property
    def tens(self):
        return nm_labels(self.calibration.wavelengthData,step=10)

    @property
    def fifties(self):
        return nm_labels(self.calibration.wavelengthData,step=50)
    
    def sample_intensity(self,preview,sample_count=3):
        crop_center = len(preview) // 2
        self.sample_start = max(0,crop_center - sample_count // 2)
        self.sample_stop = min(len(preview), self.sample_start + sample_count)
        sample = preview[self.sample_start:self.sample_stop]
        intensities = [sum(col)//len(col) for col in zip(*sample)]
        if self.holdpeaks:
           self.intensity = [max(previous,current) for previous,current in zip(self.intensity,intensities)]
        else:
           self.intensity = intensities
        self.intensity = np.uint8(self.intensity)
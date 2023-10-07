from dataclasses import dataclass
from importlib.resources import files
from typing import List

import cv2
import numpy as np


def logo():
    #banner image
    background = files('pyspectrometer2').joinpath("static/background.png").read_bytes()
    np_data = np.frombuffer(background,np.uint8)
    mat = cv2.imdecode(np_data,3)
    return mat

@dataclass
class Coordinates():
    x: int
    y: int

class MouseEvent():

    def __init__(self,mat):
        self.mat = mat

@dataclass
class Overlay():
    mat: cv2.Mat
    frame_width: int
    message_height: int = 80
    preview_height: int = 80
    font: int = cv2.FONT_HERSHEY_SIMPLEX
    cursor = Coordinates(0,0)
    scale: float = 0.4
    clicks = []

    def handle_mouse(self,event,x,y,flags,param):
        if event == cv2.EVENT_MOUSEMOVE:
            self.cursor.x = x
            self.cursor.y = y
        if event == cv2.EVENT_LBUTTONDOWN:
            click = Coordinates(x,y)
            self.clicks.append(click)

    def draw_sample_boundry(self, start, stop):
        color = (255,0,0)
        preview_start = self.message_height
        preview_stop = preview_start + self.preview_height
        sample_start = preview_start+start
        sample_stop = preview_start+stop
        top = max(preview_start,sample_start)
        bottom = min(preview_stop,sample_stop)
        for y in top,bottom:
            begin = (0,y)
            end = (self.frame_width,y)
            cv2.line(self.mat,begin,end,color,thickness=1)

    def draw_divisions(self):
        #dividing lines...
        y=0
        for offset in self.message_height, self.preview_height:
            y += offset
            begin = (0,y)
            end = (self.frame_width,y)
            color = (255,255,255)
            cv2.line(self.mat,begin,end,color,thickness=1)

    def label(self,label,msg):
        locations = {
            'cal': (490,15),
            'sample_y': (490,33),
            'fps': (490,51),
            'save': (490,69),
            'hold': (640,15),
            'savpoly': (640,33),
            'label_width': (640,51),
            'label_threshold': (640,69),
        }

        location = locations[label]
        color = (0,255,255)
        thickness = 1
        cv2.putText(self.mat,msg,location,self.font,self.scale,color,thickness,lineType=cv2.LINE_AA)

    def show_measure(self, cursor_offset_px=5, wavelengthData=None):
        """
        If wavelengthData is provided, display the wavelength corresponding to
        cursor position. Otherwise, display the cursor position in px.
        """
        if wavelengthData:
            wavelength = wavelengthData[self.cursor.x]
            label = f"{wavelength:0.2f}nm"
        else: 
            label = f"{self.cursor.x}px"
        x = self.cursor.x
        x += cursor_offset_px # right of cursor
        y = self.cursor.y
        y -= cursor_offset_px # above cursor
        color = (0,0,0)

        cv2.putText(
            self.mat,
            label,
            (x,y),
            self.font,self.scale,color,
            thickness=1, lineType=cv2.LINE_AA)

    def show_cursor(self,rectile_size_px=40):
        #show the cursor!
        len = rectile_size_px // 2
        color = (0,0,0)

        #vertical   
        cv2.line(self.mat,
           (self.cursor.x,self.cursor.y-len),
           (self.cursor.x,self.cursor.y+len),
           color=color,
           thickness=1)
        #horizontal
        cv2.line(self.mat,
           (self.cursor.x-len,self.cursor.y),
           (self.cursor.x+len,self.cursor.y),
           color=color,
           thickness=1)
    
    def show_calibration_choices(self, radius=5, label_offset_px=5):
        color = (0,0,0)
        for idx,click in enumerate(self.clicks):
            center = (click.x,click.y)
            cv2.circle(self.mat,center=center,radius=5,color=color,thickness=-1)
            #we can display text :-) so we can work out wavelength from x-pos
            #and display it ultimately
            x = click.x + label_offset_px
            y = click.y
            label = f"{idx}:{click.x}px"
            cv2.putText(self.mat,label,(x,y),self.font,self.scale,color)
    
    @classmethod
    def clear_claibration_clicks(cls):
        cls.clicks = []

    @classmethod
    def background(cls,width):
        "all black background, with logo overlay"
        bg = np.zeros([cls.message_height,width,3],dtype=np.uint8)
        img = logo()
        h = min(bg.shape[0],img.shape[0])
        w = min(bg.shape[1],img.shape[1])
        bg[0:h,0:w] = img[0:h,0:w]
        return bg
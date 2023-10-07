from dataclasses import dataclass
import cv2

@dataclass
class Overlay():
    mat: cv2.Mat
    frame_width: int
    message_height: int = 80
    preview_height: int = 80
    font: int = cv2.FONT_HERSHEY_SIMPLEX


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
            'cal1': (490,15),
            'cal3': (490,33),
            'fps': (490,51),
            'save': (490,69),
            'hold': (640,15),
            'savpoly': (640,33),
            'label_width': (640,51),
            'label_threshold': (640,69),
        }

        location = locations[label]
        color = (0,255,255)
        scale = 0.4
        thickness = 1
        cv2.putText(self.mat,msg,location,self.font,scale,color,thickness,lineType=cv2.LINE_AA)

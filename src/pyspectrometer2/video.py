import cv2

class Capture(cv2.VideoCapture):

    def __init__(self, *args, preview_origin = 0, preview_height = 80, **kwargs):
        super().__init__(*args,**kwargs)
        self.crop_offset = preview_origin
        self.preview_height = preview_height

    @property
    def width(self):
        return int(self.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def height(self):
        return int(self.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @property
    def fps(self):
        return int(self.get(cv2.CAP_PROP_FPS))

    @classmethod
    def initialize(cls, device="0", width=800, height=600, fps=30):
        #init video
        cap = cls('/dev/video'+device, cv2.CAP_V4L)
        #cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
        cap.set(cv2.CAP_PROP_FPS,fps)
        return cap
    
    def cropped_preview(self, frame):
        y = self.height//2 + self.crop_offset #origin of the vertical crop
        x = 0     #origin of the horiz crop
        h=self.preview_height   #height of the crop
        w=self.width #width of the crop
        cropped = frame[y:y+h, x:x+w]
        return cropped


    def __str__(self):
        return f"[info] W={self.width}, H={self.height}, FPS={self.fps}"
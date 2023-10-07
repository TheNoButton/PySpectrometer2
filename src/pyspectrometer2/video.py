import cv2

class Capture(cv2.VideoCapture):
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

    def __str__(self):
        return f"[info] W={self.width}, H={self.height}, FPS={self.fps}"
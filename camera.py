"""A module for video camera."""

import cv2

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

class Camera():
    """This class privides video camera functions."""

    def __init__(self):
        self.capture = None
        self._device = 0
        self._fps = 30
        self.image_width = CAMERA_WIDTH
        self.image_height = CAMERA_HEIGHT

    @property
    def device(self):
        """Device number."""
        return self._device

    @property
    def fps(self):
        """Frames per second."""
        return self._fps

    def capture_video(self, device=0, fps=30, size=(CAMERA_WIDTH, CAMERA_HEIGHT)):
        """Sets periodic screen capture.

        Args:
            device (int): Device number. Default is 0.
            fps (int): Frames per second. Default is 30 frames.
            size ((width, height)): Frame width and height in pixels.
        """
        self._device = device
        self._fps = fps
        self.image_width, self.image_height = size

        # open webcam
        self.capture = cv2.VideoCapture(self._device)
        if not self.capture.isOpened():
            if not self.capture.open():
                raise TypeError

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.image_width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.image_height)

    def read_frame(self):
        """Reads next frame from the camera.

        Returns:
            retval, image: True if success; video image frame.
        """
        return self.capture.read()

    def release(self):
        """Closes video file or capturing device."""
        self.capture.release()

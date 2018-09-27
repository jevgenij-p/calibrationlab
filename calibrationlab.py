
"""An application for exploring OpenCV functions working with a camera.
"""
# https://wiki.wxpython.org/Getting%20Started
# http://zetcode.com/wxpython/layout/
# http://www.blog.pythonlibrary.org/2012/02/14/wxpython-all-about-menus/

import wx
import cv2
from camera import Camera
from calibration import CameraCalibration
from calibrationpanel import CalibrationPanel

__author__ = "Jevgenijs Pankovs"
__license__ = "GNU GPL 3.0 or later"

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

class MainWindow(wx.Frame):
    """Base class for the UI layout."""

    def __init__(self, parent, title):

        wx.Frame.__init__(self, parent, title=title,
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        self.captured_image = None
        self.timer = None
        self.bitmap = None
        self.camera_label = None
        self.camera_menu_ids = []
        self.menu_save_capture = None
        self.button_calibrate = None
        self.camera = Camera()
        self.calibration = CameraCalibration()
        self.calibration.calibrated += self.on_calibrated
        self.calibration.on_progress += self.on_calibration_progress

        self.screen = wx.Panel(self, size=(SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.Bind(wx.EVT_PAINT, self._on_paint)
        self.screen.Bind(wx.EVT_ERASE_BACKGROUND, self._disable_event)

        panel1 = wx.Panel(self)
        sizer1 = wx.BoxSizer(wx.VERTICAL)

        panel2 = wx.Panel(panel1)
        panel2.SetMinSize((200, 400))
        sizer2 = wx.BoxSizer(wx.VERTICAL)

        self.camera_label = wx.StaticText(panel2, label="Camera 0")
        sizer2.Add(self.camera_label, flag=wx.LEFT)

        self.preview = wx.StaticBitmap(panel2, size=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4))
        self.preview.SetBackgroundColour(wx.LIGHT_GREY)
        sizer2.Add(self.preview, flag=wx.TOP, border=10)

        button1 = wx.Button(panel2, label='Capture')
        sizer2.Add(button1, flag=wx.TOP, border=6)
        button1.Bind(wx.EVT_BUTTON, self._on_capture)

        calibration_file_name = "camera1_calibration.xml"
        calibration_file = (calibration_file_name[:16] + '...') \
            if len(calibration_file_name) > 16 else calibration_file_name

        sizer3 = wx.FlexGridSizer(3, 2, 4, 10)
        label1 = wx.StaticText(panel2, label="Calibrated:")
        self.calibration_status = wx.StaticText(panel2, label="no")
        label3 = wx.StaticText(panel2, label="Mean error:")
        self.calibration_error = wx.StaticText(panel2, label="")
        label5 = wx.StaticText(panel2, label="Calibration file:")
        label6 = wx.StaticText(panel2, label=calibration_file)
        sizer3.AddMany([(label1, 0, wx.EXPAND),
                        (self.calibration_status, 0, wx.EXPAND),
                        (label3, 0, wx.EXPAND),
                        (self.calibration_error, 0, wx.EXPAND),
                        (label5, 0, wx.EXPAND),
                        (label6, 0, wx.EXPAND)])

        sizer2.Add(sizer3, flag=wx.TOP, border=20)

        self.button_calibrate = wx.Button(panel2, label='Calibrate')
        self.button_calibrate.Bind(wx.EVT_BUTTON, self._on_calibrate)
        sizer2.Add(self.button_calibrate, flag=wx.TOP, border=6)

        sizer1.Add(panel2, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM, border=16)

        clibration_panel = CalibrationPanel(panel2)
        sizer2.Add(clibration_panel, flag=wx.TOP, border=20)

        panel2.SetSizer(sizer2)
        panel1.SetSizer(sizer1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.screen, 0, wx.ALIGN_CENTER)
        sizer.Add(panel1, flag=wx.EXPAND)

        self._create_menu()

        self.SetSizerAndFit(sizer)
        self.Show(True)

    def _disable_event(*pargs, **kwargs):
        # pylint: disable=E0211
        pass

    def _create_menu(self):
        menu1 = wx.Menu()
        menu1.AppendSeparator()
        self.menu_save_capture = menu1.Append(wx.ID_ANY, "Save captured image")
        self.menu_save_capture.Enable(False)
        menu_exit = menu1.Append(wx.ID_EXIT, "E&xit")

        menu2 = wx.Menu()
        camera_menu_items = []
        for i in range(0, 5):
            menu_id = wx.NewId()
            self.camera_menu_ids.append(menu_id)
            menu_item = menu2.Append(menu_id, "Camera {}".format(i), kind=wx.ITEM_RADIO)
            camera_menu_items.append(menu_item)
            self.Bind(wx.EVT_MENU, self._on_camera, menu_item)

        menu2.Check(self.camera_menu_ids[0], True)

        menu_bar = wx.MenuBar()
        menu_bar.Append(menu1, "&File")
        menu_bar.Append(menu2, "&Camera")
        self.SetMenuBar(menu_bar)

        # Set events
        self.Bind(wx.EVT_MENU, self._on_save_capture, self.menu_save_capture)
        self.Bind(wx.EVT_MENU, self._on_exit, menu_exit)

    def capture_video(self, device=0, fps=30, size=(640, 480)):
        """Sets periodic screen capture.

        Args:
            device (int): Device number. Default is 0.
            fps (int): Frames per second. Default is 30 frames.
            size ((width, height)): Frame width and height in pixels.
        """

        # open webcam
        try:
            self.camera.capture_video(device, fps, size)
        except TypeError:
            dialog = wx.MessageDialog(self, "Could not open camera %d" % self.camera.device, "Error")
            dialog.SetOKLabel("Close")
            dialog.ShowModal()
            dialog.Destroy()
            return

        # set up periodic screen capture
        self.timer = wx.Timer(self)
        self.timer.Start(1000. / self.camera.fps)
        self.Bind(wx.EVT_TIMER, self._on_next_frame)

    def _on_camera(self, event):
        # pylint: disable=W0613
        menu_id = event.GetId()
        device_number = self.camera_menu_ids.index(menu_id)
        self.camera_label.SetLabel("Camera {}".format(device_number))
        self.capture_video(device_number)

    def _on_calibrate(self, event):
        # pylint: disable=W0613
        self.button_calibrate.Disable()
        self.calibration.calibrate()

    def on_calibrated(self):
        # pylint: disable=C0111
        self.button_calibrate.Enable()
        self.calibration_status.SetLabel("yes" if self.calibration.is_calibrated else "no")
        self.calibration_error.SetLabel("{:.3f}".format(self.calibration.mean_error) \
            if self.calibration.is_calibrated else "")

    def on_calibration_progress(self, progress):
        # pylint: disable=C0111
        self.calibration_status.SetLabel(progress)

    def _on_next_frame(self, event):
        """Captures a new frame from the camera and copies it
           to an image buffer to be displayed.
        """
        # pylint: disable=W0613
        success, frame = self.camera.read_frame()
        if success:
            frame = self.calibration.process_frame(frame)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # update buffer and paint
            if self.bitmap is None:
                self.bitmap = wx.Bitmap.FromBuffer(frame.shape[1], frame.shape[0], frame)
            else:
                self.bitmap.CopyFromBuffer(frame)

            self.Refresh(eraseBackground=False)

    def _on_paint(self, event):
        # pylint: disable=W0613
        # read and draw buffered bitmap
        if self.bitmap is not None:
            _device_context = wx.BufferedPaintDC(self.screen)
            _device_context.DrawBitmap(self.bitmap, 0, 0)

    def _on_capture(self, event):
        # pylint: disable=W0613
        if self.bitmap is not None:
            size = self.preview.GetSize()
            self.captured_image = self.bitmap.ConvertToImage()
            image = self.captured_image.Scale(size.Width, size.Height, wx.IMAGE_QUALITY_HIGH)
            self.preview.SetBitmap(wx.Bitmap(image))
            self.menu_save_capture.Enable(True)

    def _on_save_capture(self, event):
        # pylint: disable=W0613
        with wx.FileDialog(self, "Save captured image", wildcard="PNG files (*.png)|*.png",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = file_dialog.GetPath()
            try:
                self.captured_image.SaveFile(pathname, wx.BITMAP_TYPE_BMP)
            except IOError:
                wx.LogError("Cannot save captured image in file '%s'." % pathname)

    def _on_exit(self, event):
        # pylint: disable=W0613
        self.camera.release()
        self.Close(True)


def main():
    """Method creating main window.
    """
    app = wx.App(False)
    frame = MainWindow(None, "Camera")
    frame.capture_video(device=0, fps=30, size=(640, 480))
    app.SetTopWindow(frame)
    app.MainLoop()

if __name__ == '__main__':
    main()

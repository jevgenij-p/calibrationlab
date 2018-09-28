
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
        self.menu_load_calibration = None
        self.menu_save_capture = None
        self.menu_save_calibration = None
        self.button_capture = None
        self.button_calibrate = None
        self.button_cancel = None
        self.chk_undistort = None
        self.camera = Camera()
        self.screen = None
        self.right_panel = None
        self.calibration_panel = None
        self.calibration = CameraCalibration()
        self.calibration.calibrated += self.on_calibrated
        self.calibration.on_progress += self.on_calibration_progress

        self.create_layout()
        self.create_menu()

        self.button_capture.Bind(wx.EVT_BUTTON, self.on_capture)
        self.button_calibrate.Bind(wx.EVT_BUTTON, self.on_calibrate)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.on_cancel_calibrate)
        self.chk_undistort.Bind(wx.EVT_CHECKBOX, self.on_undistort)

        self.Show(True)

    def disable_event(*pargs, **kwargs):
        # pylint: disable=E0211
        pass

    def create_layout(self):
        self.screen = wx.Panel(self, size=(SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen.Bind(wx.EVT_PAINT, self.on_paint)
        self.screen.Bind(wx.EVT_ERASE_BACKGROUND, self.disable_event)

        self.right_panel = wx.Panel(self)

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        panel1 = wx.Panel(self.right_panel)
        panel1.SetMinSize((200, 400))
        sizer2 = wx.BoxSizer(wx.VERTICAL)

        self.camera_label = wx.StaticText(panel1, label="Camera 0")
        sizer2.Add(self.camera_label, flag=wx.TOP)

        self.preview = wx.StaticBitmap(panel1, size=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4))
        self.preview.SetBackgroundColour(wx.LIGHT_GREY)
        sizer2.Add(self.preview, flag=wx.TOP, border=10)

        self.button_capture = wx.Button(panel1, label='Capture')
        sizer2.Add(self.button_capture, flag=wx.TOP, border=6)

        self.calibration_panel = CalibrationPanel(panel1)
        self.calibration_panel.status = "no"
        self.calibration_panel.filename = "camera1_calibration.xml"
        sizer2.Add(self.calibration_panel, flag=wx.TOP, border=16)

        self.button_calibrate = wx.Button(panel1, label='Calibrate')
        self.button_cancel = wx.Button(panel1, label='Cancel')
        self.button_cancel.Disable()

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.button_calibrate, flag=wx.TOP, border=6)
        sizer3.Add(self.button_cancel, flag=wx.TOP, border=6)

        sizer2.Add(sizer3, flag=wx.LEFT|wx.RIGHT|wx.EXPAND)

        self.chk_undistort = wx.CheckBox(panel1, label="Undistort")
        self.chk_undistort.SetValue(False)
        self.chk_undistort.Disable()
        sizer2.Add(self.chk_undistort, flag=wx.TOP, border=16)

        sizer1.Add(panel1, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM, border=16)
        panel1.SetSizer(sizer2)
        self.right_panel.SetSizer(sizer1)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.screen, 0, wx.ALIGN_CENTER)
        sizer.Add(self.right_panel, flag=wx.EXPAND)

        self.SetSizerAndFit(sizer)

    def create_menu(self):
        menu1 = wx.Menu()
        self.menu_load_calibration = menu1.Append(wx.ID_ANY, "Load calibration file")
        menu1.AppendSeparator()
        self.menu_save_capture = menu1.Append(wx.ID_ANY, "Save captured image")
        self.menu_save_calibration = menu1.Append(wx.ID_ANY, "Save calibration file")
        menu1.AppendSeparator()
        menu_exit = menu1.Append(wx.ID_EXIT, "E&xit")

        self.menu_save_capture.Enable(False)
        self.menu_save_calibration.Enable(False)

        menu2 = wx.Menu()
        for i in range(0, 5):
            menu_id = wx.NewId()
            self.camera_menu_ids.append(menu_id)
            menu_item = menu2.Append(menu_id, f"Camera {i}", kind=wx.ITEM_RADIO)
            self.Bind(wx.EVT_MENU, self.on_camera, menu_item)

        menu2.Check(self.camera_menu_ids[0], True)

        menu_bar = wx.MenuBar()
        menu_bar.Append(menu1, "&File")
        menu_bar.Append(menu2, "&Camera")
        self.SetMenuBar(menu_bar)

        # Set events
        self.Bind(wx.EVT_MENU, self.on_save_calibration, self.menu_save_calibration)
        self.Bind(wx.EVT_MENU, self.on_save_capture, self.menu_save_capture)
        self.Bind(wx.EVT_MENU, self.on_exit, menu_exit)

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
            dialog = wx.MessageDialog(self, f"Could not open camera {self.camera.device}", "Error")
            dialog.SetOKLabel("Close")
            dialog.ShowModal()
            dialog.Destroy()
            return

        # set up periodic screen capture
        self.timer = wx.Timer(self)
        self.timer.Start(1000. / self.camera.fps)
        self.Bind(wx.EVT_TIMER, self.on_next_frame)

    def on_camera(self, event):
        # pylint: disable=W0613
        menu_id = event.GetId()
        device_number = self.camera_menu_ids.index(menu_id)
        self.camera_label.SetLabel(f"Camera {device_number}")
        self.capture_video(device_number)

    def on_calibrate(self, event):
        # pylint: disable=W0613
        self.chk_undistort.SetValue(False)
        self.chk_undistort.Disable()
        self.button_calibrate.Disable()
        self.button_cancel.Enable()
        self.calibration.calibrate()
        self.menu_load_calibration.Enable(False)
        self.menu_save_calibration.Enable(False)
        self.calibration_panel.filename = ""

    def on_cancel_calibrate(self, event):
        # pylint: disable=W0613
        self.button_calibrate.Enable()
        self.button_cancel.Disable()
        self.calibration.cancel()
        self.calibration_panel.status = "no"
        self.calibration_panel.error = ""
        self.menu_load_calibration.Enable(True)

    def on_undistort(self, event):
        # pylint: disable=W0613
        pass

    def on_calibrated(self):
        # pylint: disable=C0111
        calibrated = self.calibration.is_calibrated
        self.button_calibrate.Enable()
        self.button_cancel.Disable()
        self.calibration_panel.status = "yes" if calibrated else "no"
        self.calibration_panel.error = "{:.3f}".format(self.calibration.mean_error) \
            if calibrated else ""
        self.chk_undistort.Enabled = calibrated
        self.menu_load_calibration.Enable(True)
        self.menu_save_calibration.Enable(calibrated)

    def on_calibration_progress(self, progress):
        # pylint: disable=C0111
        self.calibration_panel.status = progress

    def on_next_frame(self, event):
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

    def on_paint(self, event):
        # pylint: disable=W0613
        # read and draw buffered bitmap
        if self.bitmap is not None:
            _device_context = wx.BufferedPaintDC(self.screen)
            _device_context.DrawBitmap(self.bitmap, 0, 0)

    def on_capture(self, event):
        # pylint: disable=W0613
        if self.bitmap is not None:
            size = self.preview.GetSize()
            self.captured_image = self.bitmap.ConvertToImage()
            image = self.captured_image.Scale(size.Width, size.Height, wx.IMAGE_QUALITY_HIGH)
            self.preview.SetBitmap(wx.Bitmap(image))
            self.menu_save_capture.Enable(True)

    def on_save_capture(self, event):
        # pylint: disable=W0613
        with wx.FileDialog(self, "Save captured image", wildcard="PNG files (*.png)|*.png",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = file_dialog.GetPath()
            try:
                self.captured_image.SaveFile(pathname, wx.BITMAP_TYPE_BMP)
            except IOError:
                wx.LogError(f"Cannot save captured image in file '{pathname}'.")

    def on_save_calibration(self, event):
        with wx.FileDialog(self, "Save calibration file", wildcard="JSON files (*.json)|*.json",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = file_dialog.GetPath()
            try:
                self.calibration.save_calibration(pathname)
            except IOError:
                wx.LogError(f"Cannot save calibration data in file '{pathname}'.")

    def on_exit(self, event):
        # pylint: disable=W0613
        self.timer.Stop()
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

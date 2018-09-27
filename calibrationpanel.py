"""A module creating UI control, containing calibration properties."""

import wx

class CalibrationPanel(wx.Panel):
    """Class creating UI layout for calibration properties."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(wx.LIGHT_GREY)

        sizer = wx.BoxSizer(wx.VERTICAL)
        fsizer = wx.FlexGridSizer(3, 2, 4, 10)
        self._status = wx.StaticText(self, label="")
        self._error = wx.StaticText(self, label="")
        self._file = wx.StaticText(self, label="")
        fsizer.AddMany([(wx.StaticText(self, label="Calibrated:"), 0, wx.EXPAND),
                        (self._status, 0, wx.EXPAND),
                        (wx.StaticText(self, label="Mean error:"), 0, wx.EXPAND),
                        (self._error, 0, wx.EXPAND),
                        (wx.StaticText(self, label="Calibration file:"), 0, wx.EXPAND),
                        (self._file, 0, wx.EXPAND)])

        sizer.Add(fsizer, flag=wx.TOP, border=10)
        self.SetSizer(sizer)

    @property
    def status(self):
        """Calibration status."""
        return self._status.GetLabel()

    @status.setter
    def status(self, value):
        self._status.SetLabel(value)

    @property
    def error(self):
        """Calibration mean error."""
        return self._error.GetLabel()

    @error.setter
    def error(self, value):
        self._error.SetLabel(value)

    @property
    def filename(self):
        """Calibration file name."""
        return self._file.GetLabel()

    @filename.setter
    def filename(self, value):
        self._file.SetLabel(value)
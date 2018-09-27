"""A module creating UI control, containing calibration properties."""

import wx

class CalibrationPanel(wx.Panel):
    """Class creating UI layout for calibration properties."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(wx.StaticText(self, label="Calibration"))

        fsizer = wx.FlexGridSizer(3, 2, 4, 10)
        self._status = wx.StaticText(self, label="no")
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

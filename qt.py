import sys, amcam
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel, QApplication, QWidget, QDesktopWidget, QCheckBox, QMessageBox

class SnapWin(QWidget):
    def __init__(self):
        super().__init__()
        self.w = 0           # video width
        self.h = 0           # video height
        self.total = 0
        self.setFixedSize(800, 600)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        self.initUI()

    def initUI(self):
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.label.move(0, 30)
        self.label.resize(self.geometry().width(), self.geometry().height())


class MainWin(QWidget):
    eventImage = pyqtSignal(int)

    def __init__(self, gain=100, integration_time=10):
        super().__init__()
        self.hcam = None
        self.buf = None      # video buffer
        self.w = 0           # video width
        self.h = 0           # video height
        self.total = 0
        self.snap_total = 0
        self.gain = gain
        self.integration_time = integration_time
        self.setFixedSize(800, 600)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        self.initUI()
        self.initCamera()
        self.snap_win = None

    def initUI(self):
        self.cb = QCheckBox('Auto Exposure', self)
        self.cb.stateChanged.connect(self.changeAutoExposure)
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.label.move(0, 30)
        self.label.resize(self.geometry().width(), self.geometry().height())

# the vast majority of callbacks come from amcam.dll/so/dylib internal threads, so we use qt signal to post this event to the UI thread  
    @staticmethod
    def cameraCallback(nEvent, ctx):
        if nEvent == amcam.AMCAM_EVENT_IMAGE or amcam.AMCAM_EVENT_STILLIMAGE:
            ctx.eventImage.emit(nEvent)

# run in the UI thread
    @pyqtSlot(int)
    def eventImageSignal(self, nEvent):
        if self.hcam is not None:
            if nEvent == amcam.AMCAM_EVENT_IMAGE:
                try:
                    self.hcam.PullImageV2(self.buf, 24, None)
                    self.total += 1
                except amcam.HRESULTException as ex:
                    QMessageBox.warning(self, '', 'pull image failed, hr=0x{:x}'.format(ex.hr), QMessageBox.Ok)
                else:
                    self.setWindowTitle('{}: {}'.format(self.camname, self.total))
                    img = QImage(self.buf, self.w, self.h, (self.w * 24 + 31) // 32 * 4, QImage.Format_RGB888)
                    self.label.setPixmap(QPixmap.fromImage(img))
            elif nEvent == amcam.AMCAM_EVENT_STILLIMAGE:
                try:
                    self.hcam.PullStillImageV2(self.buf, 24, None)
                    self.snap_total += 1
                except amcam.HRESULTException as ex:
                    QMessageBox.warning(self, '', 'pull image failed, hr=0x{:x}'.format(ex.hr), QMessageBox.Ok)
                else:
                    if self.snap_win == None:
                        self.snap_win = SnapWin()
                    self.snap_win.setWindowTitle('{}: {}'.format(self.camname, self.snap_total))
                    img = QImage(self.buf, self.w, self.h, (self.w * 24 + 31) // 32 * 4, QImage.Format_RGB888)
                    self.snap_win.label.setPixmap(QPixmap.fromImage(img))
                    self.snap_win.show()

    def initCamera(self):
        a = amcam.Amcam.EnumV2()
        if len(a) <= 0:
            self.setWindowTitle('No camera found')
            self.cb.setEnabled(False)
        else:
            self.camname = a[0].displayname
            self.setWindowTitle(self.camname)
            self.eventImage.connect(self.eventImageSignal)
            try:
                self.hcam = amcam.Amcam.Open(a[0].id)
            except amcam.HRESULTException as ex:
                QMessageBox.warning(self, '', 'failed to open camera, hr=0x{:x}'.format(ex.hr), QMessageBox.Ok)
            else:
                self.hcam.put_ExpoAGain(self.gain)
                self.hcam.put_ExpoTime(self.integration_time) 
                self.hcam.put_eSize(0) # 2560x1922

                self.w, self.h = self.hcam.get_Size()
                bufsize = ((self.w * 24 + 31) // 32 * 4) * self.h
                self.buf = bytes(bufsize)
                self.cb.setChecked(self.hcam.get_AutoExpoEnable())            
                try:
                    if sys.platform == 'win32':
                        self.hcam.put_Option(amcam.AMCAM_OPTION_BYTEORDER, 0) # QImage.Format_RGB888
                    self.hcam.StartPullModeWithCallback(self.cameraCallback, self)
                except amcam.HRESULTException as ex:
                    QMessageBox.warning(self, '', 'failed to start camera, hr=0x{:x}'.format(ex.hr), QMessageBox.Ok)

    def snap(self):
        self.hcam.Snap(0)
    
    def changeAutoExposure(self, state):
        if self.hcam is not None:
            self.hcam.put_AutoExpoEnable(state == Qt.Checked)

    def closeEvent(self, event):
        if self.hcam is not None:
            self.hcam.Close()
            self.hcam = None
            # print("Closing")

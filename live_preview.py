import sys, amcam, driver
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel, QApplication, QWidget, QDesktopWidget, QCheckBox, QMessageBox
import threading
import time
import asyncio
import matplotlib
matplotlib.use("TkAgg")

class MainWin(QWidget):
    eventImage = pyqtSignal(int)

    def __init__(self, gain=100, integration_time=10):
        super().__init__()
        self.gain = gain
        self.time = integration_time
        self.driver = driver.Driver(gain, integration_time)
        # threading.Thread(target=self.driver.run()).start()
        # self.driver.run()
        self.setFixedSize(800, 600)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        self.initUI()
        self.width = 2560
        self.height = 1922
        # self.update
        # self.initCamera()

    def initUI(self):
        self.cb = QCheckBox('Auto Exposure', self)
        self.cb.stateChanged.connect(self.changeAutoExposure)
        self.label = QLabel(self)
        self.label.setScaledContents(True)
        self.label.move(0, 30)
        self.label.resize(self.geometry().width(), self.geometry().height())

# the vast majority of callbacks come from amcam.dll/so/dylib internal threads, so we use qt signal to post this event to the UI thread  
#    @staticmethod
#    def cameraCallback(nEvent, ctx):
#        if nEvent == amcam.AMCAM_EVENT_IMAGE or amcam.AMCAM_EVENT_STILLIMAGE:
#            ctx.eventImage.emit(nEvent)

# run in the UI thread
#    @pyqtSlot(int)
#    def eventImageSignal(self, nEvent):
#        if self.driver is not None:
#            if nEvent == amcam.AMCAM_EVENT_IMAGE:
#                try:
#                    self.hcam.PullImageV2(self.buf, 24, None)
#                    self.total += 1
#                except amcam.HRESULTException as ex:
#                    QMessageBox.warning(self, '', 'pull image failed, hr=0x{:x}'.format(ex.hr), QMessageBox.Ok)
#                else:
#                    self.setWindowTitle('{}: {}'.format(self.camname, self.total))
#                    img = QImage(self.buf, self.w, self.h, (self.w * 24 + 31) // 32 * 4, QImage.Format_RGB888)
#                    self.label.setPixmap(QPixmap.fromImage(img))

    async def update(self):
        asyncio.create_task(self.driver.run())

        time.sleep(5)
        self.driver.close()

    async def updateImageRepeat(self):
        while True:
            self.updateImage()

    def updateImage(self):
        self.setWindowTitle('{}: {}'.format(self.driver.get_name(), self.driver.get_total()))
        img = QImage(self.driver.get_image_fast(), self.width, self.height, (self.width * 24 + 31) // 32 * 4, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(img))

    def changeAutoExposure(self, state):
        if self.driver is not None:
            self.driver.setAutoExposure(state == Qt.Checked)

    def closeEvent(self, event):
        if self.driver is not None:
            self.driver.close()
            self.driver = None
            # sys.exit(app.exec_())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWin(100, 10)
    win.show()
    print("showing??")
    # threading.Thread(target=win.driver.run()).start()

    asyncio.run(win.update())

    asyncio.run(win.updateImageRepeat())
    # win.update()
    # win.updateImage()
    #time.sleep(5)
    #win.driver.close()

    sys.exit(app.exec_()) 



    




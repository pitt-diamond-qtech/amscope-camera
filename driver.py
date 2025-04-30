import amcam, numpy as np
import threading
import asyncio
import matplotlib
matplotlib.use("TkAgg")

class Driver:

    def __init__(self, gain=100, time=10):
        self.hcam = None
        self.buf = None
        self.width = 0
        self.height = 0
        self.total = 0
        self.snap_total = 0
        self.live_image = None
        self.snap_image = None
        self.gain = gain
        self.time = time * 1000
        self.closing = False
        self.ready_event = asyncio.Event()
        self.camname = "Camera"

    # the vast majority of callbacks come from amcam.dll/so/dylib internal threads
    @staticmethod
    def cameraCallback(nEvent, ctx):
        if nEvent == amcam.AMCAM_EVENT_IMAGE:
            ctx.CameraCallback(nEvent)

    def CameraCallback(self, nEvent):
        if nEvent == amcam.AMCAM_EVENT_IMAGE:
            try:
                self.hcam.PullImageV2(self.buf, 24, None)
                self.total += 1
                img = np.frombuffer(self.buf, dtype=np.uint8).reshape(self.height, self.width, 3)
                cropwidth = self.width//2
                cropheight = self.height//2
                self.live_image = img[self.height//2-cropheight:self.height//2+cropheight,self.width//2-cropwidth:self.width//2+cropwidth,]
            except amcam.HRESULTException as ex:
                print('pull image failed, hr=0x{:x}'.format(ex.hr))
        elif nEvent == amcam.AMCAM_EVENT_STILLIMAGE:
            # print("still image detected")
            try:
                self.hcam.PullStillImageV2(self.buf, 24, None)
                snap_total += 1
                img = np.frombuffer(self.buf, dtype=np.uint8).reshape(self.height, self.width, 3)
                cropwidth = self.width//2
                cropheight = self.height//2
                self.snap_image = img[self.height//2-cropheight:self.height//2+cropheight,self.width//2-cropwidth:self.width//2+cropwidth,]
            except amcam.HRESULTException as ex:
                print('pull image failed, hr=0x{:x}'.format(ex.hr))
        else:
            print('event callback: {}'.format(nEvent))

    async def run(self):
        a = amcam.Amcam.EnumV2()
        if len(a) > 0:
            print('{}: flag = {:#x}, preview = {}, still = {}'.format(a[0].displayname, a[0].model.flag, a[0].model.preview, a[0].model.still))
            for r in a[0].model.res:
                print('\t = [{} x {}]'.format(r.width, r.height))
            self.camname = a[0].displayname
            self.hcam = amcam.Amcam.Open(a[0].id)
            if self.hcam:
                try:
                    self.hcam.put_ExpoAGain(self.gain)
                    self.hcam.put_ExpoTime(self.time) 
                    self.hcam.put_eSize(0) # 2560x1922

                    self.width, self.height = self.hcam.get_Size()
                    bufsize = ((self.width * 24 + 31) // 32 * 4) * self.height
                    print('image size: {} x {}, bufsize = {}'.format(self.width, self.height, bufsize))
                    self.buf = bytes(bufsize)
                    if self.buf:
                        try:
                            self.hcam.StartPullModeWithCallback(self.cameraCallback, self)
                        except amcam.HRESULTException as ex:
                            print('failed to start camera, hr=0x{:x}'.format(ex.hr))
                        print("Waiting for trigger...")
                        await self.ready_event.wait()
                        print("Triggered! Continuing execution...")
                finally:
                    self.hcam.Close()
                    self.hcam = None
                    self.buf = None
            else:
                print('failed to open camera')
        else:
            print('no camera found')

    def get_int_time(self):
        return self.hcam.get_ExpoTime() / 1000

    def set_int_time(self, t):
        if t > 2000:
            print("Warning: Integration time cannot be higher than 2000ms. It has been set to the maximum value of 2000ms.")
            self.time = 2000
        elif t < 0.05:
            print("Warning: Integration time cannot be smaller than 0.05ms. It has been set to the minimum value of 0.05ms.")
            self.time = 0.05
        else:
            self.time = t
        self.time *= 1000
        self.hcam.put_ExpoTime(self.time)

    def get_gain(self):
        return self.hcam.get_ExpoAGain()

    def set_gain(self, g):
        if g > 300:
            print("Warning: Gain cannot be higher than 300%. It has been set to the maximum value of 300%.")
            self.gain = 300
        elif g < 100:
            print("Warning: Gain cannot be smaller than 100%. It has been set to the minimum value of 100%.")
            self.gain = 100
        else:
            self.gain = g
        self.hcam.put_ExpoAGain(self.gain)

    def setAutoExposure(self, state):
        if self.hcam is not None:
            self.hcam.put_AutoExpoEnable(state)

    def get_total(self):
        return self.total
    
    def get_name(self):
        return self.camname
    
    def get_width(self):
        return self.width
    
    def get_height(self):
        return self.height
    
    def get_image_fast(self):
        return self.buf
    
    def get_image(self, t):
        self.set_int_time(t)
        self.hcam.Snap()
        return self.snap_image
    
    def close(self):
        self.ready_event.set()
import amcam
import cv2
import numpy as np

def runRegistration(currImgArray, prevImgArray):
    if prevImgArray is None:
        return 0,0
    # do registration stuff
    # grayscale+float conversions
    gray1 = np.float32(cv2.cvtColor(currImgArray, cv2.COLOR_BGR2GRAY))
    gray2 = np.float32(cv2.cvtColor(prevImgArray, cv2.COLOR_BGR2GRAY))

    # Calculate phase correlation
    (dx, dy), _ = cv2.phaseCorrelate(gray1, gray2)

    # Get image size
    height, width = currImgArray.shape[:2]

    # Calculate number of pixels mapped in X and Y directions
    num_pixels_x = dx * width
    num_pixels_y = dy * height

    #print("Number of pixels mapped in X direction:", num_pixels_x)
    #print("Number of pixels mapped in Y direction:", num_pixels_y)
    # save this frame's array data for the next frame of registration
    return num_pixels_x, num_pixels_y

class App:
    def __init__(self):
        self.hcam = None
        self.buf = None
        self.total = 0

# the vast majority of callbacks come from amcam.dll/so/dylib internal threads
    @staticmethod
    def cameraCallback(nEvent, ctx):
        if nEvent == amcam.AMCAM_EVENT_IMAGE or nEvent == amcam.AMCAM_EVENT_STILLIMAGE:
            ctx.CameraCallback(nEvent)

    def CameraCallback(self, nEvent):
        if nEvent == amcam.AMCAM_EVENT_IMAGE:
            try:
                self.hcam.PullImageV2(self.buf, 24, None)
                self.total += 1
                # print('pull image ok, total = {}'.format(self.total))
                img = np.frombuffer(self.buf, dtype=np.uint8).reshape(self.height, self.width, 3)
                cropwidth = self.width//2
                cropheight = self.height//2
                img = img[self.height//2-cropheight:self.height//2+cropheight,self.width//2-cropwidth:self.width//2+cropwidth,]
                cv2.imshow('image', img)
                cv2.waitKey(1)
                px,py = runRegistration(img, self.prevImg)
                self.prevImg = img
            except amcam.HRESULTException as ex:
                print('pull image failed, hr=0x{:x}'.format(ex.hr))
        elif nEvent == amcam.AMCAM_EVENT_STILLIMAGE:
            # print("still image detected")
            try:
                self.hcam.PullStillImageV2(self.buf, 24, None)
                # self.total += 1
                # print('pull still image ok')
                img = np.frombuffer(self.buf, dtype=np.uint8).reshape(self.height, self.width, 3)
                cropwidth = self.width//2
                cropheight = self.height//2
                img = img[self.height//2-cropheight:self.height//2+cropheight,self.width//2-cropwidth:self.width//2+cropwidth,]
                cv2.imshow('snap', img)
                cv2.waitKey(1)
                # px,py = runRegistration(img, self.prevImg)
                # self.prevImg = img
            except amcam.HRESULTException as ex:
                print('pull image failed, hr=0x{:x}'.format(ex.hr))
        else:
            print('event callback: {}'.format(nEvent))

    def run(self):

        self.prevImg = None
        a = amcam.Amcam.EnumV2()

        if len(a) > 0:
            print('{}: flag = {:#x}, preview = {}, still = {}'.format(a[0].displayname, a[0].model.flag, a[0].model.preview, a[0].model.still))
            for r in a[0].model.res:
                print('\t = [{} x {}]'.format(r.width, r.height))
            self.hcam = amcam.Amcam.Open(a[0].id)
            if self.hcam:
                try:
                    #integrationTime = float(input())
                    self.hcam.put_AutoExpoEnable(False)

                    # self.input_gain(100, 300)
                    # self.input_integration_time(0.05, 2000)
                    # self.input_resolution()

                    # defaults for testing
                    self.hcam.put_ExpoAGain(100)
                    self.hcam.put_ExpoTime(10 * 1000)
                    self.hcam.put_eSize(0)

                    width, height = self.hcam.get_Size()
                    self.width = width
                    self.height = height
                    print(self.height)
                    bufsize = ((width * 24 + 31) // 32 * 4) * height
                    print('image size: {} x {}, bufsize = {}'.format(width, height, bufsize))
                    self.buf = bytes(bufsize)
                    if self.buf:
                        isLive = True
                        #while(True):
                        #    mode = input("Choose mode - (l)ive or (s)nap: ")
                        #    if mode == "s":
                        #        isLive = False
                        #        break
                        #    elif not(mode == "l"):
                        #        print("Invalid mode.")
                        #    else:
                        #        break
                        try:
                            self.hcam.StartPullModeWithCallback(self.cameraCallback, self)
                        except amcam.HRESULTException as ex:
                            print('failed to start camera, hr=0x{:x}'.format(ex.hr))
                        
                        # self.hcam.Snap(0)
                        # self.hcam.Snap(0)
                        # input("Press ENTER to exit")
                    while(True):
                        command = input('Press q to quit, s to snap: ')
                        if command == "q":
                            break
                        elif command == "s":
                            self.hcam.Snap(0)
                        else:
                            print("Invalid command")
                finally:
                    self.hcam.Close()
                    self.hcam = None
                    self.buf = None
            else:
                print('failed to open camera')
        else:
            print('no camera found')

if __name__ == '__main__':
    app = App()
    app.run()
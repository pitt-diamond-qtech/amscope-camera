import qt
from PyQt5.QtWidgets import QApplication
import sys

def input_gain(low_bound, high_bound): # parameters in %
    gain = 0
    while gain < low_bound or gain > high_bound:
        gain = int(input("Enter the electronic gain (100-300) in %: "))
    return gain

def input_integration_time(low_bound, high_bound): # parameters in ms
    integration_time = 0
    while integration_time < low_bound or integration_time > high_bound:
        integration_time = int(input("Enter the integration time (0.05-2000) in ms: "))
    integration_time *= 1000 # put in units of microseconds
    return integration_time

def input_resolution():
    res = ""
    while not (res == "high" or res == "mid" or res == "low"):
        res = input("Choose a resolution (\"high\", \"mid\", or \"low\"): ")
    return res

if __name__ == '__main__':
    gain = input_gain(100, 300) # MU503B default range
    integration_time = input_integration_time(0.05, 2000) # MU503B default range
    # res = input_resolution()

    app = QApplication(sys.argv)
    win = qt.MainWin(gain, integration_time)
    win.show()
    
    while(True):
        command = input('Press q to quit, s to snap: ')
        if command == "q":
            print("Close all windows to terminate program")
            sys.exit(app.exec_())
        elif command == "s":
            win.snap()
        else:
            print("Invalid command")
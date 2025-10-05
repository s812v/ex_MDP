import os
import argparse

from src.tasks.maintask1 import MultiProcessComms
from src.tasks.taska2 import DetectImage
from src.tasks.taska5 import NavigateSearching

task = "A2"

def init():
    os.system("sudo hciconfig hci0 piscan")
    if task == "A2":
        detect_image_process = DetectImage()
        detect_image_process.start()
    elif task == "M1":
        main_process = MultiProcessComms()
        main_process.start()

if __name__ == '__main__':
    init()
 
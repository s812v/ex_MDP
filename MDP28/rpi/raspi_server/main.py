import os
import argparse

from src.tasks.maintask1v2 import MainTask
from src.tasks.maintask1 import MultiProcessComms
from src.tasks.taska2 import DetectImage
from src.tasks.taska5 import A5
from src.tasks.taska34 import AndroidMovement

task = "M1V2"
# 6C:2F:8A:38:0E:AA tablet
# 50:DA:D6:B3:8F:88 redmi
def init():
    os.system("sudo hciconfig hci0 piscan")
    if task == "A2":
        detect_image_process = DetectImage()
        detect_image_process.start()
    elif task == "A34":
        android_movement_process = AndroidMovement()
        android_movement_process.start()
    elif task == "M1":
        main_process = MultiProcessComms()
        main_process.start()
    elif task == "M1V2":
        main_proces = MainTask()
        main_proces.start()
    elif task == "A5":
        main_proces = A5()
        main_proces.start()

if __name__ == '__main__':
    init()
 
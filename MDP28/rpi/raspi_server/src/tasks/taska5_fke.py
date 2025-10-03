import time
import serial
import pickle
# from rpiStm import STM32
from src.PseudoSTM_com import Arduino_communicator
from src.Algorithm_com import Algorithm_communicator
#from imageDetection import imageDetect

def _take_pic(self):
    try:
        start_time = datetime.now()
        # initialize the camera and grab a reference to the raw camera capture
        camera = PiCamera(resolution=(IMAGE_WIDTH, IMAGE_HEIGHT))  # '1920x1080'
        rawCapture = PiRGBArray(camera)
        # allow the camera to warmup
        time.sleep(0.1)
        # grab an image from the camera
        camera.capture(rawCapture, format=IMAGE_FORMAT)
        image = rawCapture.array
        camera.close()
        print('Time taken to take picture: ' + str(datetime.now() - start_time) + 'seconds')

    except Exception as error:
        print('Taking picture failed: ' + str(error))
    
    return image
    

def a5main():
    ImageServer = Algorithm_communicator()
    STM = Arduino_communicator()
    
    ImageServer.connect()
    STM.connect()
    
    digits = '0123456789'
    img_dist = 15
    c = 1
    while(True):
        print('Round ' + str(c))
        while True:
            STM.write('scan obstacle'.encode())
            time.sleep(0.5)
            stm_recv = STM.read()
            stm_recv = stm_recv.decode('utf-8')
            time.sleep(0.5)
            obs_dist = 0
            if stm_recv is None:
                continue
            for digit in stm_recv:
                if digit not in digits:
                    break
                else:
                    obs_dist = obs_dist*10 + int(digit)
            if obs_dist > 0:
                break
        move_dist = obs_dist - img_dist
        if(move_dist < 0):
            move_dist = abs(move_dist)
            STM.send(f'SB0{move_dist}') # straight backward
        else:
            STM.send(f'SF0{move_dist}')
        
        result = 0
        while True:
            message = STM.read()
            time.sleep(0.5)
            if message is not None:
                # ! searching for image
                image = _take_pic()
                # ! send to inference client
                image = image.tobytes()
                ImageServer.send(image)
                time.sleep(0.5)
                # ! receive result from inference client
                while True:
                    try:
                        detection = ImageServer.read()
                        if data is not None:
                            result = pickle.loads(detection)
                            if len(result) == 0:
                                result = "nothing"
                            else:
                                result = result[0]["class_name"]
                            break
                    except Exception as error:
                        print('Image detection failed: ' + str(error))
                break
            else:
                continue
        if c>3:
            break
        
        if(result == 'bulls' or result == 'nothing'):
            #commands = ["right,90,reverse,0", "center,0,forward,30", "right,90,forward,10", 'right,180,forward,10'] #, "center,0,reverse,20", "center,0,forward,20"]
            commands = ["right,90,reverse,0", "center,0,forward,75","left,90,forward,0", 'center,0,forward,5','left,90,forward,0']
            STM.send(commands[0])
            cnt = 1
            while(True):
                
                message = STM.recv()
                time.sleep(0.5)
                if cnt >= len(commands) and message is not None:
                    break
                if message != None:
                    # if(message[:4] == 'move
                    STM.send(commands[cnt])
                    message = None
                    #print(message)
                    cnt += 1
        else:
            print('Not bullseye ', result)
            break
        c+=1

if __name__ == "__main__":
    a5main()
    

import sys
import time
import ast
from typing import List

import algorithm.settings as settings
from algorithm.app import AlgoMinimal
from algorithm.entities.assets.direction import Direction
from algorithm.entities.connection.algorithm_client import AlgorithmClient
from algorithm.entities.connection.algorithm_server import AlgorithmServer
from algorithm.entities.grid.obstacle import Obstacle

def get_relative_pos(obstacles, targets):
    results = []
    for i in range(len(obstacles)):
        ob = obstacles[i]
        target = targets[i]
        ob_x = ob.x_cm 
        ob_y = ob.y_cm
        camera_x = target.x // settings.SCALING_FACTOR
        camera_y = target.y // settings.SCALING_FACTOR
        if ob.direction == Direction.TOP:
            horizontal = camera_x - ob_x
            vertical = abs(camera_y - ob_y)
        elif ob.direction == Direction.BOTTOM:
            horizontal = ob_x - camera_x
            vertical = abs(camera_y - ob_y)
        elif ob.direction == Direction.LEFT:
            horizontal = camera_y - ob_y
            vertical = abs(camera_x - ob_x)
        elif ob.direction == Direction.RIGHT:
            horizontal = ob_y - camera_y
            vertical = abs(camera_x - ob_x)
        
        # print(" get relative pos", ob, target, ob.direction)
        # print(f"realtive position camera {camera_x} {camera_y}, obstacle {ob_x}, {ob_y}")
        results.append([horizontal*10, vertical*10])
    return results

def parse_obstacle_data(data) -> List[Obstacle]:
    obs = []
    for obstacle_params in data:
        obs.append(Obstacle(obstacle_params[0]+5,
                            obstacle_params[1]+5,
                            Direction(obstacle_params[2]),
                            obstacle_params[3]))
    # [[x, y, orient, index], [x, y, orient, index]]
    return obs

def run_minimal(waiting_rpi: bool = True, hardcoded: bool = False):
    # Create a client to connect to the RPi.
    # print(f"Attempting to connect to {settings.RPI_HOST}:{settings.RPI_PORT}")
    if waiting_rpi:
        client = AlgorithmClient(settings.RPI_HOST, settings.RPI_PORT)
        print("Wait to connect to RPi.")
        while True:
            try:
                client.connect()
                break
            except OSError:
                pass
            except KeyboardInterrupt:
                client.close()
                sys.exit(1)
        print("Connected to RPi!\n")

        print("Waiting to receive obstacle data from RPi...")
        obstacle_data = None
        client.socket.settimeout(10)
    while True:
        if waiting_rpi:
            while True:
                try:
                    buffer = client.receive_data()
                    if buffer is None:
                        continue
                    else:
                        print("Got data buffer, ", buffer)
                        if buffer.decode() == '':
                            client.close()
                            client = AlgorithmClient(settings.RPI_HOST, settings.RPI_PORT)
                            print("Got disconnected")
                            print("Trying to reconnect")
                            while True:
                                time.sleep(1)
                                try:
                                    client.connect()
                                    break
                                except OSError as e:
                                    client = AlgorithmClient(settings.RPI_HOST, settings.RPI_PORT)
                                    pass
                                except KeyboardInterrupt:
                                    client.close()
                                    sys.exit(1)
                            print("Connected to RPi!\n")
                            continue
                        else:   
                            buffer = buffer.decode()
                            buffer = buffer.split('|')
                            obstacle_data = buffer[-1]
                            obstacle_data = ast.literal_eval(obstacle_data)
                            print(obstacle_data)
                            break
                except OSError as e:
                    print(e)
                    pass
                except KeyboardInterrupt:
                    client.close()
                    sys.exit(1)
                    print("Got data from RPi:")
        
        path_hist = []
        if hardcoded:
            obstacle_data = [[10, 190, 270, 1], [150, 160, 270, 2], [60, 120, 90, 3], [190, 90, 180, 4], [100, 70, 0, 5], [130, 20, 180, 6]]

        st = time.time() # start to receive the obstacle
        obstacles = parse_obstacle_data(obstacle_data)
        print("obstacles ", obstacles)
        
        app = AlgoMinimal(obstacles)
        order = app.execute() # [] all are based 1, but might in different order, for e.g: [8,4,3,1] and missing some as well
        obstacles_ordered = []
        for index in order:
            for obstacle in obstacles:
                if index == obstacle.index:
                    obstacles_ordered.append(obstacle)
        print("order", order)
        print("obstacle after ordered", obstacles_ordered)
        targets = get_relative_pos(obstacles_ordered, app.targets)
        commands = app.robot.convert_all_commands()
        
        ed = time.time()
        print("time to received the commands from beginning of received obstacles", ed-st)
        if waiting_rpi:
            print("Sending list of commands to RPi...", commands)
            client.send_message(target='RSP', data_type="ObsOrder", data=order)
            time.sleep(0.2)
            client.send_message(target='RSP', data_type="Targets", data=targets)
            time.sleep(0.2)
            client.send_message(target='ARD', data_type='Commands', data=commands)
        else:
            print(commands)

if __name__ == '__main__':
    run_minimal(True, False)

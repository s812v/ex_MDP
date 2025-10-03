import sys
import time
import ast
from typing import List

import algorithm.settings as settings
from algorithm.app import AlgoSimulator, AlgoMinimal
from algorithm.entities.assets.direction import Direction
from algorithm.entities.connection.algorithm_client import AlgorithmClient
from algorithm.entities.connection.algorithm_server import AlgorithmServer
from algorithm.entities.grid.obstacle import Obstacle


def parse_obstacle_data(data) -> List[Obstacle]:
    obs = []
    for obstacle_params in data:
        obs.append(Obstacle(obstacle_params[0]+5,
                            obstacle_params[1]+5,
                            Direction(obstacle_params[2]),
                            obstacle_params[3]))
    # [[x, y, orient, index], [x, y, orient, index]]
    return obs


def run_simulator():
    # Fill in obstacle positions with respect to lower bottom left corner.
    # (x-coordinate, y-coordinate, Direction, index)
    # obstacles = [[105, 75, 90, 0], [175, 25, 180, 1], [175, 175, 180, 2], [75, 125, 180, 3], [15, 185, -90, 4], [65, 25, 180, 5], [85, 185, -90, 6], [185, 95, 180, 7]]
    obstacles = [[50, 130, 0, 1], [60, 50, 90, 5], [140, 50, 180, 6], [130, 120, 270, 7]]
    obs = parse_obstacle_data(obstacles)
    app = AlgoSimulator(obs)
    order = app.init()
    print(order)
    cmds = app.robot.convert_all_commands()
    print(cmds)
    app.execute()


def run_minimal(also_run_simulator):
    # Create a client to connect to the RPi.
    print(f"Attempting to connect to {settings.RPI_HOST}:{settings.RPI_PORT}")
    client = AlgorithmClient(settings.RPI_HOST, settings.RPI_PORT)
    # Wait to connect to RPi.
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
        while True:
            try:
                buffer = client.receive_data()
                if buffer is None:
                    continue
                else:
                    buffer = buffer.decode()
                    buffer = buffer.split('|')
                    obstacle_data = buffer[-1]
                    obstacle_data = ast.literal_eval(obstacle_data)
                    print(obstacle_data)
                    break
            except Exception as e:
                print(e)
                continue
            print("Got data from RPi:")
        
        path_hist = []
        obstacles = parse_obstacle_data(obstacle_data)
        #order_and_commands = [[1, 2, 3, 4], ['P', 'LF090', 'P', 'LF090', 'P', 'LF090', 'P', 'finish']]
        order_and_commands = [[1,2,3,4], ['P', 'SF015', 'LF090','P', 'SF015', 'LF090', 'P', 'SF015', 'LF090', 'P', 'finish']]
        # order_and_commands = [[1], ['P', 'SF015', 'LF090','P]]
        # order_and_commands = [[5, 7, 1, 2, 4], ['RF090', 'SF050', 'LF090', 'P', 'SB020', 'RF090', 'SF020', 'P', 'SB010', 'LF090', 'SF050', 'RF090', 'SF040', 'P', 'SB010', 'LF090', 'SF060', 'P', 'SB020', 'LF090', 'P', 'finish']]
        
        order = order_and_commands[0]
        commands = order_and_commands[1]
        print(order, commands)
        client.send_message(target='RSP', data_type="ObsOrder", data=order)
        time.sleep(2)
        client.send_message(target='ARD', data_type='Commands', data=commands)

    client.close()

def run_rpi():
    while True:
        run_minimal(False)
        time.sleep(5)


if __name__ == '__main__':
    # run_simulator()
    run_minimal(True)
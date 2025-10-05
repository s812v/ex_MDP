import sys
import time
from typing import List

from algorithm import settings
from algorithm.app import AlgoSimulator, AlgoMinimal
from algorithm.entities.assets.direction import Direction
from algorithm.entities.connection.rpi_client import RPiClient
from algorithm.entities.connection.rpi_server import RPiServer
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
    # obstacles = [[105, 75, 90, 0], [175, 25, 180, 1], [175, 175, 180, 2], [75, 125, 180, 3], [65, 25, 180, 5]]
    obstacles = [[100,70,90,0],[170,20,180,1],[170,170,180,2],[70,120,180,3]]
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
    client = RPiClient(settings.RPI_HOST, settings.RPI_PORT)
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

    obstacle_data: list = client.receive_data()
    print("Got data from RPi:")
    print(obstacle_data)
    path_hist = []

    obstacles = parse_obstacle_data(obstacle_data)
    if also_run_simulator:
        app = AlgoSimulator(obstacles)
        app.init()
        app.execute()
        path_hist = app.robot.get_all_path_hist_by_command()
    app = AlgoMinimal(obstacles)
    app.init()
    order = app.execute()

    # Send the list of commands over.
    print("Sending list of commands to RPi...")
    commands = app.robot.convert_all_commands()
    order_and_commands = [order, commands, path_hist]
    client.send_message(order_and_commands)
    client.close()


def run_rpi():
    while True:
        run_minimal(False)
        time.sleep(5)


if __name__ == '__main__':
    run_simulator()
    # run_minimal(True)
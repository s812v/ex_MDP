import math
from typing import List, Dict, Tuple
from algorithm.entities.grid.obstacle import Obstacle
from algorithm.entities.grid.position import RobotPosition
from algorithm.entities.assets.direction import Direction
from algorithm.entities.commands.straight_command import StraightCommand
from algorithm.entities.commands.turn_command import TurnCommand
from algorithm.entities.commands.scan_command import ScanCommand
from algorithm.app import AlgoMinimal
from algorithm import settings
from PC.messages import StmCommandMessage, ImageRecognitionMessage, CommandsMessage  
# messages under PC or RPI

class AlgorithmIntegrate:
    def __init__(self):
        pass

    def obstacle_format_converter(self, obstacles_from_android: List[Dict]) -> List[Obstacle]:
        """
        Input: [{"id": 0, "x": 100, "y": 70, "image_side": "N"}, ...]
        Output: [Obstacle(105, 75, Direction.TOP, 0), ...]

            Direction: 0°=East, 90°=North, 180°=West, -90°=South

        """
        direction_map = {
            "N": Direction.TOP,  #90
            "E": Direction.RIGHT,  #0
            "S": Direction.BOTTOM,  #-90
            "W": Direction.LEFT    #180
        }

        obstacles = []

        for obs_data in obstacles_from_android:
            x = obs_data["x"] +5  #+5 offset needed? 
            y = obs_data["y"] +5
            direction = direction_map[obs_data["image_side"]]
            obs_id = obs_data["id"]
            # x = round((x - 5) / 10) * 10 + 5
            # y = round((y - 5) / 10) * 10 + 5

            obstacles.append(Obstacle(x,y, direction, obs_id))

        print(f"Converted {len(obstacles)} obstacles for algorithm")
        return obstacles
    
    def run_algorithm(self, obstacles_from_android: List[Dict]) -> Tuple[List[int], List[str]]:
        """
        Returns:
            (obstacle_order, detailed_commands)
            
        detailed_commands format:
        [
            {
                "type": "straight",
                "distance": 15.0,
                "start": {"x": 20, "y": 20, "theta": 90},
                "end": {"x": 20, "y": 35, "theta": 90}
            },
            {
                "type": "turn",
                "angle": 90,
                "reverse": False,
                "start": {"x": 20, "y": 35, "theta": 90},
                "end": {"x": 17.5, "y": 60, "theta": 180}  #X/Y changed due to arc
            },
            {
                "type": "scan",
                "obstacle_id": 0,
                "position": {"x": 100, "y": 70, "theta": 90}
            }
        ]
        """

        print("RUNNING PATH PLANNING ALGORITHM: ")

        obstacles = self.obstacle_format_converter(obstacles_from_android)

        print(f"\nObstacles loaded:")
        for obs in obstacles:
            x_cm = obs.pos.x / settings.SCALING_FACTOR   #in cm
            y_cm = obs.pos.y / settings.SCALING_FACTOR
            print(f"  - Obstacle {obs.index}: ({x_cm:.0f}, {y_cm:.0f}) facing {obs.pos.direction.name}")

        algo = AlgoMinimal(obstacles)
        algo.init()
        obstacle_order = algo.execute()

        print(f"Algorithm complete!")
        print(f"Obstacle visit order: {obstacle_order}")
        print(f"Total commands: {len(algo.robot.brain.commands)}")

     # Extract detailed commands with position data
        string_commands = []

        current_pos = RobotPosition(
            20.0 * settings.SCALING_FACTOR,
            20.0 * settings.SCALING_FACTOR,
            Direction.TOP,
            90.0
        )   #start position

        print("EXTRACTING POSITION DATA FROM COMMANDS")

        for i, command in enumerate(algo.robot.brain.commands):
            # Store starting position
            start_pos = current_pos.copy()
            
            if isinstance(command, StraightCommand):
                # Apply command to get end position
                command.apply_on_pos(current_pos)
                
                # De-scale positions back to cm
                distance_cm = command.dist / settings.SCALING_FACTOR
                
                cmd_data = {
                    "type": "straight",
                    "distance": round(distance_cm, 1),
                    "start": {
                        "x": round(start_pos.x / settings.SCALING_FACTOR, 1),
                        "y": round(start_pos.y / settings.SCALING_FACTOR, 1),
                        "theta": round(start_pos.angle, 1)
                    },
                    "end": {
                        "x": round(current_pos.x / settings.SCALING_FACTOR, 1),
                        "y": round(current_pos.y / settings.SCALING_FACTOR, 1),
                        "theta": round(current_pos.angle, 1)
                    }
                }
                
                string_commands.append(cmd_data)
                
                direction = "forward" if distance_cm > 0 else "backward"
                print(f"{i+1}. STRAIGHT {direction} {abs(distance_cm):.1f}cm")
                print(f"   Start: ({cmd_data['start']['x']:.1f}, {cmd_data['start']['y']:.1f}, {cmd_data['start']['theta']:.1f}°)")
                print(f"   End:   ({cmd_data['end']['x']:.1f}, {cmd_data['end']['y']:.1f}, {cmd_data['end']['theta']:.1f}°)")
                
            elif isinstance(command, TurnCommand):
                # Apply turn command - this calculates arc geometry
                command.apply_on_pos(current_pos)
                
                cmd_data = {
                    "type": "turn",
                    "angle": command.angle,
                    "reverse": command.rev,
                    "start": {
                        "x": round(start_pos.x / settings.SCALING_FACTOR, 1),
                        "y": round(start_pos.y / settings.SCALING_FACTOR, 1),
                        "theta": round(start_pos.angle, 1)
                    },
                    "end": {
                        "x": round(current_pos.x / settings.SCALING_FACTOR, 1),
                        "y": round(current_pos.y / settings.SCALING_FACTOR, 1),
                        "theta": round(current_pos.angle, 1)
                    }
                }
                
                string_commands.append(cmd_data)
                
                turn_dir = "LEFT" if command.angle > 0 else "RIGHT"
                move_dir = "forward" if not command.rev else "backward"
                print(f"{i+1}. TURN {turn_dir} {move_dir} ({command.angle:.0f}°)")
                print(f"   Start: ({cmd_data['start']['x']:.1f}, {cmd_data['start']['y']:.1f}, {cmd_data['start']['theta']:.1f}°)")
                print(f"   End:   ({cmd_data['end']['x']:.1f}, {cmd_data['end']['y']:.1f}, {cmd_data['end']['theta']:.1f}°)")
                print(f"   Arc dx: {cmd_data['end']['x'] - cmd_data['start']['x']:.1f}cm, dy: {cmd_data['end']['y'] - cmd_data['start']['y']:.1f}cm")
                
            elif isinstance(command, ScanCommand):
                cmd_data = {
                    "type": "scan",
                    "obstacle_id": command.obj_index,
                    "position": {
                        "x": round(current_pos.x / settings.SCALING_FACTOR, 1),
                        "y": round(current_pos.y / settings.SCALING_FACTOR, 1),
                        "theta": round(current_pos.angle, 1)
                    }
                }
                
                string_commands.append(cmd_data)
                
                print(f"{i+1}. SCAN obstacle {command.obj_index}")
                print(f"   Position: ({cmd_data['position']['x']:.1f}, {cmd_data['position']['y']:.1f}, {cmd_data['position']['theta']:.1f}°)")
        
        print("=" * 60)
        print(f"Extracted {len(string_commands)} commands with position data")
        print("=" * 60)


        return obstacle_order, string_commands
    

    def translate_to_stm_format(self, cmd: Dict) -> Dict:
        """
        Translate detailed command to STM format
        
        Input: {"type": "straight", "start": {...}, "end": {...}, ...}
        Output: {"action": "forward", "parameters": {"x": 20, "y": 35, "theta": 90}}
        """
        if cmd["type"] == "straight":
            distance = cmd["distance"]
            end = cmd["end"]
            
            return {
                "action": cmd["type"],
                "parameters": {
                    "distance" : distance
                }
            }
            
        elif cmd["type"] == "turn":
            # For turns, use the calculated end position (includes arc)
            reverse = cmd['reverse']
            # print ("turn: ",cmd)
            if reverse:
                angle = -90
            else:
                angle = 90
            if (cmd["angle"]* angle) > 0:
                action = "left" 
            else:
                action = "right"
            return {
                "action": action,
                "parameters": {
                    "angle": angle
                }
            }
            
        elif cmd["type"] == "scan":
            return {
                "action": "stop",
                "parameters": {
                    "obstacle_id": cmd["obstacle_id"],
                    # "x": cmd["position"]["x"],
                    # "y": cmd["position"]["y"],
                    # "theta": cmd["position"]["theta"]
                }
            }
        
        else:
            raise ValueError(f"Unknown command type: {cmd['type']}")
    

    def run_full_pipeline(self, obstacles_from_android: List[Dict]) -> Tuple[List[int], List[Dict]]:
        """
        Complete pipeline: Algorithm → Position extraction → STM format
        
        Returns:
            (obstacle_order, stm_commands)
        """
        # Run algorithm and get detailed commands
        obstacle_order, detailed_commands = self.run_algorithm(obstacles_from_android)
        
        # Translate to STM format
        stm_commands = []
        for cmd in detailed_commands:
            stm_cmd = self.translate_to_stm_format(cmd)
            stm_commands.append(stm_cmd)
        
        print(f"\nTranslated {len(stm_commands)} commands to STM format")
        
        return obstacle_order, stm_commands
    
    def build_commands(self,commands): 
        messages = []
        for cmd in commands:
            if cmd['action'] == 'stop':
                # message = StmCommandMessage(action=cmd['action'],parameter = cmd['parameters'])
                # messages.append(message)
                message = ImageRecognitionMessage(id = cmd['parameters'])
                messages.append(message)
            elif cmd['action'] == 'straight':
                message = StmCommandMessage(action = cmd['action'],parameter = cmd['parameters'])
                messages.append(message)
            else: # action == left or right
                message = StmCommandMessage(action = cmd['action'],parameter = cmd['parameters'])
                messages.append(message)
        messages.append(StmCommandMessage(action= 'finish',parameter=None))        
        number = len(messages)
        cmds = CommandsMessage(messages)
        return cmds


# Test function
def test_algorithm_integrate():
    """Test the wrapper with sample obstacles"""
    test_obstacles = [
        {"id": 0, "x": 60, "y": 50, "image_side": "S"},
        {"id": 3, "x": 130, "y": 80, "image_side": "W"},
        {"id": 2, "x": 50, "y": 150, "image_side": "S"},
        {"id": 1, "x": 90, "y": 150, "image_side": "S"}
    ]
    
    integrated = AlgorithmIntegrate()
    order, stm_commands = integrated.run_full_pipeline(test_obstacles)
    commands = integrated.build_commands(stm_commands)
    print("\n" + "=" * 60)
    print("FINAL OUTPUT")
    print("=" * 60)
    print(f"Visit order: {order}")
    print(f"\nFirst n STM commands:")
    # for i, cmd in enumerate(stm_commands):
    #     print(f"{i+1}. {cmd}")
    print(commands)


if __name__ == "__main__":
    test_algorithm_integrate()
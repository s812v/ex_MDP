# PyGame settings
SCALING_FACTOR = 4
FRAMES = 30
WINDOW_SIZE = 800, 800

# Connection to RPi
RPI_HOST: str = "192.168.28.28"
RPI_PORT: int = 1111

# Connection to PC
PC_HOST: str = "192.168.28.33"
PC_PORT: int = 2222

# Commands attributes
UNIT_STRAIGHT = 5 # in cm, each command straight should be divided by this number
 
# Robot Attributes
ROBOT_LENGTH = 25 * SCALING_FACTOR

# ROBOT_LEFT_TURN_RADIUS_X = 28 * SCALING_FACTOR # use 0.001 for in-place turns, or turn radius for 90-degree turns
ROBOT_RIGHT_TURN_RADIUS_X = 36 * SCALING_FACTOR # use 0.001 for in-place turns, or turn radius for 90-degree turns
# ROBOT_RIGHT_TURN_RADIUS_X = 28 * SCALING_FACTOR # use 0.001 for in-place turns, or turn radius for 90-degree turns
ROBOT_LEFT_TURN_RADIUS_X = 36 * SCALING_FACTOR # use 0.001 for in-place turns, or turn radius for 90-degree turns

# ROBOT_LEFT_TURN_RADIUS_Y = 28 * SCALING_FACTOR # use 0.001 for in-place turns, or turn radius for 90-degree turns
ROBOT_RIGHT_TURN_RADIUS_Y = 22 * SCALING_FACTOR # use 0.001 for in-place turns, or turn radius for 90-degree turns
# ROBOT_RIGHT_TURN_RADIUS_Y = 28 * SCALING_FACTORß # use 0.001 for in-place turns, or turn radius for 90-degree turns
ROBOT_LEFT_TURN_RADIUS_Y = 22 * SCALING_FACTOR # use 0.001 for in-place turns, or turn radius for 90-degree turns


ROBOT_SPEED_PER_SECOND = 50 * SCALING_FACTOR
ROBOT_LEFT_S_FACTOR = (ROBOT_LENGTH / ROBOT_LEFT_TURN_RADIUS_X + ROBOT_LENGTH / ROBOT_LEFT_TURN_RADIUS_Y)/2
ROBOT_RIGHT_S_FACTOR = (ROBOT_LENGTH / ROBOT_RIGHT_TURN_RADIUS_X + ROBOT_LENGTH / ROBOT_RIGHT_TURN_RADIUS_Y)/2
ROBOT_START_POSITION_X = 15 * SCALING_FACTOR
ROBOT_START_POSITION_Y = 15 * SCALING_FACTOR
ROBOT_SAFETY_DISTANCE = 15 * SCALING_FACTOR
ROBOT_SCAN_TIME = 2  # Time provided for scanning an obstacle image in seconds.

# Grid Attributes
GRID_LENGTH = 200 * SCALING_FACTOR
GRID_CELL_LENGTH = 5 * SCALING_FACTOR
GRID_START_BOX_LENGTH = 30 * SCALING_FACTOR
GRID_NUM_GRIDS = GRID_LENGTH // GRID_CELL_LENGTH

# Obstacle Attributes
OBSTACLE_LENGTH = 10 * SCALING_FACTOR
# OBSTACLE_SAFETY_WIDTH = ROBOT_SAFETY_DISTANCE // 3 * 3  # With respect to the center of the obstacle
OBSTACLE_SAFETY_WIDTH = 25 * SCALING_FACTOR # plus 10 from the center of the obstacle, but actual landed position, depends on the original position of the robot
OBSTACLE_TARGET_DISTANCE = 32 * SCALING_FACTOR
# if the robot is at the center of the obstacle, the robot will be safety+10-5 away from the obstacle

# Path Finding Attributes
PATH_TURN_COST = 99999 * ROBOT_SPEED_PER_SECOND * (ROBOT_RIGHT_TURN_RADIUS_X+ROBOT_RIGHT_TURN_RADIUS_Y)/2
# NOTE: Higher number == Lower Granularity == Faster Checking.
# Must be an integer more than 0! Number higher than 3 not recommended.
PATH_TURN_CHECK_GRANULARITY = 3

NUM_THREADS = 1
NUM_HAM_PATH_CHECK = 5

multi_threading = False
lower_bound=3
upper_bound=10
lower_bound_side=5
upper_bound_side=10

peak_horizontal_tolerance = 15
minimum_vertical = 500
maximum_vertical = 700# mm
angle_peak_threshold = 8 # degree
left_pixel_threshold = 200
right_pixel_threshold = 800
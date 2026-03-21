# joystick.launch.py
#
# Launches teleoperation nodes for controlling the robot.
# It does the following:
#   1. Reads joystick/teleop parameters from config/joystick.yaml.
#   2. Launches a joystick teleop node (teleop_twist_joy) if teleop_type is 'joystick'.
#   3. Launches a keyboard teleop node (teleop_twist_keyboard in an xterm window)
#      if teleop_type is 'keyboard'.
# Both controllers publish velocity commands to /diff_cont/cmd_vel_unstamped.
# Note: the joy_node (raw joystick input) is currently commented out.

from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory
from launch.conditions import IfCondition, UnlessCondition, LaunchConfigurationEquals

def generate_launch_description():

    joy_params = os.path.join(get_package_share_directory('my_bot_one'),'config','joystick.yaml')

    joy_node = Node(
            package='joy',
            executable='joy_node',
            parameters=[joy_params],
         )
    
    teleop_node = Node(
            package='teleop_twist_joy', 
            executable='teleop_node',
            name = 'teleop_node',
            condition=LaunchConfigurationEquals('teleop_type', 'joystick'),
            parameters=[joy_params],
            remappings=[('/cmd_vel', '/diff_cont/cmd_vel_unstamped')]
            )
    
    teleop_keyboard_node = Node(
            package='teleop_twist_keyboard',
            executable='teleop_twist_keyboard',
            name = 'teleop_twist_keyboard',
            condition=LaunchConfigurationEquals('teleop_type', 'keyboard'),
            output='screen',
            prefix='xterm -e',
            remappings=[('/cmd_vel', '/diff_cont/cmd_vel_unstamped')]
            )

    return LaunchDescription([
        #joy_node,
        teleop_node,
        teleop_keyboard_node
    ])
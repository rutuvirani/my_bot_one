# rsp.launch.py (Robot State Publisher)
#
# Processes the robot URDF/XACRO description and starts the robot_state_publisher node.
# It does the following:
#   1. Processes robot.urdf.xacro with runtime arguments (use_ros2_control, sim_mode)
#      using the xacro command to produce a complete URDF XML string.
#   2. Starts the robot_state_publisher node with the processed robot description,
#      which publishes TF transforms for all robot links based on joint states.
#
# Launch arguments:
#   use_sim_time    -- true/false, enables Gazebo simulation clock (default: true)
#   use_ros2_control -- true/false, enables ros2_control hardware interface (default: true)

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node

import xacro


def generate_launch_description():

    # Check if we're told to use sim time
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_ros2_control = LaunchConfiguration('use_ros2_control')

    # Process the URDF file
    pkg_path = os.path.join(get_package_share_directory('my_bot_one'))
    xacro_file = os.path.join(pkg_path,'description','robot.urdf.xacro')

    # below syntax give string
    # robot_description_config = xacro.process_file(xacro_file).toxml()
    ''' 
    
    The command is used to dynamically process the robot description file (robot.urdf.xacro) 
    with runtime parameters. It constructs and executes a shell command to process the XACRO file, 
    applying conditional parameters for ROS2 control and simulation mode. The output is a complete 
    URDF XML string containing the robot's description, which is then used by the robot_state_publisher 
    node to maintain and publish the robot's state information.
    
    '''
    robot_description_config = Command(['xacro ', xacro_file, ' use_ros2_control:=', use_ros2_control, ' sim_mode:=', use_sim_time])
    
    # Create a robot_state_publisher node
    params = {'robot_description': robot_description_config, 'use_sim_time': use_sim_time}
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[params]
    )


    # Launch!
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use sim time if true'),
        DeclareLaunchArgument(
            'use_ros2_control',
            default_value='true',
            description='Use ros2_control if true'),

        node_robot_state_publisher
    ])
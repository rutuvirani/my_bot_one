import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, GroupAction
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.actions import RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit # used to put delay


def generate_launch_description():

    # Include the rsp.launch.py(robot_state_publisher)
    #  file, force sim time to enable

    package_name='my_bot_one'
    pkg_share = get_package_share_directory(package_name)

    teleop_type = DeclareLaunchArgument(
        'teleop_type',
        description='Type of teleoperation to move bot (joystick or keyboard).',
        choices=['joystick', 'keyboard', 'none']
    )

    map_file_arg = DeclareLaunchArgument(
    'map_file',
    default_value=os.path.join(os.path.expanduser('~'), 'learn_ros_ws/src/my_bot_one/recorded_map/test_map.yaml'),
    description='Full path to map yaml file'
    )

    use_sim_time_arg = DeclareLaunchArgument(
    'use_sim_time',
    default_value='true',
    description='Use simulation (Gazebo) clock if true'
    )

    localization_type_arg = DeclareLaunchArgument(
    'localization_type',
    default_value='amcl',
    description='Localization method: slam_toolbox or amcl',
    choices=['slam_toolbox', 'amcl']
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_file = LaunchConfiguration('map_file')
    localization_type = LaunchConfiguration('localization_type')

    params = LaunchConfiguration('teleop_type')
    # Only include joystick launch if teleop_type is not 'none'
    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory(package_name), 'launch', 'joystick.launch.py'
        )),
        launch_arguments={'teleop_type': params}.items(),
        condition=IfCondition(PythonExpression(["'", params, "' != 'none'"]))
    )


    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory(package_name),'launch','rsp.launch.py'
        )), launch_arguments={'force_sim_time': 'true', 'use_ros2_control': 'true'}.items()
    )

    # joystick = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource(os.path.join(
    #         get_package_share_directory(package_name), 'launch', 'joystick.launch.py'
    #     )),
    #     launch_arguments={'teleop_type': params}.items()
    # )
    gazebo_params_file = os.path.join(get_package_share_directory(package_name),'config','gazebo_params.yaml')

    # Include  Gazebo launch file, provided by the gazebo_ros package
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource(os.path.join(
                    get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py'
                    )), launch_arguments={'world': 'src/my_bot_one/world/myworld.world', 'extra_gazebo_args': '--ros-args --params-file' + gazebo_params_file}.items()
    )

    # Run the spawner node from the gazebo_ros package

    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description', '-entity', 'my_bot'],
                        output='screen')
    

    # Robot localization node (for better odometry)
    robot_localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[
            os.path.join(pkg_share, 'config', 'ekf.yaml'),
            {'use_sim_time': True}
        ]
    )

    slam_config_file = os.path.join(pkg_share, 'config', 'slam_config.yaml')
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_config_file,
            {'use_sim_time': True}
        ]
    )

    # We have many methods for controller such as service, but we use spawn method

    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],
    )

    delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[diff_drive_spawner],
        )
    )

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
    )

    delayed_joint_broad_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_entity,
            on_exit=[joint_broad_spawner],
        )
    )

    controller_params_file = os.path.join(pkg_share, 'config', 'my_controllers.yaml')
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[controller_params_file],
        output='screen'
    )


    delayed_controller_manager = TimerAction(
        period=3.0,
        actions=[controller_manager]
    )

       # Map Server - loads your saved map
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'yaml_filename': map_file}
        ]
    )
    
    # Map Server Lifecycle Manager
    map_server_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='map_server_lifecycle_manager',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'autostart': True},
            {'node_names': ['map_server']}
        ]
    )
    
    # SLAM Toolbox Localization Mode
    slam_localization_config = os.path.join(pkg_share, 'config', 'localization_config.yaml')
    slam_localization_node = Node(
        package='slam_toolbox',
        executable='localization_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_localization_config,
            {'use_sim_time': use_sim_time}
        ]
    )
    
    # AMCL Localization (alternative to SLAM Toolbox)
    amcl_config = os.path.join(pkg_share, 'config', 'amcl_config.yaml')
    amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[
            amcl_config,
            {'use_sim_time': use_sim_time}
        ]
    )
    
    # AMCL Lifecycle Manager
    amcl_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='amcl_lifecycle_manager',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'autostart': True},
            {'node_names': ['amcl']}
        ]
    )

# Navigation2 parameters
    nav2_params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')

    # Navigation2 nodes
    nav2_nodes = GroupAction([
        # Behavior Tree Navigator
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[
                nav2_params_file,
                {'use_sim_time': use_sim_time}
            ]
        ),

        # Planner Server
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[
                nav2_params_file,
                {'use_sim_time': use_sim_time}
            ]
        ),

        # Controller Server
        Node(
            package='nav2_controller',
            executable='controller_server',
            output='screen',
            parameters=[
                nav2_params_file,
                {'use_sim_time': use_sim_time}
            ],
            remappings=[('cmd_vel', '/diff_cont/cmd_vel_unstamped'   
            )]
        ),

        # Smoother Server
        Node(
            package='nav2_smoother',
            executable='smoother_server',
            name='smoother_server',
            output='screen',
            parameters=[
                nav2_params_file,
                {'use_sim_time': use_sim_time}
            ]
        ),

        # Behavior Server
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=[
                nav2_params_file,
                {'use_sim_time': use_sim_time}
            ]
        ),

        # Velocity Smoother
        Node(
            package='nav2_velocity_smoother',
            executable='velocity_smoother',
            name='velocity_smoother',
            output='screen',
            parameters=[
                nav2_params_file,
                {'use_sim_time': use_sim_time}
            ],
            remappings=[('cmd_vel', 'cmd_vel_nav'), ('cmd_vel_smoothed', '/diff_cont/cmd_vel_unstamped')]
        ),

        # Waypoint Follower
        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[
                nav2_params_file,
                {'use_sim_time': use_sim_time}
            ]
        ),
    ])

    # Lifecycle Manager for Navigation2
    nav2_lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='navigation_lifecycle_manager',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'autostart': True},
            {'node_names': [
                'bt_navigator',
                'planner_server', 
                'controller_server',
                'smoother_server',
                'behavior_server',
                'waypoint_follower',
                'velocity_smoother'
            ]}
        ]
    )

    # RViz with Navigation
    rviz_config_file = os.path.join(pkg_share, 'config', 'navigation_config.rviz')
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Delayed starts - wait for localization to be ready
    delayed_nav2_nodes = TimerAction(
        period=8.0,
        actions=[nav2_nodes]
    )

    delayed_nav2_lifecycle = TimerAction(
        period=10.0,
        actions=[nav2_lifecycle_manager]
    )

    
    # Delayed localization start
    delayed_map_server = TimerAction(
        period=6.0,
        actions=[map_server_node, map_server_manager]
    )
    
    delayed_slam_localization = TimerAction(
        period=7.0,
        actions=[slam_localization_node]
    )
    
    delayed_amcl = TimerAction(
        period=8.0,
        actions=[amcl_node, amcl_manager]
    )



    # Launch all!
    return LaunchDescription([
        use_sim_time_arg,
        map_file_arg,
        localization_type_arg,
        teleop_type,
        rsp,
        gazebo,
        spawn_entity,
        delayed_controller_manager,
        delayed_diff_drive_spawner,
        delayed_joint_broad_spawner,
        joystick,
        # robot_localization_node,
        # slam_toolbox_node
        # delayed_map_server,
        delayed_slam_localization,  # Comment this out to use AMCL
        # delayed_amcl,
        delayed_nav2_nodes,
        delayed_nav2_lifecycle,

        ])
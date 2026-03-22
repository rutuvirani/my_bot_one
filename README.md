# my_bot_one

A ROS2 differential-drive robot package with Gazebo simulation, SLAM, localization, and autonomous navigation using Nav2.

---

## Robot Overview

- **Type**: Differential-drive (2 driven wheels + 1 caster)
- **Chassis**: 0.3 × 0.3 × 0.15 m, 0.5 kg
- **Wheel separation**: 0.35 m | **Wheel radius**: 0.05 m
- **Sensor**: 360° LiDAR, 0.3–12 m range, 10 Hz, published to `/scan`
- **Control**: ros2_control with `diff_drive_controller`

---

## Package Structure

```
my_bot_one/
├── config/
│   ├── my_controllers.yaml     # ros2_control: diff_cont + joint_broad
│   ├── nav2_params.yaml        # Full Nav2 stack parameters
│   ├── slam_config.yaml        # SLAM Toolbox (mapping mode)
│   ├── localization_config.yaml# SLAM Toolbox (localization mode)
│   ├── amcl_config.yaml        # AMCL localization (alternative)
│   ├── ekf.yaml                # robot_localization EKF
│   ├── joystick.yaml           # Joy + teleop_twist_joy config
│   ├── gazebo_params.yaml      # Gazebo publish rate
│   └── twist_mux.yaml          # Velocity priority multiplexer
├── description/
│   ├── robot.urdf.xacro        # Top-level robot description
│   ├── robot_core.xacro        # Links, joints, chassis geometry
│   ├── lidar.xacro             # LiDAR sensor + Gazebo plugin
│   ├── ros2_control.xacro      # ros2_control hardware interface
│   ├── gazebo_control.xacro    # Gazebo diff drive plugin (alternative)
│   └── inertial_macros.xacro   # Inertia helper macros
├── launch/
│   ├── launch_sim.launch.py    # Full simulation + Nav2 (main entry point)
│   ├── launch_robot.launch.py  # Real hardware bringup (no Gazebo)
│   ├── rsp.launch.py           # Robot State Publisher
│   └── joystick.launch.py      # Teleoperation nodes
├── scripts/
│   ├── simple_navigation.py    # Sends a sequence of Nav2 goals
│   └── cmd_vel_bridge.py       # Bridges cmd_vel topics to diff_cont
├── recorded_map/
│   ├── test_map.yaml           # Saved map for AMCL/Nav2
│   └── slam_map.*              # Saved SLAM Toolbox map
└── world/
    └── myworld.world           # Gazebo world with obstacles
```

---

## Dependencies

```xml
gazebo_ros
slam_toolbox
robot_localization
nav2_map_server
sensor_msgs
rclcpp
std_msgs
```

Install Nav2 and other runtime deps:
```bash
sudo apt install ros-$ROS_DISTRO-navigation2 ros-$ROS_DISTRO-nav2-bringup \
  ros-$ROS_DISTRO-slam-toolbox ros-$ROS_DISTRO-robot-localization \
  ros-$ROS_DISTRO-gazebo-ros-pkgs ros-$ROS_DISTRO-ros2-control \
  ros-$ROS_DISTRO-ros2-controllers ros-$ROS_DISTRO-teleop-twist-joy \
  ros-$ROS_DISTRO-teleop-twist-keyboard
```

---

## Build

```bash
cd ~/learn_ros_ws
colcon build --symlink-install
source install/setup.bash
```

---

## Running the Simulation

### Launch Gazebo + Nav2 (keyboard teleop)
```bash
ros2 launch my_bot_one launch_sim.launch.py teleop_type:=keyboard
```

### Launch with joystick teleop
```bash
ros2 launch my_bot_one launch_sim.launch.py teleop_type:=joystick
```

### Launch without teleop (autonomous only)
```bash
ros2 launch my_bot_one launch_sim.launch.py teleop_type:=none
```

### Optional arguments
| Argument | Default | Description |
|---|---|---|
| `teleop_type` | *(required)* | `joystick`, `keyboard`, or `none` |
| `use_sim_time` | `true` | Use Gazebo clock |
| `map_file` | `recorded_map/test_map.yaml` | Path to map YAML |
| `localization_type` | `amcl` | `slam_toolbox` or `amcl` |

---

## Mapping (SLAM)

To build a new map, set `mode: mapping` in `config/slam_config.yaml`, then drive the robot around with teleoperation. Save the map:

```bash
# Save as PGM/YAML (for AMCL / map_server)
ros2 run nav2_map_server map_saver_cli -f ~/learn_ros_ws/src/my_bot_one/recorded_map/test_map

# Save SLAM Toolbox serialized map (for slam_toolbox localization mode)
ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap "name: {data: 'slam_map'}"
```

---

## Localization Options

| Method | Config file | When to use |
|---|---|---|
| SLAM Toolbox (localization mode) | `localization_config.yaml` | More accurate, uses `.posegraph` map |
| AMCL | `amcl_config.yaml` | Lighter weight, uses `.pgm`/`.yaml` map |

Switch in `launch_sim.launch.py` by commenting/uncommenting `delayed_slam_localization` vs `delayed_amcl`.

---

## Navigation

Nav2 starts automatically with `launch_sim.launch.py`. Use RViz to:
1. Set the **Initial Pose** (2D Pose Estimate)
2. Send a **Nav2 Goal** (Navigation2 Goal)

Or use the provided script to send goals programmatically:
```bash
ros2 run my_bot_one simple_navigation.py
```
Edit the `goals` list in the script to set your waypoints.

---

## Real Robot Bringup

For physical hardware (no Gazebo):
```bash
ros2 launch my_bot_one launch_robot.launch.py
```
This starts the Robot State Publisher, controller manager, `diff_cont`, and `joint_broad`. Localization and Nav2 are not included — extend this file for a full real-robot stack.

---

## Joystick Configuration

Default mapping (`config/joystick.yaml`):
- **Left stick vertical** → linear velocity (axis 1)
- **Left stick horizontal** → angular velocity (axis 0)
- **LB (button 6)** → enable movement
- **RB (button 7)** → turbo mode (2× speed)
- Device: `/dev/input/js2` (change `device_id` if different)

---

## Key Topics

| Topic | Type | Description |
|---|---|---|
| `/scan` | `sensor_msgs/LaserScan` | LiDAR data |
| `/odom` | `nav_msgs/Odometry` | Wheel odometry |
| `/diff_cont/cmd_vel_unstamped` | `geometry_msgs/Twist` | Robot velocity command |
| `/map` | `nav_msgs/OccupancyGrid` | Current map |
| `/tf` | `tf2_msgs/TFMessage` | Transform tree |

---

## Maintainer

Rutvik Virani — viranirutvik1@gmail.com
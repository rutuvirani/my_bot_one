#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class CmdVelBridge(Node):
    def __init__(self):
        super().__init__('cmd_vel_bridge')
        
        # Subscribe to navigation commands
        self.nav_sub = self.create_subscription(
            Twist,
            '/cmd_vel_nav',  # From navigation
            self.nav_callback,
            10
        )
        
        # Subscribe to velocity smoother output
        self.smoother_sub = self.create_subscription(
            Twist,
            '/cmd_vel_smoothed',  # From velocity smoother
            self.smoother_callback,
            10
        )
        
        # Publish to robot controller
        self.robot_pub = self.create_publisher(
            Twist,
            '/diff_cont/cmd_vel_unstamped',  # To robot
            10
        )
        
        self.get_logger().info("Velocity bridge started")
        self.get_logger().info("Bridging: /cmd_vel_nav -> /diff_cont/cmd_vel_unstamped")
    
    def nav_callback(self, msg):
        """Forward navigation commands to robot"""
        self.robot_pub.publish(msg)
        self.get_logger().info(f"Forwarded nav cmd: linear={msg.linear.x:.2f}, angular={msg.angular.z:.2f}")
    
    def smoother_callback(self, msg):
        """Forward smoothed commands to robot"""
        self.robot_pub.publish(msg)
        self.get_logger().info(f"Forwarded smoothed cmd: linear={msg.linear.x:.2f}, angular={msg.angular.z:.2f}")

def main():
    rclpy.init()
    
    try:
        bridge = CmdVelBridge()
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
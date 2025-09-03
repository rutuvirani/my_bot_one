#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
import math

class DirectNavigator(Node):
    def __init__(self):
        super().__init__('direct_navigator')
        
        # Create action client for navigation
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        
        # Wait for action server
        self.get_logger().info("Waiting for navigation action server...")
        self._action_client.wait_for_server()
        self.get_logger().info("Navigation action server ready!")
        
        # Example goals - modify these coordinates for your map
        self.goals = [
            {'x': 0.0, 'y': 0.0, 'yaw': 0.0, 'name': 'Goal 1'},
            {'x': -1.0, 'y': 2.0, 'yaw': 1.57, 'name': 'Goal 2'},
            {'x': 0.0, 'y': 0.0, 'yaw': 0.0, 'name': 'Home'},
        ]
        
        self.current_goal_index = 0
        self.navigate_to_next_goal()
    
    def create_pose_stamped(self, x, y, yaw):
        """Create a PoseStamped message"""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        
        # Convert yaw to quaternion
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        
        return pose
    
    def navigate_to_next_goal(self):
        """Navigate to the next goal in the list"""
        if self.current_goal_index >= len(self.goals):
            self.get_logger().info("All goals completed!")
            return
        
        goal = self.goals[self.current_goal_index]
        self.get_logger().info(f"Navigating to {goal['name']}: ({goal['x']}, {goal['y']})")
        
        # Create navigation goal
        nav_goal = NavigateToPose.Goal()
        nav_goal.pose = self.create_pose_stamped(goal['x'], goal['y'], goal['yaw'])
        
        # Send goal
        self._send_goal_future = self._action_client.send_goal_async(
            nav_goal, 
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)
    
    def goal_response_callback(self, future):
        """Handle goal response"""
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return
        
        self.get_logger().info('Goal accepted')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)
    
    def get_result_callback(self, future):
        """Handle navigation result"""
        result = future.result().result
        goal_name = self.goals[self.current_goal_index]['name']
        
        if result:
            self.get_logger().info(f'Successfully reached {goal_name}!')
        else:
            self.get_logger().info(f'Failed to reach {goal_name}')
        
        # Move to next goal
        self.current_goal_index += 1
        
        # Wait a bit then go to next goal
        self.create_timer(2.0, self.navigate_to_next_goal)
    
    def feedback_callback(self, feedback_msg):
        """Handle navigation feedback"""
        feedback = feedback_msg.feedback
        distance = feedback.distance_remaining
        # self.get_logger().info(f'Distance remaining: {distance:.2f} meters')

def main():
    rclpy.init()
    
    try:
        navigator = DirectNavigator()
        rclpy.spin(navigator)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
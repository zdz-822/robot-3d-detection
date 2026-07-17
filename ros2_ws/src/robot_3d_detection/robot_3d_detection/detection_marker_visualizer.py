"""Convert 3D detection messages into RViz MarkerArray boxes and labels."""

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from vision_msgs.msg import Detection3DArray


CLASS_COLORS = {
    "car": (1.0, 0.35, 0.10),
    "truck": (1.0, 0.72, 0.0),
    "bus": (0.35, 0.62, 0.95),
    "pedestrian": (1.0, 0.82, 0.25),
    "bicycle": (0.0, 0.84, 0.62),
    "motorcycle": (0.94, 0.28, 0.44),
}


class DetectionMarkerVisualizer(Node):
    def __init__(self):
        super().__init__("detection_marker_visualizer")
        self.declare_parameter("input_topic", "/perception/detections")
        self.declare_parameter("marker_topic", "/perception/markers")
        self.publisher = self.create_publisher(MarkerArray, self.get_parameter("marker_topic").value, 10)
        self.subscription = self.create_subscription(
            Detection3DArray, self.get_parameter("input_topic").value, self.on_detections, 10
        )
        self.get_logger().info(
            f"Visualizing {self.get_parameter('input_topic').value} on "
            f"{self.get_parameter('marker_topic').value}"
        )

    def on_detections(self, message):
        markers = MarkerArray()
        clear = Marker()
        clear.action = Marker.DELETEALL
        markers.markers.append(clear)
        for index, detection in enumerate(message.detections):
            if not detection.results:
                continue
            hypothesis = detection.results[0].hypothesis
            class_name = hypothesis.class_id
            score = hypothesis.score
            red, green, blue = CLASS_COLORS.get(class_name, (0.92, 0.92, 0.92))
            box = Marker()
            box.header = message.header
            box.ns = "detection_boxes"
            box.id = index * 2
            box.type = Marker.CUBE
            box.action = Marker.ADD
            box.pose = detection.bbox.center
            box.scale = detection.bbox.size
            box.color.r, box.color.g, box.color.b, box.color.a = red, green, blue, 0.45
            box.lifetime = Duration(seconds=1.5).to_msg()
            markers.markers.append(box)

            label = Marker()
            label.header = message.header
            label.ns = "detection_labels"
            label.id = index * 2 + 1
            label.type = Marker.TEXT_VIEW_FACING
            label.action = Marker.ADD
            label.pose = detection.bbox.center
            label.pose.position.z += detection.bbox.size.z / 2.0 + 0.35
            label.scale.z = 0.35
            label.color.r, label.color.g, label.color.b, label.color.a = red, green, blue, 1.0
            label.text = f"{class_name} {score:.2f}"
            label.lifetime = Duration(seconds=1.5).to_msg()
            markers.markers.append(label)
        self.publisher.publish(markers)
        self.get_logger().info(f"Published {len(markers.markers) - 1} visualization markers")


def main():
    rclpy.init()
    node = DetectionMarkerVisualizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

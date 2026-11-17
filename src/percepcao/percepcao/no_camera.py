import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2 as cv
from cv_bridge import CvBridge


class NoCamera(Node):
    def __init__(self):
        super().__init__("no_camera")
        self.captura = cv.VideoCapture(0)
        self.publisher = self.create_publisher(Image, '/camera/imagem', 1)
        self.timer = self.create_timer(1/30, self.publica)
        self.bridge = CvBridge()

    def publica(self):
        ok, quadro = self.captura.read()
        if not ok:
            self.get_logger().warning("Falha ao ler quadro da câmera")
            return
        
        msg = self.bridge.cv2_to_imgmsg(quadro, encoding="bgr8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_frame'
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    no = NoCamera()
    try:
        rclpy.spin(no)
    except KeyboardInterrupt:
        pass
    finally:
        no.captura.release()
        no.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
        
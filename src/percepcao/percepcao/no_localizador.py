import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool


class NoLocalizadorAlvo(Node):
    def __init__(self):
        super().__init__("no_localizador_alvo")
        self.declare_parameter("lado_real_m", 0.0)
        self.declare_parameter("foco_px", 0.0)
        self.declare_parameter("centro_x_px", 320.0)
        self.declare_parameter("centro_y_px", 240.0)

        self.lado_real_m = self.get_parameter("lado_real_m").get_parameter_value().double_value
        self.foco_px = self.get_parameter("foco_px").get_parameter_value().double_value
        self.centro_x_px = self.get_parameter("centro_x_px").get_parameter_value().double_value
        self.centro_y_px = self.get_parameter("centro_y_px").get_parameter_value().double_value

        if self.lado_real_m <= 0.0 or self.foco_px <= 0.0:
            self.get_logger().warning("lado_real_m ou foco_px não calibrados (<= 0.0); /alvo/pose não será publicado.")

        self.pub_pose = self.create_publisher(PoseStamped, "/alvo/pose", 1)
        self.pub_visivel = self.create_publisher(Bool, "/alvo/visivel", 1)
        self.assinatura = self.create_subscription(
            Detection2DArray, "/visao/deteccoes", self.ao_receber_deteccoes, 1
        )

    def ao_receber_deteccoes(self, msg):
        visivel = Bool()
        if not msg.detections or self.lado_real_m <= 0.0 or self.foco_px <= 0.0:
            visivel.data = False
            self.pub_visivel.publish(visivel)
            return

        det = max(msg.detections, key=lambda d: d.results[0].hypothesis.score)
        lado_px = (det.bbox.size_x + det.bbox.size_y) / 2.0
        if lado_px <= 0.0:
            visivel.data = False
            self.pub_visivel.publish(visivel)
            return

        z = (self.foco_px * self.lado_real_m) / lado_px
        x = ((det.bbox.center.position.x - self.centro_x_px) * z) / self.foco_px
        y = ((det.bbox.center.position.y - self.centro_y_px) * z) / self.foco_px

        pose = PoseStamped()
        pose.header = msg.header
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = float(z)
        pose.pose.orientation.w = 1.0

        visivel.data = True
        self.pub_visivel.publish(visivel)
        self.pub_pose.publish(pose)
def main(args=None):
    rclpy.init(args=args)
    no = NoLocalizadorAlvo()
    try:
        rclpy.spin(no)
    except KeyboardInterrupt:
        pass
    finally:
        no.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
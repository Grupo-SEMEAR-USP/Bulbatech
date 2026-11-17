import rclpy
import os
from ament_index_python.packages import get_package_share_directory
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge
from percepcao.detector_yolo import DetectorYolo

class NoDetector(Node):
    def __init__(self):
        super().__init__("no_detector")
        self.bridge = CvBridge()
        pkg_share = get_package_share_directory("percepcao")
        pesos_padrao = os.path.join(pkg_share, "weights", "best.pt")
        repo_padrao = os.environ.get("YOLOV5_REPO", os.path.expanduser("~/yolov5"))

        self.declare_parameter("caminho_repo", repo_padrao)
        self.declare_parameter("caminho_pesos", pesos_padrao)
        self.declare_parameter("confianca_minima", 0.5)
        self.declare_parameter("classes_aceitas", ["SOL"])
        
        caminho_repo = self.get_parameter("caminho_repo").get_parameter_value().string_value
        caminho_pesos = self.get_parameter("caminho_pesos").get_parameter_value().string_value
        confianca_minima = self.get_parameter("confianca_minima").get_parameter_value().double_value
        classes_aceitas = self.get_parameter("classes_aceitas").get_parameter_value().string_array_value
        self.detector = DetectorYolo(caminho_repo, caminho_pesos, confianca_minima, classes_aceitas)

        
        self.publicador = self.create_publisher(Detection2DArray, "/visao/deteccoes", 1)
        
        self.assinatura = self.create_subscription(Image, "/camera/imagem", self.ao_receber_quadro, 1)

    def ao_receber_quadro(self, msg):
        
        quadro = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        deteccoes = self.detector.detecta(quadro)

        saida = Detection2DArray()
        saida.header = msg.header
        for x_min, y_min, x_max, y_max, confianca, nome in deteccoes:
            det = Detection2D()
            det.bbox.center.position.x = (x_max + x_min) / 2
            det.bbox.center.position.y = (y_max + y_min) / 2
            det.bbox.center.theta = 0.0
            det.bbox.size_x,det.bbox.size_y = ((x_max-x_min)**2)**(1/2),((y_max-y_min)**2)**(1/2)

            hipotese = ObjectHypothesisWithPose()
            hipotese.hypothesis.class_id = nome
            hipotese.hypothesis.score = confianca

            det.results.append(hipotese)

            saida.detections.append(det)

        self.publicador.publish(saida)


def main(args=None):
    rclpy.init(args=args)
    no = NoDetector()
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
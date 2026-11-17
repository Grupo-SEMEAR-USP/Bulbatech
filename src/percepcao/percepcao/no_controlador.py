import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool


class NoControlador(Node):
    def __init__(self):
        super().__init__("no_controlador")
        self.declare_parameter("largura_imagem_px", 640.0)
        self.declare_parameter("altura_imagem_px", 480.0)
        self.declare_parameter("alfa_ema", 0.4)             
        self.declare_parameter("deteccoes_para_travar", 3)  
        self.declare_parameter("perdidos_para_soltar", 5)   
        self.declare_parameter("ganho_angular", 1.0)
        self.declare_parameter("velocidade_linear", 0.1)
        self.declare_parameter("limiar_perto_liga", 0.30)   
        self.declare_parameter("limiar_perto_desliga", 0.25)
        

        self.largura_imagem_px = self.get_parameter("largura_imagem_px").get_parameter_value().double_value
        self.altura_imagem_px = self.get_parameter("altura_imagem_px").get_parameter_value().double_value
        self.alfa_ema = self.get_parameter("alfa_ema").get_parameter_value().double_value
        self.deteccoes_para_travar = self.get_parameter("deteccoes_para_travar").get_parameter_value().integer_value
        self.perdidos_para_soltar = self.get_parameter("perdidos_para_soltar").get_parameter_value().integer_value
        self.ganho_angular = self.get_parameter("ganho_angular").get_parameter_value().double_value
        self.velocidade_linear = self.get_parameter("velocidade_linear").get_parameter_value().double_value
        self.limiar_perto_liga = self.get_parameter("limiar_perto_liga").get_parameter_value().double_value
        self.limiar_perto_desliga = self.get_parameter("limiar_perto_desliga").get_parameter_value().double_value

        # Estado
        self.cx_filtrado = None
        self.tamanho_filtrado = None
        self.consecutivas = 0
        self.perdidas = 0
        self.travado = False
        self.perto = False

        self.pub_cmd = self.create_publisher(Twist, "/cmd_vel", 1)
        self.pub_perto = self.create_publisher(Bool, "/alvo/pronto_para_garra", 1)
        self.assinatura = self.create_subscription(Detection2DArray, "/visao/deteccoes", self.ao_receber_deteccoes, 1)
        

    def ao_receber_deteccoes(self, msg):
        if not msg.detections:
            self.registra_perda()
            return
        
        det = max(msg.detections, key=lambda d: d.results[0].hypothesis.score)
        cx = det.bbox.center.position.x
        tamanho = det.bbox.size_y / self.altura_imagem_px   

        if self.cx_filtrado is None:
            self.cx_filtrado = cx
        else:
            self.cx_filtrado = self.alfa_ema * cx + (1 - self.alfa_ema) * self.cx_filtrado

        if self.tamanho_filtrado is None:
            self.tamanho_filtrado = tamanho
        else:
            self.tamanho_filtrado = self.alfa_ema * tamanho + (1 - self.alfa_ema) * self.tamanho_filtrado

        self.perdidas = 0
        self.consecutivas += 1
        if self.consecutivas >= self.deteccoes_para_travar:
            self.travado = True

        if self.tamanho_filtrado > self.limiar_perto_liga:
            self.perto = True
        elif self.tamanho_filtrado < self.limiar_perto_desliga:
            self.perto = False
        
        self.publica_comando()

    def registra_perda(self):
        self.consecutivas = 0
        self.perdidas += 1
        if self.perdidas >= self.perdidos_para_soltar:
            self.travado = False
            self.perto = False
            self.cx_filtrado = None
            self.tamanho_filtrado = None
        self.publica_comando()

    def publica_comando(self):
        cmd = Twist()
        if self.travado:
            
            erro = (self.cx_filtrado - self.largura_imagem_px/2) / (self.largura_imagem_px/2)
            cmd.angular.z = -self.ganho_angular * erro 
            if not self.perto:
                cmd.linear.x = self.velocidade_linear 
            else:
                cmd.linear.x = 0.0
        self.pub_cmd.publish(cmd)
        pronto = Bool()
        pronto.data = self.travado and self.perto
        self.pub_perto.publish(pronto)


def main(args=None):
    rclpy.init(args=args)
    no = NoControlador()
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
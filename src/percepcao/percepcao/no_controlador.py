"""No controlador de percepcao: busca alvo e segue com controle proporcional."""

import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from std_msgs.msg import String


class NoControlador(Node):
    """Controla busca e seguimento de um alvo detectado pela visao."""

    def __init__(self):
        """Declara parametros, estado, publishers e subscriptions."""
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
        self.declare_parameter("vel_busca_angular", 0.35)
        self.declare_parameter("timeout_seguranca_s", 0.5)

        self._carrega_parametros()
        self._inicia_estado()

        self.pub_cmd = self.create_publisher(Twist, "/cmd_vel", 1)
        self.pub_perto = self.create_publisher(Bool, "/alvo/pronto_para_garra", 1)
        self.pub_status = self.create_publisher(String, "/controle/status", 1)
        self.assinatura = self.create_subscription(
            Detection2DArray, "/visao/deteccoes", self.ao_receber_deteccoes, 1)
        self.assinatura_comando = self.create_subscription(
            String, "/controle/comando", self.ao_receber_comando, 1)
        self.timer_seguranca = self.create_timer(0.2, self.verifica_seguranca)

    def _carrega_parametros(self):
        """Le todos os parametros declarados para atributos."""
        self.largura_imagem_px = self.get_parameter(
            "largura_imagem_px").get_parameter_value().double_value
        self.altura_imagem_px = self.get_parameter(
            "altura_imagem_px").get_parameter_value().double_value
        self.alfa_ema = self.get_parameter(
            "alfa_ema").get_parameter_value().double_value
        self.deteccoes_para_travar = self.get_parameter(
            "deteccoes_para_travar").get_parameter_value().integer_value
        self.perdidos_para_soltar = self.get_parameter(
            "perdidos_para_soltar").get_parameter_value().integer_value
        self.ganho_angular = self.get_parameter(
            "ganho_angular").get_parameter_value().double_value
        self.velocidade_linear = self.get_parameter(
            "velocidade_linear").get_parameter_value().double_value
        self.limiar_perto_liga = self.get_parameter(
            "limiar_perto_liga").get_parameter_value().double_value
        self.limiar_perto_desliga = self.get_parameter(
            "limiar_perto_desliga").get_parameter_value().double_value
        self.vel_busca_angular = self.get_parameter(
            "vel_busca_angular").get_parameter_value().double_value
        self.timeout_seguranca_s = self.get_parameter(
            "timeout_seguranca_s").get_parameter_value().double_value

    def _inicia_estado(self):
        """Zera o estado interno e inicia no modo PARADO."""
        self.cx_filtrado = None
        self.tamanho_filtrado = None
        self.consecutivas = 0
        self.perdidas = 0
        self.travado = False
        self.perto = False
        self.modo = "PARADO"
        self.classe_alvo = None
        self.ultima_deteccao_s = self.get_clock().now().nanoseconds / 1e9

    def ao_receber_comando(self, msg):
        """Trata PARAR, BUSCAR:SOL e BUSCAR:NUVEM em /controle/comando."""
        comando = msg.data.strip()
        if comando == "PARAR":
            self._entra_em_parado()
        elif comando == "BUSCAR:SOL":
            self._inicia_busca("SOL")
        elif comando == "BUSCAR:NUVEM":
            self._inicia_busca("NUVEM")

    def _inicia_busca(self, classe):
        """Inicia uma busca por uma classe e vai para PROCURANDO."""
        self.classe_alvo = classe
        self.modo = "PROCURANDO"
        self.travado = False
        self.perto = False
        self.cx_filtrado = None
        self.tamanho_filtrado = None
        self.consecutivas = 0
        self.perdidas = 0
        self.ultima_deteccao_s = self.get_clock().now().nanoseconds / 1e9
        self._publica_status()

    def _entra_em_parado(self):
        """Zera /cmd_vel e volta ao modo PARADO."""
        self.modo = "PARADO"
        self.classe_alvo = None
        self.travado = False
        self.perto = False
        self.pub_cmd.publish(Twist())
        self._publica_status()

    def ao_receber_deteccoes(self, msg):
        """Filtra pela classe alvo, aplica EMA e atualiza travamento."""
        if self.modo == "PARADO":
            return
        self.ultima_deteccao_s = self.get_clock().now().nanoseconds / 1e9
        deteccoes = self._filtra_por_classe(msg.detections)
        if not deteccoes:
            self.registra_perda()
            return
        det = max(deteccoes, key=self._score_deteccao)
        self._atualiza_filtro(det)
        self._atualiza_travamento()
        self._atualiza_perto()
        self.publica_comando()

    def _filtra_por_classe(self, deteccoes):
        """Mantem apenas deteccoes cujo class_id e a classe alvo."""
        resultado = []
        for d in deteccoes:
            if d.results and d.results[0].hypothesis.class_id == self.classe_alvo:
                resultado.append(d)
        return resultado

    def _score_deteccao(self, d):
        """Retorna o score da primeira hipotese de uma deteccao."""
        return d.results[0].hypothesis.score

    def _atualiza_filtro(self, det):
        """Atualiza cx e tamanho filtrados por EMA."""
        cx = det.bbox.center.position.x
        tamanho = det.bbox.size_y / self.altura_imagem_px
        if self.cx_filtrado is None:
            self.cx_filtrado = cx
        else:
            self.cx_filtrado = self.alfa_ema * cx + \
                (1 - self.alfa_ema) * self.cx_filtrado
        if self.tamanho_filtrado is None:
            self.tamanho_filtrado = tamanho
        else:
            self.tamanho_filtrado = self.alfa_ema * tamanho + \
                (1 - self.alfa_ema) * self.tamanho_filtrado

    def _atualiza_travamento(self):
        """Conta deteccoes consecutivas e trava no alvo."""
        self.perdidas = 0
        self.consecutivas += 1
        if self.consecutivas >= self.deteccoes_para_travar:
            self.travado = True

    def _atualiza_perto(self):
        """Aplica histerese para marcar se o alvo esta perto."""
        if self.tamanho_filtrado > self.limiar_perto_liga:
            self.perto = True
        elif self.tamanho_filtrado < self.limiar_perto_desliga:
            self.perto = False

    def registra_perda(self):
        """Conta perdas e solta o alvo apos o limite de perdas."""
        self.consecutivas = 0
        self.perdidas += 1
        if self.perdidas >= self.perdidos_para_soltar:
            self.travado = False
            self.perto = False
            self.cx_filtrado = None
            self.tamanho_filtrado = None
        self.publica_comando()

    def publica_comando(self):
        """Publica /cmd_vel conforme o modo e atualiza status/pronto."""
        if self.perto and self.travado:
            self._chega_no_alvo()
            return
        cmd = Twist()
        if self.travado:
            self.modo = "SEGUINDO"
            cmd = self._comando_seguindo()
        else:
            self.modo = "PROCURANDO"
            cmd.angular.z = self.vel_busca_angular
        self.pub_cmd.publish(cmd)
        self._publica_status()
        self._publica_pronto()

    def _comando_seguindo(self):
        """Controle proporcional em angular e avanco linear."""
        cmd = Twist()
        erro = (self.cx_filtrado - self.largura_imagem_px / 2) / \
            (self.largura_imagem_px / 2)
        cmd.angular.z = -self.ganho_angular * erro
        cmd.linear.x = self.velocidade_linear
        return cmd

    def _chega_no_alvo(self):
        """Para o robo, avisa CHEGOU e volta ao modo PARADO."""
        self.pub_cmd.publish(Twist())
        self.modo = "CHEGOU"
        self._publica_status()
        self._publica_pronto()
        self._entra_em_parado()

    def verifica_seguranca(self):
        """Para por seguranca se a visao atrasar durante uma busca."""
        if self.modo != "SEGUINDO" and self.modo != "PROCURANDO":
            return
        agora = self.get_clock().now().nanoseconds / 1e9
        if agora - self.ultima_deteccao_s > self.timeout_seguranca_s:
            self.get_logger().warning("Timeout da visao: parando por seguranca.")
            self._entra_em_parado()

    def _publica_status(self):
        """Publica o modo atual em /controle/status."""
        status = String()
        status.data = self.modo
        self.pub_status.publish(status)

    def _publica_pronto(self):
        """Publica se o alvo esta travado e perto."""
        pronto = Bool()
        pronto.data = self.travado and self.perto
        self.pub_perto.publish(pronto)


def main(args=None):
    """Inicia o no e mantem o spin ate interrupcao."""
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

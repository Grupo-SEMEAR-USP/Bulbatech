import rclpy
from rclpy.node import Node

from datetime import datetime
from std_msgs.msg import Bool, String

class engine_node(Node):
    def __init__(self):
        super().__init__("engine_node")

        #Definição de parâmetros e setup
        self.declare_parameter("greeting", "Olá, eu sou o Bulbatek! Como vão as coisas?")
        self._greeting = self.get_parameter("greeting").value

        #Definição de publicação/inscrição
        self._say_pub = self.create_publisher(String, "voice/tts/say", 10)
        self._comando_pub = self.create_publisher(String, "/controle/comando", 10)
        self.create_subscription(String, "voice/stt/text", self._on_text, 10)
        self.create_subscription(Bool, "voice/tts/speaking", self._on_speaking, 10)
        self.create_subscription(String, "/controle/status", self._on_status, 10)

        self._desligando = False
        self._viu_falando = False
        self._ultimo_status = ""

        # Saudação inicial: espera o TTS estar conectado
        self._greet_timer = self.create_timer(0.5, self._saudar)

    def _saudar(self):
        if self._say_pub.get_subscription_count() > 0:
            self._greet_timer.cancel()
            self._falar(self._greeting)

    def _falar(self, texto: str):
        self._say_pub.publish(String(data=texto))

    def _enviar_comando(self, comando: str):
        self._comando_pub.publish(String(data=comando))

    def _on_text(self, msg: String):
        comando = msg.data

        if "clima" in comando:
            self._falar("Hoje tá muito, muito quente!")
        if "bom dia" in comando:
            self._falar("Bom dia! O Tibas tá por aí?")
        elif "sabedoria" in comando:
            self._falar("Nunca deixe de ser mau por causa das pessoas boas")
        elif "horas" in comando:
            agora = datetime.now()
            self._falar(agora.strftime("Agora são %H horas e %M minutos."))
        elif "desligar" in comando:
            self._desligando = True
            self._falar("Até mais, amigo")
        elif "sol" in comando:
            self._enviar_comando("BUSCAR:SOL")
            self._falar("Procurando o Sol!")
        elif "nuvem" in comando:
            self._enviar_comando("BUSCAR:NUVEM")
            self._falar("Procurando a Nuvem!")
        elif "parar" in comando:
            self._enviar_comando("PARAR")
            self._falar("Parando agora.")

    def _on_status(self, msg: String):
        status = msg.data
        if status == "CHEGOU" and self._ultimo_status != "CHEGOU":
            self._falar("Encontrei o alvo! Missao concluida.")
        self._ultimo_status = status

    def _on_speaking(self, msg: Bool):
        if not self._desligando:
            return
        if msg.data:
            self._viu_falando = True
        elif self._viu_falando:  # terminou de falar a despedida
            self.get_logger().info("Desligando...")
            rclpy.try_shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = engine_node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
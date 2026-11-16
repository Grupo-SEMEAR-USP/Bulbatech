import wave
import queue
import rclpy
import threading

from piper import PiperVoice
from rclpy.node import Node
from std_msgs.msg import Bool, String
from voice.voice_tools import play_wav, resolve_path

class TTSNode(Node):
    def __init__(self):
        super().__init__("tts_node")

        #Definição de parâmetros
        self.declare_parameter("voice_model", "")
        self.declare_parameter("voice_config", "")
        self.declare_parameter("output_wav", "/tmp/resposta.wav")

        #Configuração Piper
        self._output = self.get_parameter("output_wav").value
        # self._voice = PiperVoice.load(
        #     self.get_parameter("voice_model").value,
        #     config_path=self.get_parameter("voice_config").value,
        # )
        self._voice = PiperVoice.load(
            resolve_path(self.get_parameter("voice_model").value),
            config_path=resolve_path(self.get_parameter("voice_config").value),
        )

        #Definição fila e publicação/inscrição
        self._fila = queue.Queue()
        self._speaking_pub = self.create_publisher(Bool, "voice/tts/speaking", 10)
        self.create_subscription(String, "voice/tts/say", self._on_say, 10)

        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _on_say(self, msg: String):
        self._fila.put(msg.data)

    def _set_speaking(self, valor: bool):
        self._speaking_pub.publish(Bool(data=valor))

    def _worker(self):
        while rclpy.ok():
            try:
                texto = self._fila.get(timeout=0.5)
            except queue.Empty:
                continue

            self._set_speaking(True)
            try:
                self.get_logger().info(f"Bulbatech do Mal: {texto}")
                self._falar(texto)
            except Exception as e:
                self.get_logger().error(f"Erro ao falar: {e}")
            finally:
                # só libera o microfone quando a fila esvaziar
                if self._fila.empty():
                    self._set_speaking(False)

    def _falar(self, texto: str):
        with wave.open(self._output, "wb") as wav_file:
            self._voice.synthesize_wav(texto, wav_file)
        play_wav(self._output)


def main(args=None):
    rclpy.init(args=args)
    node = TTSNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

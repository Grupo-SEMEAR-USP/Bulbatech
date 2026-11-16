import json
import threading
import time

import numpy as np
import pyaudio
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from vosk import KaldiRecognizer, Model

from voice.voice_tools import resolve_path

VOSK_RATE = 16000  # taxa em que o modelo do Vosk foi treinado


class STTNode(Node):
    def __init__(self):
        super().__init__("stt_node")

        # Parâmetros
        self.declare_parameter("recognizer_model", "")
        self.declare_parameter("device_name", "")    # trecho do nome do mic; vazio = usa device_index
        self.declare_parameter("device_index", -1)   # -1 = microfone padrão do sistema
        self.declare_parameter("audio_frequency", 16000)  # 0 = automático
        self.declare_parameter("buffer_size", 4000)
        self.declare_parameter("audio_vocabulary", [""])  # [""] = sem restrição
        self.declare_parameter("debug", False)

        model_path = resolve_path(self.get_parameter("recognizer_model").value)
        name = self.get_parameter("device_name").value
        index = self.get_parameter("device_index").value
        wanted_rate = self.get_parameter("audio_frequency").value
        self._buffer = self.get_parameter("buffer_size").value
        self._debug = self.get_parameter("debug").value
        vocab = [w for w in self.get_parameter("audio_vocabulary").value if w]

        # Publicação/inscrição
        self._pub = self.create_publisher(String, "voice/stt/text", 10)
        self.create_subscription(Bool, "voice/tts/speaking", self._on_speaking, 10)
        self._speaking = False

        # Vosk (sempre a 16 kHz; com vocabulário fica mais rápido e preciso)
        self._model = Model(model_path)
        if vocab:
            grammar = json.dumps(vocab, ensure_ascii=False)
            self._recognizer = KaldiRecognizer(self._model, VOSK_RATE, grammar)
        else:
            self._recognizer = KaldiRecognizer(self._model, VOSK_RATE)

        # Microfone
        self._pa = pyaudio.PyAudio()
        self._device = self._find_device(index, name)
        self._freq = self._pick_rate(self._device, wanted_rate)
        dev_name = self._pa.get_device_info_by_index(self._device)["name"]
        self.get_logger().info(
            f"Microfone [{self._device}] {dev_name} a {self._freq} Hz"
        )

        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._freq,
            input=True,
            input_device_index=self._device,
            frames_per_buffer=self._buffer,
        )

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._stream.start_stream()
        self._thread.start()
        self.get_logger().info("Estou ouvindo...")

    # ---------- seleção do dispositivo ----------
    def _find_device(self, index: int, name: str) -> int:
        if name:
            for i in range(self._pa.get_device_count()):
                info = self._pa.get_device_info_by_index(i)
                if info["maxInputChannels"] > 0 and name.lower() in info["name"].lower():
                    return i
            self.get_logger().warn(f"Nenhum microfone com '{name}' no nome")
        if index >= 0:
            return index
        return int(self._pa.get_default_input_device_info()["index"])

    def _pick_rate(self, idx: int, wanted: int) -> int:
        info = self._pa.get_device_info_by_index(idx)
        candidates = [wanted, VOSK_RATE, int(info["defaultSampleRate"]), 48000, 44100]
        for rate in dict.fromkeys(candidates):  # sem repetir, mantém a ordem
            if rate <= 0:
                continue
            try:
                if self._pa.is_format_supported(
                    rate,
                    input_device=idx,
                    input_channels=1,
                    input_format=pyaudio.paInt16,
                ):
                    return rate
            except ValueError:
                continue
        raise RuntimeError(f"Dispositivo {idx} não aceita nenhuma taxa de amostragem testada")

    # ---------- áudio ----------
    def _to_16k(self, data: bytes) -> bytes:
        if self._freq == VOSK_RATE:
            return data
        x = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        if self._freq % VOSK_RATE == 0:
            k = self._freq // VOSK_RATE
            n = len(x) // k * k
            y = x[:n].reshape(-1, k).mean(axis=1)  # média = filtro simples
        else:
            n_out = int(len(x) * VOSK_RATE / self._freq)
            y = np.interp(np.linspace(0, len(x) - 1, n_out), np.arange(len(x)), x)
        return y.astype(np.int16).tobytes()

    def _on_speaking(self, msg: Bool):
        self._speaking = msg.data

    def _loop(self):
        pico = 0.0
        ultimo_log = time.monotonic()
        ultimo_parcial = ""

        while self._running:
            raw = self._stream.read(self._buffer, exception_on_overflow=False)

            if self._debug:
                x = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                pico = max(pico, float(np.sqrt(np.mean(x**2))))
                if time.monotonic() - ultimo_log >= 2.0:
                    self.get_logger().info(f"[debug] nível do mic (pico 2s): {pico:.0f}")
                    pico, ultimo_log = 0.0, time.monotonic()

            # Descarta o áudio enquanto o robô fala (evita ouvir a si mesmo)
            if self._speaking:
                self._recognizer.Reset()
                continue

            data = self._to_16k(raw)
            if self._recognizer.AcceptWaveform(data):
                resultado = json.loads(self._recognizer.Result())
                palavras = [w for w in resultado.get("text", "").lower().split() if w != "[unk]"]
                texto = " ".join(palavras)
                ultimo_parcial = ""
                if texto:  # ignora silêncio/ruído
                    self.get_logger().info(f"Você disse: {texto}")
                    self._pub.publish(String(data=texto))
            elif self._debug:
                parcial = json.loads(self._recognizer.PartialResult()).get("partial", "")
                if parcial and parcial != ultimo_parcial:
                    self.get_logger().info(f"[debug] parcial: {parcial}")
                    ultimo_parcial = parcial

    def destroy_node(self):
        self._running = False
        self._thread.join(timeout=1.0)
        self._stream.stop_stream()
        self._stream.close()
        self._pa.terminate()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = STTNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
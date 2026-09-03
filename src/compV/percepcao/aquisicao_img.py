"""
Propósito único de obter os frames e melhorar o framerate
Extremamente útil em hardware limitado
"""
from threading import Thread, Lock
import cv2 as cv
import time
import logging

class FluxoVideo:
    """Objeto de video"""
    def __init__(self, resolucao=(1280,720), taxaquadros=30, NoteOuWebcam=1, src=0):
        """
        Args:
            resolucao (tuple): Define a tupla(W,H) da resolução da câmera,
            Default=(1280,720)
            framerate (int): Define o framerate da câmera, Default=30
            NoteOrWebcam (int): Entre 1 ou 2 para qual câmera está sendo cap-
            turada, Default = 1
            src (int): Indice do componente físico de captura,
            Default=0 
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.NoteOuWebcam = NoteOuWebcam 
        self.taxaquadros = taxaquadros
        self.resolucao = resolucao

        
        self.fluxo = cv.VideoCapture(src, cv.CAP_V4L2)
        
        if isinstance(resolucao, (tuple, list)) and len(resolucao) >= 2:
            self.fluxo.set(cv.CAP_PROP_FRAME_WIDTH, resolucao[0])
            self.fluxo.set(cv.CAP_PROP_FRAME_HEIGHT, resolucao[1])
        else:
            self.logger.warning("Formato de resolução inválido. Utilizando o padrão do hardware.")
        if not self.fluxo.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*'MJPG')):
            self.logger.warning("Não foi possível aplicar o codec selecionado. Utilizando o padrão do hardware.")
        if not self.fluxo.set(cv.CAP_PROP_FPS, taxaquadros):
            self.logger.warning("Taxa de quadros incompatível. Utilizando o padrão do hardware.")
        if not self.fluxo.set(cv.CAP_PROP_AUTO_EXPOSURE, 0.25):
            self.logger.warning("Não foi permitido ajustar a exposição automática da câmera. Utilizando o padrão do hardware.")
        if not self.fluxo.set(cv.CAP_PROP_AUTO_WB, 0):
            self.logger.warning("Não foi permitido ajustar o auto balanceio de branco da câmera. Utilizando o padrão do hardware.")
        (self.capturado, self.quadro) = self.fluxo.read()
        self.stopped = False
        """bool: Variavel para controlar se a câmera parou"""
        self.lock = Lock()
        """locktype: """
        self.logger.info("Módulo FluxoVideo inicializado")
    def comeca(self):
        """
        Inicia as thread para a leitura de frames
        """
        thread = Thread(target=self.atualizacao,name="FluxoVideoThread",daemon=True) 
        thread.start()
        self.logger.info("Thread de aquisição de vídeo iniciada com sucesso.")
        return self
    def atualizacao(self):
        while not self.stopped:
            (capturado, quadro) = self.fluxo.read()
            if not capturado:
                self.logger.error("Falha física de comunicação com o sensor da câmera. Interrompendo captura.")
                self.pare()
                break

            with self.lock:
                self.quadro = quadro
    def leia(self):
        with self.lock:
            # Evita sobrescrever os pixels
            return self.quadro.copy() if self.quadro is not None else None

    def pare(self):
        self.stopped = True
        self.fluxo.release()
        self.logger.info("Recursos de captura de vídeo liberados de forma segura.")
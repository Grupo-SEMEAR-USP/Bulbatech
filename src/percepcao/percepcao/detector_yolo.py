import pathlib

import cv2 as cv
import torch

# Remendo: os pesos foram treinados no Windows e guardam um WindowsPath
pathlib.WindowsPath = pathlib.PosixPath


class DetectorYolo:
    """Detector neural sem estado. Entrada: quadro BGR. Saída: lista de tuplas
    (x_min, y_min, x_max, y_max, confianca, nome_classe)."""

    def __init__(self, caminho_repo, caminho_pesos, confianca_minima=0.5, classes_aceitas=("SOL",)):
        self.modelo = torch.hub.load(caminho_repo,"custom",caminho_pesos,source="local")
        self.modelo.conf = confianca_minima
        self.classes_aceitas = classes_aceitas

    def detecta(self, quadro):
        imagem_rgb = cv.cvtColor(quadro, cv.COLOR_BGR2RGB)
        resultados = self.modelo(imagem_rgb)
        caixas = resultados.xyxy[0]
        deteccoes = []
        for x_min, y_min, x_max, y_max, confianca, id_classe in caixas.tolist():
            nome = self.modelo.names[int(id_classe)]
            if nome not in self.classes_aceitas:
                print(f"A Classe '{nome}' não é uma classe de detecção.")
            else:
                deteccoes.append((x_min, y_min, x_max, y_max, confianca, nome))
        return deteccoes
import os
import wave
import pydub
import numpy as np
import sounddevice as sd
from pydub import AudioSegment
from ament_index_python.packages import get_package_share_directory

def resolve_path(path:str) -> str:
    if(os.path.isabs(path)):
        return path
    return os.path.join(get_package_share_directory("voice"), path)

def play_wav(path: str) -> None:
    """Toca wav (bloqueia até terminar)"""
    with wave.open(path, "rb") as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        audio = wf.readframes(wf.getnframes())
        audio_np = np.frombuffer(audio, dtype=np.int16)

        if n_channels == 2:
            audio_np = audio_np.reshape(-1, 2)
        audio_np = audio_np.astype(np.float32) / 32768.0
        
        sd.play(audio_np, sample_rate)
        sd.wait()

def load_mp3(path: str):
    """Retorna (array float32 normalizado, frame_rate)."""
    audio = AudioSegment.from_mp3(path)
    data_audio = np.array(audio.get_array_of_samples(), dtype=np.float32)
    #Normalização de audio
    if audio.sample_width == 2:
        data_audio /= 32768.0
    elif audio.sample_width == 1:
        data_audio = (data_audio - 128.0) / 128.0
    if audio.channels == 2:
        data_audio = data_audio.reshape((-1,2))
    return data_audio, audio.frame_rate

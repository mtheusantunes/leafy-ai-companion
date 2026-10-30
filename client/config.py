"""
Configurações do Cliente Raspberry Pi do Leafy AI Companion.
"""
import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class ClientConfig:
    # URL da API do backend Leafy (porta 8001 mapeada no docker-compose)
    api_url: str = os.getenv("LEAFY_API_URL", "http://localhost:8001/assistente")
    
    # Timeout de rede em segundos
    request_timeout: float = float(os.getenv("LEAFY_REQUEST_TIMEOUT", "30.0"))
    
    # Modo de operação: 'continuous' (escuta contínua), 'push_to_talk' (tecla Enter), 'text' (digitar)
    trigger_mode: str = os.getenv("LEAFY_TRIGGER_MODE", "continuous")
    
    # Motores de STT (reconhecimento de fala): 'auto', 'speech_recognition', 'keyboard', 'mock'
    stt_engine: str = os.getenv("LEAFY_STT_ENGINE", "auto")
    stt_language: str = os.getenv("LEAFY_STT_LANGUAGE", "pt-BR")
    
    # Motores de TTS (síntese de voz): 'auto', 'espeak', 'pyttsx3', 'gtts', 'mock'
    tts_engine: str = os.getenv("LEAFY_TTS_ENGINE", "auto")
    tts_voice_rate: int = int(os.getenv("LEAFY_TTS_VOICE_RATE", "165"))
    tts_language: str = os.getenv("LEAFY_TTS_LANGUAGE", "pt-BR")
    
    # Sensibilidade e silêncio do microfone
    energy_threshold: int = int(os.getenv("LEAFY_ENERGY_THRESHOLD", "300"))
    pause_threshold: float = float(os.getenv("LEAFY_PAUSE_THRESHOLD", "1.0"))


default_config = ClientConfig()

"""
Leafy AI Companion - Pacote Cliente para Raspberry Pi / Dispositivos Físicos.
"""
from .api_client import LeafyAPIClient
from .config import ClientConfig, default_config
from .audio.speaker import LeafySpeaker
from .audio.listener import LeafyListener

__all__ = ["LeafyAPIClient", "ClientConfig", "default_config", "LeafySpeaker", "LeafyListener"]

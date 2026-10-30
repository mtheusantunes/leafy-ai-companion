"""
Módulo de Síntese e Reprodução de Voz (TTS) para o Cliente Raspberry Pi.
"""
import logging
import os
import shutil
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger("LeafyClient.Speaker")


class LeafySpeaker:
    """
    Controla a reprodução de áudio da plantinha (Text-To-Speech).
    Suporta múltiplos motores: espeak-ng, pyttsx3, gTTS e fallback para terminal (mock).
    """

    def __init__(self, engine: str = "auto", voice_rate: int = 165, language: str = "pt-BR"):
        self.requested_engine = engine.lower()
        self.voice_rate = voice_rate
        self.language = language
        self.active_engine = self._detect_engine()
        logger.info(f"LeafySpeaker inicializado com o motor: {self.active_engine}")

    def _detect_engine(self) -> str:
        """Determina o melhor motor disponível no sistema."""
        if self.requested_engine in ["espeak", "espeak-ng"]:
            if self._has_espeak():
                return "espeak"
            logger.warning("espeak não encontrado no sistema. Tentando alternativas.")
        elif self.requested_engine == "pyttsx3":
            if self._has_pyttsx3():
                return "pyttsx3"
            logger.warning("pyttsx3 não disponível. Tentando alternativas.")
        elif self.requested_engine == "gtts":
            if self._has_gtts():
                return "gtts"
            logger.warning("gTTS não disponível. Tentando alternativas.")
        elif self.requested_engine == "mock":
            return "mock"

        # Modo 'auto': tenta na ordem de melhor desempenho para Raspberry Pi
        if self._has_espeak():
            return "espeak"
        elif self._has_pyttsx3():
            return "pyttsx3"
        elif self._has_gtts():
            return "gtts"
        else:
            logger.info("Nenhum sintetizador de áudio de sistema encontrado. Usando modo mock (console).")
            return "mock"

    def _has_espeak(self) -> bool:
        return bool(shutil.which("espeak-ng") or shutil.which("espeak"))

    def _has_pyttsx3(self) -> bool:
        try:
            import pyttsx3
            return True
        except Exception:
            return False

    def _has_gtts(self) -> bool:
        try:
            from gtts import gTTS
            return bool(shutil.which("aplay") or shutil.which("ffplay") or shutil.which("mpg123"))
        except Exception:
            return False

    def speak(self, text: str) -> bool:
        """
        Sintetiza e reproduz o texto.

        Args:
            text: Texto da resposta a ser falado.

        Returns:
            bool: True se reproduzido com sucesso.
        """
        if not text or not text.strip():
            return False

        texto_limpo = text.strip()
        print(f"\n🔊 [Leslia Falando]: {texto_limpo}\n")

        if self.active_engine == "espeak":
            return self._speak_espeak(texto_limpo)
        elif self.active_engine == "pyttsx3":
            return self._speak_pyttsx3(texto_limpo)
        elif self.active_engine == "gtts":
            return self._speak_gtts(texto_limpo)
        else:
            # Modo mock: a exibição no terminal já é o suficiente
            return True

    def _speak_espeak(self, text: str) -> bool:
        binary = shutil.which("espeak-ng") or shutil.which("espeak")
        if not binary:
            return False
        try:
            subprocess.run(
                [binary, "-v", "pt-br", "-s", str(self.voice_rate), text],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao executar espeak: {e}")
            return False

    def _speak_pyttsx3(self, text: str) -> bool:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self.voice_rate)
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"Erro ao executar pyttsx3: {e}")
            return False

    def _speak_gtts(self, text: str) -> bool:
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang="pt-br")
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
                temp_filename = fp.name
                tts.save(temp_filename)

            player = shutil.which("mpg123") or shutil.which("ffplay") or shutil.which("aplay")
            if player:
                args = [player, temp_filename]
                if "ffplay" in player:
                    args = [player, "-nodisp", "-autoexit", temp_filename]
                subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            return True
        except Exception as e:
            logger.error(f"Erro ao executar gTTS: {e}")
            return False

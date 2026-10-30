"""
Módulo de Captura e Reconhecimento de Voz (STT) para o Cliente Raspberry Pi.
"""
import logging
import sys
from typing import Optional

logger = logging.getLogger("LeafyClient.Listener")


class LeafyListener:
    """
    Controla a escuta do microfone e transcrição de fala para texto (Speech-To-Text).
    Suporta SpeechRecognition (Google STT), entrada por teclado ou mock para testes.
    """

    def __init__(
        self,
        engine: str = "auto",
        language: str = "pt-BR",
        energy_threshold: int = 300,
        pause_threshold: float = 1.0
    ):
        self.requested_engine = engine.lower()
        self.language = language
        self.energy_threshold = energy_threshold
        self.pause_threshold = pause_threshold
        self.active_engine = self._detect_engine()
        self._sr_recognizer = None
        self._sr_microphone = None

        if self.active_engine == "speech_recognition":
            self._setup_speech_recognition()

        logger.info(f"LeafyListener inicializado com o motor: {self.active_engine}")

    def _detect_engine(self) -> str:
        if self.requested_engine in ["sr", "speech_recognition"]:
            if self._has_speech_recognition():
                return "speech_recognition"
            logger.warning("SpeechRecognition não disponível. Alternando para modo teclado.")
            return "keyboard"
        elif self.requested_engine == "keyboard":
            return "keyboard"
        elif self.requested_engine == "mock":
            return "mock"

        # Modo 'auto': se biblioteca e microfone estiverem disponíveis, usa speech_recognition
        if self._has_speech_recognition():
            return "speech_recognition"
        else:
            logger.info("SpeechRecognition/PyAudio não detectados. Modo teclado ativado.")
            return "keyboard"

    def _has_speech_recognition(self) -> bool:
        try:
            import speech_recognition as sr
            # Testa se há microfones no sistema
            try:
                m = sr.Microphone()
                return True
            except (OSError, AttributeError):
                # Sem dispositivo de áudio disponível
                return False
        except Exception:
            return False

    def _setup_speech_recognition(self):
        try:
            import speech_recognition as sr
            self._sr_recognizer = sr.Recognizer()
            self._sr_recognizer.energy_threshold = self.energy_threshold
            self._sr_recognizer.pause_threshold = self.pause_threshold
            self._sr_microphone = sr.Microphone()
            logger.info("Ajustando sensibilidade ao ruído ambiente...")
            with self._sr_microphone as source:
                self._sr_recognizer.adjust_for_ambient_noise(source, duration=0.8)
        except Exception as e:
            logger.warning(f"Não foi possível inicializar microfone real: {e}. Alternando para teclado.")
            self.active_engine = "keyboard"

    def listen(self, prompt_message: str = "Pode falar, estou ouvindo...") -> Optional[str]:
        """
        Escuta o microfone ou aguarda entrada do usuário.

        Returns:
            Optional[str]: Texto reconhecido ou None se não foi compreendido.
        """
        if self.active_engine == "speech_recognition" and self._sr_microphone:
            return self._listen_sr(prompt_message)
        elif self.active_engine == "keyboard":
            return self._listen_keyboard(prompt_message)
        elif self.active_engine == "mock":
            return "Olá Leslia, como você está hoje?"
        return None

    def _listen_sr(self, prompt_message: str) -> Optional[str]:
        import speech_recognition as sr
        print(f"👂 [Leafy Ouvindo]: {prompt_message}")
        try:
            with self._sr_microphone as source:
                audio = self._sr_recognizer.listen(source, timeout=8.0, phrase_time_limit=15.0)
            print("🔄 [Processando fala...]")
            texto = self._sr_recognizer.recognize_google(audio, language=self.language)
            print(f"👤 [Você disse]: {texto}")
            return texto
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("❓ [Não entendi o que você disse]")
            return None
        except sr.RequestError as e:
            logger.error(f"Erro no serviço de reconhecimento de voz: {e}")
            return None
        except Exception as e:
            logger.error(f"Falha ao capturar áudio: {e}")
            return None

    def _listen_keyboard(self, prompt_message: str) -> Optional[str]:
        try:
            print(f"⌨️  [Modo Teclado]: {prompt_message}")
            texto = input("👤 Você: ").strip()
            return texto if texto else None
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando escuta...")
            return None

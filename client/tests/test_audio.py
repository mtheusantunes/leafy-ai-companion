"""
Testes unitários para os módulos de áudio (Speaker e Listener).
"""
import unittest
from unittest.mock import patch
from client.audio.speaker import LeafySpeaker
from client.audio.listener import LeafyListener


class TestLeafyAudio(unittest.TestCase):

    def test_speaker_mock_speak(self):
        speaker = LeafySpeaker(engine="mock")
        self.assertEqual(speaker.active_engine, "mock")
        self.assertTrue(speaker.speak("Olá da plantinha!"))
        self.assertFalse(speaker.speak(""))

    def test_listener_mock_listen(self):
        listener = LeafyListener(engine="mock")
        self.assertEqual(listener.active_engine, "mock")
        texto = listener.listen()
        self.assertIsNotNone(texto)
        self.assertIn("Leslia", texto)

    @patch("builtins.input", return_value="Bom dia Leslia")
    def test_listener_keyboard_listen(self, mock_input):
        listener = LeafyListener(engine="keyboard")
        self.assertEqual(listener.active_engine, "keyboard")
        texto = listener.listen()
        self.assertEqual(texto, "Bom dia Leslia")


if __name__ == "__main__":
    unittest.main()

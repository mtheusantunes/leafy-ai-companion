"""
Teste de integração de ponta a ponta para o fluxo do cliente (Listener -> API -> Speaker).
"""
import unittest
from unittest.mock import patch, MagicMock
from client.api_client import LeafyAPIClient
from client.audio.listener import LeafyListener
from client.audio.speaker import LeafySpeaker


class TestClientIntegration(unittest.TestCase):

    @patch("client.api_client.requests.post")
    def test_full_pipeline_roundtrip(self, mock_post):
        # 1. Configura a resposta simulada da API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Adoro conversar com você. Como foi seu dia?"
        mock_post.return_value = mock_response

        # 2. Inicializa componentes em modo mock
        listener = LeafyListener(engine="mock")
        speaker = LeafySpeaker(engine="mock")
        client = LeafyAPIClient(api_url="http://localhost:8001/assistente")

        # 3. Executa o fluxo: escuta -> envio -> fala
        texto_ouvido = listener.listen()
        self.assertIsNotNone(texto_ouvido)

        sucesso, resposta_api = client.send_message(texto_ouvido)
        self.assertTrue(sucesso)
        self.assertEqual(resposta_api, "Adoro conversar com você. Como foi seu dia?")

        resultado_fala = speaker.speak(resposta_api)
        self.assertTrue(resultado_fala)


if __name__ == "__main__":
    unittest.main()

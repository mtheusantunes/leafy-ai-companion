"""
Testes unitários para o cliente HTTP do Leafy AI Companion.
"""
import unittest
from unittest.mock import patch, MagicMock
from client.api_client import LeafyAPIClient


class TestLeafyAPIClient(unittest.TestCase):

    def setUp(self):
        self.api_url = "http://localhost:8001/assistente"
        self.client = LeafyAPIClient(api_url=self.api_url, timeout=5.0)

    def test_send_empty_message(self):
        sucesso, msg = self.client.send_message("")
        self.assertFalse(sucesso)
        self.assertIn("Nenhum texto informado", msg)

    @patch("client.api_client.requests.post")
    def test_send_message_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Olá! Estou muito bem, obrigado por perguntar."
        mock_post.return_value = mock_response

        sucesso, resposta = self.client.send_message("Oi Leslia")
        self.assertTrue(sucesso)
        self.assertEqual(resposta, "Olá! Estou muito bem, obrigado por perguntar.")
        mock_post.assert_called_once_with(
            self.api_url,
            json={"texto": "Oi Leslia"},
            headers={"Content-Type": "application/json"},
            timeout=5.0
        )

    @patch("client.api_client.requests.post")
    def test_send_message_server_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        sucesso, resposta = self.client.send_message("Oi")
        self.assertFalse(sucesso)
        self.assertIn("500", resposta)

    @patch("client.api_client.requests.post")
    def test_send_message_connection_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Falha ao conectar")

        sucesso, resposta = self.client.send_message("Oi")
        self.assertFalse(sucesso)
        self.assertIn("Não foi possível conectar", resposta)


if __name__ == "__main__":
    unittest.main()

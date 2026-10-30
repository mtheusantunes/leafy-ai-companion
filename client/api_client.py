"""
Cliente HTTP isolado para comunicação com a API do Leafy AI Companion.
"""
import json
import logging
from typing import Optional, Tuple

logger = logging.getLogger("LeafyClient.API")

# Tenta usar a biblioteca requests, com fallback para urllib nativo
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request
    import urllib.error


class LeafyAPIClient:
    """
    Gerencia as requisições HTTP para a API do assistente virtual (api_agente.py).
    """

    def __init__(self, api_url: str, timeout: float = 30.0):
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

    def send_message(self, texto: str) -> Tuple[bool, str]:
        """
        Envia a mensagem transcrita do usuário para o endpoint /assistente.
        
        Args:
            texto: Texto falado pelo usuário.
            
        Returns:
            Tuple[bool, str]: (sucesso, resposta_texto_ou_erro)
        """
        if not texto or not texto.strip():
            return False, "Nenhum texto informado para envio."

        texto_limpo = texto.strip()
        payload = {"texto": texto_limpo}

        if HAS_REQUESTS:
            return self._send_with_requests(payload)
        else:
            return self._send_with_urllib(payload)

    def _send_with_requests(self, payload: dict) -> Tuple[bool, str]:
        try:
            resp = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )
            if resp.status_code == 200:
                return True, resp.text.strip()
            else:
                msg = f"Erro no servidor ({resp.status_code}): {resp.text}"
                logger.error(msg)
                return False, msg
        except requests.exceptions.ConnectTimeout:
            return False, "Tempo de resposta esgotado ao contatar o servidor da plantinha."
        except requests.exceptions.ConnectionError:
            return False, "Não foi possível conectar ao servidor Leafy. Verifique se a API está rodando."
        except Exception as e:
            return False, f"Falha na comunicação com a API: {e}"

    def _send_with_urllib(self, payload: dict) -> Tuple[bool, str]:
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.api_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                return True, body.strip()
        except urllib.error.URLError as e:
            return False, f"Erro de conexão: {e.reason}"
        except Exception as e:
            return False, f"Falha na requisição: {e}"

    def ping(self) -> bool:
        """
        Verifica se a API está online enviando uma saudação simples.
        """
        sucesso, _ = self.send_message("ping")
        return sucesso

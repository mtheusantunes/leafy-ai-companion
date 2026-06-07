# -----------------------------------------------------------------------------
# Project: Leafy AI Companion
# Author: Matheus Antunes Freire (github.com/mtheusantunes)
# Copyright (c) 2026 Matheus Antunes Freire. All rights reserved.
#
# This file is part of the Leafy AI Companion project.
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution. This software is licensed under the GNU GPLv3.
# -----------------------------------------------------------------------------
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import weaviate
from agente_rag import consultar_base_conhecimento

# Define o formato que o celular vai enviar
class RequisicaoMobile(BaseModel):
    texto: str

app = FastAPI(title="API Mobile - Assistente Virtual")

# Variável global para manter a conexão do banco viva
cliente_weaviate = None

@app.on_event("startup")
def iniciar_banco():
    global cliente_weaviate
    try:
        print("Conectando ao Weaviate para a API Mobile...")
        cliente_weaviate = weaviate.connect_to_custom(
            http_host="weaviate",
            http_port=8080,
            http_secure=False,
            grpc_host="weaviate",
            grpc_port=50051,
            grpc_secure=False
        )
    except Exception as e:
        print(f"Erro ao conectar no banco: {e}")

@app.on_event("shutdown")
def fechar_banco():
    if cliente_weaviate:
        cliente_weaviate.close()

@app.post("/assistente", response_class=PlainTextResponse)
def receber_audio(req: RequisicaoMobile):
    """Rota que o dispositivo vai acessar"""
    if not cliente_weaviate:
        return "Desculpe, o sistema de arquivos está offline."
    
    # Passa a pergunta do celular para o seu agente RAG
    resposta_ia = consultar_base_conhecimento(req.texto, cliente_weaviate)
    
    # Devolve APENAS o texto puro, sem metadados JSON!
    return resposta_ia

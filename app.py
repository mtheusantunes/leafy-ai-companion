# -----------------------------------------------------------------------------
# Project: Leafy AI Companion
# Author: Matheus Antunes Freire (github.com/mtheusantunes)
# Copyright (c) 2026 Matheus Antunes Freire. All rights reserved.
#
# This file is part of the Leafy AI Companion project.
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution. This software is licensed under the GNU GPLv3.
# -----------------------------------------------------------------------------
import streamlit as st
import weaviate
from agente_rag import consultar_base_conhecimento

st.set_page_config(
    page_title="Assistente",
    page_icon="📚",
    layout="centered"
)

st.title("📚 Assistente Virtual")
st.markdown("""
            <style>
            [data-testid="stChatMessageAvatarAssistant"] {
                background-color: #C8191E;
            }
            [data-testid="stChatMessageAvatarUser"] {
                background-color: #2F9E40;
            }
            </style>
        """, unsafe_allow_html=True)

@st.cache_resource
def iniciar_conexao_banco():
    try:
        cliente_weaviate = weaviate.connect_to_custom(
            http_host="weaviate",
            http_port=8080,
            http_secure=False,
            grpc_host="weaviate",
            grpc_port=50051,
            grpc_secure=False
        )
        return cliente_weaviate
    except Exception as e:
        st.error(f"Falha ao conectar no banco de dados vetorial: {e}")
        return None

cliente_weaviate = iniciar_conexao_banco()

if "mensagens" not in st.session_state:
    st.session_state.mensagens = [
        {"role": "assistant", "content": "Olá! Sou um assistente virtual. Como posso ajudar você hoje?"}
    ]

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

if pergunta := st.chat_input("Digite sua pergunta sobre os regulamentos..."):
    
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    
    with st.chat_message("assistant"):
        with st.spinner("Consultando a base de conhecimento..."):
            ultimas_mensagens = st.session_state.mensagens[-5:-1]
            
            if cliente_weaviate:
                resposta_ia = consultar_base_conhecimento(pergunta, cliente_weaviate)
            else:
                resposta_ia = "Desculpe, o sistema de arquivos está offline no momento."
            
            st.markdown(resposta_ia)
    
    st.session_state.mensagens.append({"role": "assistant", "content": resposta_ia})

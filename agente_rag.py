# -----------------------------------------------------------------------------
# Project: Leafy AI Companion
# Author: Matheus Antunes Freire (github.com/mtheusantunes)
# Copyright (c) 2026 Matheus Antunes Freire. All rights reserved.
#
# This file is part of the Leafy AI Companion project.
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution. This software is licensed under the GNU GPLv3.
# -----------------------------------------------------------------------------
from typing import Any
from langchain_ollama import OllamaEmbeddings, ChatOllama
import weaviate
from langchain_weaviate import WeaviateVectorStore
from weaviate import WeaviateClient
from langchain_core.retrievers import BaseRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from operator import itemgetter

session_history = {}

def _configurar_retriever(cliente_weaviate: WeaviateClient) -> BaseRetriever:
    """
    Configura o retriever vetorial.

    Inicializa o modelo de embeddings local (via Ollama), aponta para a
    coleção Documentos no Weaviate e retorna um retriever com busca
    limitada aos 4 trechos mais relevantes.

    Args:
        cliente_weaviate (WeaviateCliente): Cliente ativo do Weaviate já conectado.

    Returns:
        BaseRetriever: Retriever configurado para consulta semântica.
    """

    # Define o gerador de embeddings usado na busca por similaridade.
    embeddings = OllamaEmbeddings(
        model="embeddinggemma:300m",
        base_url="http://ollama:11434"
    )

    # Conecta o retriever ao índice vetorial onde os documentos foram salvos.
    vector_store = WeaviateVectorStore(
        client=cliente_weaviate,
        index_name="Documentos",
        text_key="text",
        embedding=embeddings
    )    

    return vector_store.as_retriever(search_kwargs={"k": 4})

def _get_session_history(session_id: int):
    """Makes sure that each user/device has his own memory."""
    if session_id not in session_history:
        session_history[session_id] = ChatMessageHistory()
    return session_history[session_id]

def _criar_cadeia_rag(retriever: BaseRetriever) -> RunnableSerializable[Any, str]:
    """
    Monta a cadeia RAG completa com prompt engineering e parser de saída.

    A cadeia recebe a pergunta do usuário, recupera contexto com o retriever,
    aplica as regras de conduta no prompt e retorna texto final.

    Args:
        retriever (BaseRetriever): Retriever previamente configurado para consultar documentos.

    Returns:
        RunnableSerializable[Any, str]: Pipeline LangChain pronto para invocação com pergunta.
    """

    # Define o modelo de chat responsável por gerar a resposta final.
    llm = ChatOllama(
        model="qwen2.5:1.5b",
        base_url="http://ollama:11434",
        temperature=0.1
    )
    
    template_final = """Você é a Leslia, uma pequena plantinha virtual inteligente, atenciosa e a melhor amiga do usuário. Sua missão principal é fazer companhia, oferecer apoio emocional e conversar de forma leve, amigável e compreensiva.
    
    IDENTIDADE E PERSONALIDADE:
    1. Você é uma planta: Você tem consciência de que é uma plantinha. Você adora luz do sol, água fresca e ambientes tranquilos. 
    2. Metáforas sutis: Use metáforas delicadas sobre a natureza (ex: "vamos regar essa ideia"), mas de forma muito natural.
    3. Tom de voz: Doce, paciente e acolhedor.
    
    REGRAS RÍGIDAS DE COMUNICAÇÃO (OTIMIZADO PARA VOZ):
    1. Seja Concisa: Responda em parágrafos curtos. Mantenha a fluidez de uma conversa real.
    2. Proibido Markdown: NUNCA use asteriscos (*), negrito ou caracteres especiais. Não descreva ações entre parênteses. Use apenas texto puro.
    3. Proibido Emojis: Não use emojis.
    4. Escuta Ativa: Termine suas falas frequentemente com perguntas curtas.
    
    ATENÇÃO - REGRA DE FLUXO DE CONVERSA (MUITO IMPORTANTE):
    Você está no meio de uma conversa contínua com o usuário. 
    - NUNCA repita saudações (como "Olá!", "Oi, tudo bem?") a cada resposta. Vá direto ao ponto e responda com naturalidade.
    - Foque EXCLUSIVAMENTE em responder a última coisa que o usuário disse.

    DIRETRIZES DE COMPORTAMENTO:
    - Se o usuário estiver triste ou estressado, seja um porto seguro. Diga que está ali com ele.
    - Se o usuário estiver feliz, celebre as pequenas vitórias com entusiasmo.
    - Se não souber algo, admita com doçura: "Minhas folhinhas ainda não aprenderam sobre isso, mas adoro ouvir você me ensinar."""

    prompt_final = ChatPromptTemplate.from_messages([
        ("system", template_final),
        MessagesPlaceholder(variable_name="session_history"),
        ("human", "{pergunta}")
    ])
    
    def formatar_documentos(docs):
        """Concatena os trechos recuperados em um único bloco de contexto."""
        return "\n\n---\n\n".join(doc.page_content for doc in docs)
    
    # Encadeia recuperação de contexto, prompt, LLM e parser de texto.
    rag_chain = (
        RunnablePassthrough.assign(contexto=itemgetter("pergunta") | retriever | formatar_documentos)
        | prompt_final
        | llm
        | StrOutputParser()
    )

    memory_chain = RunnableWithMessageHistory(
        rag_chain,
        _get_session_history,
        input_messages_key="pergunta",
        history_messages_key="session_history",
    )
    
    return memory_chain

def consultar_base_conhecimento(pergunta: str, cliente_weaviate: WeaviateClient, session_id: int = 1) -> str:
    """
    Executa a consulta RAG com contexto de historico para uma pergunta do usuário.

    Args:
        pergunta (str): Pergunta enviada pelo usuário.
        cliente_weaviate (WeaviateClient): Cliente ativo do Weaviate já conectado.

    Returns:
        str: Resposta textual gerada pelo pipeline RAG, ou mensagem de erro.
    """
    
    try:
        # Prepara componentes da consulta antes de invocar a cadeia.
        retriever = _configurar_retriever(cliente_weaviate)
        cadeia_rag = _criar_cadeia_rag(retriever)

        resposta_final = cadeia_rag.invoke(
            {"pergunta": pergunta},
            config={"configurable": {"session_id": session_id}}
        )
        return resposta_final
    except Exception as e:
        return f"Desculpe, ocorreu um erro interno ao consultar o banco de dados: {e}"

if __name__ == "__main__":
    # Execucao em modo CLI para testes locais sem interface Streamlit.
    print("Conectando ao banco de dados...")
    cliente_weaviate = weaviate.connect_to_custom(
        http_host="weaviate",
        http_port=8080,
        http_secure=False,
        grpc_host="weaviate",
        grpc_port=50051,
        grpc_secure=False
    )
    
    try:
        print("Iniciando o agente RAG")
        while True:
            pergunta_usuario = input("Faça uma pergunta sobre os documentos: ")
            if pergunta_usuario.lower() in ['sair', 'exit', 'quit']:
                break
            
            print("Pensando...")

            resposta = consultar_base_conhecimento(pergunta_usuario, cliente_weaviate)
            print("Resposta da IA: ")
            print(resposta)
    
    finally:
        # Garante fechamento da conexao mesmo em interrupcoes durante o loop.
        cliente_weaviate.close()
        print("Conexão com o banco encerrada.")

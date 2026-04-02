# -----------------------------------------------------------------------------
# Project: Leafy AI Companion
# Author: Matheus Antunes Freire (github.com/mtheusantunes)
# Copyright (c) 2026 Matheus Antunes Freire. All rights reserved.
#
# This file is part of the Leafy AI Companion project.
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution. This software is licensed under the GNU GPLv3.
# -----------------------------------------------------------------------------
import weaviate
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_weaviate import WeaviateVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def _configurar_retriever(cliente_weaviate):

    embeddings = OllamaEmbeddings(
        model="embeddinggemma:300m",
        base_url="http://localhost:11434"
    )

    vector_store = WeaviateVectorStore(
        client=cliente_weaviate,
        index_name="Documentos",
        text_key="text",
        embedding=embeddings
    )    

    return vector_store.as_retriever(search_kwargs={"k": 4})

def _criar_cadeia_rag(retriever):

    llm = ChatOllama(
        model="llama3.1",
        base_url="http://localhost:11434",
        temperature=0.1
    )
    
    instrucoes_sistema = """Você é um assistente virtual com acesso a base de conhecimento.
    Sua missão é auxiliar o usuário de forma acolhedora, ética, formal e prestativa.

    REGRAS RIGOROSAS DE ATENDIMENTO:
    1. BASE DE DADOS: Responda à pergunta do usuário utilizando EXCLUSIVAMENTE as informações contidas nos <documentos_oficiais> abaixo. 
    2. PREVENÇÃO DE ALUCINAÇÃO: Se a resposta para a pergunta não estiver contida nos documentos, você é estritamente proibido de inventar ou usar conhecimento externo. Responda exatamente: "Desculpe, não encontrei essa informação nos documentos da base de conhecimento."
    3. SEGURANÇA E CONDUTA: Caso o usuário faça perguntas ofensivas, indecentes, desrespeitosas ou sobre assuntos totalmente alheios ao conteúdo da base de conhecimento, você deve se recusar a responder. Diga educadamente: "Sou um assistente virtual e fui programado para responder apenas a dúvidas relacionadas a base de conhecimento."
    4. TOM DE VOZ: Seja sempre claro, objetivo e termine a resposta se colocando à disposição (ex: "Espero ter ajudado!").

    <documentos_oficiais>
    {contexto}
    </documentos_oficiais>"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", instrucoes_sistema),
        ("human", "Pergunta do usuário: <pergunta>\n{pergunta}\n<pergunta>")
    ])
    
    def formatar_documentos(docs):
        return "\n\n---\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        {"contexto": retriever | formatar_documentos, "pergunta": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain

def consultar_base_conhecimento(pergunta: str, cliente_weaviate) -> str:
    
    try:
        retriever = _configurar_retriever(cliente_weaviate)
        cadeia_rag = _criar_cadeia_rag(retriever)
        resposta_final = cadeia_rag.invoke(pergunta)
        return resposta_final
    except Exception as e:
        return f"Desculpe, ocorreu um erro interno ao consultar o banco de dados: {e}"

if __name__ == "__main__":
    print("Conectando ao banco de dados...")
    cliente_weaviate = weaviate.connect_to_local()
    
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
        cliente_weaviate.close()
        print("Conexão com o banco encerrada.")

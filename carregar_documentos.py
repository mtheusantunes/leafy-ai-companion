# -----------------------------------------------------------------------------
# Project: Leafy AI Companion
# Author: Matheus Antunes Freire (github.com/mtheusantunes)
# Copyright (c) 2026 Matheus Antunes Freire. All rights reserved.
#
# This file is part of the Leafy AI Companion project.
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution. This software is licensed under the GNU GPLv3.
# -----------------------------------------------------------------------------
from docling.document_converter import DocumentConverter
from docling.chunking import HierarchicalChunker
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import weaviate
from langchain_weaviate import WeaviateVectorStore
from weaviate.classes.query import Filter
import os
import hashlib

def gerar_hash_arquivo(caminho_arquivo):
    """
    Gera uma impressão digital (SHA-256) única para um arquivo PDF.

    Lê o arquivo em blocos de 4KB para garantir baixo uso de memória RAM,
    mesmo com documentos grandes.

    Args:
        caminho_arquivo (str): O caminho completo ou relativo para o arquivo PDF.

    Returns:
        str: Uma string de 64 caracteres hexadecimais representando o hash.
    """
    sha256_hash = hashlib.sha256()
    with open(caminho_arquivo, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() 

def processar_documento(caminho_arquivo: str, hash_arquivo: str) -> list[Document]:
    """
    Converte um PDF em documentos LangChain prontos para vetorização.

    O processamento acontece em duas etapas: primeiro gera chunks estruturais
    com o Docling e depois aplica um splitter recursivo para reduzir riscos de
    blocos muito grandes na etapa de embeddings.

    Args:
        caminho_arquivo (str): Caminho do arquivo PDF a ser processado.
        hash_arquivo (str): Hash SHA-256 do arquivo, usado para sincronização.

    Returns:
        list[Document]: Lista de documentos LangChain com texto e metadados.
    """
    print(f"Lendo e processando {caminho_arquivo}...")
    
    # Converte o PDF para a estrutura interna do Docling.
    conversor = DocumentConverter()
    resultado = conversor.convert(caminho_arquivo)
    documento_docling = resultado.document
    chunker = HierarchicalChunker()
    chunks_docling = chunker.chunk(documento_docling)

    # Mapeia cada chunk para o formato Document do LangChain.
    documentos_langchain = []
    for chunk in chunks_docling:
        texto = chunk.text
        item = chunk.meta.doc_items[0] if chunk.meta.doc_items else None

        if item and hasattr(item, 'prov') and item.prov:
            numero_pagina = item.prov[0].page_no
        else:
            numero_pagina = 0

        metadados = {
            "source": caminho_arquivo,
            "titulo_secao": chunk.meta.headings[0] if chunk.meta.headings else "Sem Título",
            "pagina": int(numero_pagina),
            "hash_arquivo": hash_arquivo
        }
        
        documento_langchain = Document(page_content=texto, metadata=metadados)
        documentos_langchain.append(documento_langchain)

    # Segunda camada de split para manter blocos em tamanho seguro.
    divisor = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=400,
        length_function=len
    )
    
    documentos_seguros = divisor.split_documents(documentos_langchain)
    print(f"Sucesso! PDF dividido em {len(documentos_seguros)} blocos contextuais seguros.")
    return documentos_seguros

def salvar_documentos(documentos_langchain: list[Document], cliente_weaviate):
    """
    Gera embeddings e persiste documentos no Weaviate.

    Usa o modelo local de embeddings via Ollama e grava os vetores na coleção
    Documentos_CEADi. Em caso de erro, registra a falha sem interromper o
    fechamento da conexão no fluxo principal.

    Args:
        documentos_langchain (list[Document]): Documentos a serem vetorizados.
        cliente_weaviate: Cliente ativo do Weaviate já conectado.

    Returns:
        None
    """
    # Configura o provedor de embeddings
    embeddings = OllamaEmbeddings(
        model="embeddinggemma:300m",
        base_url="http://ollama:11434"
    )

    try:
        print(f"Iniciando a vetorização de {len(documentos_langchain)} documentos...")
        vector_store = WeaviateVectorStore.from_documents(
            documents=documentos_langchain,
            embedding=embeddings,
            client=weaviate_cliente,
            index_name="Documentos"
        )
    except Exception as e:
        print(f"Erro ao tentar salvar os documentos no banco de dados: {e}.")
    else:
        print("Sucesso! Os documentos foram salvos no banco de dados.")
        

if __name__ == "__main__":
    # Configurações iniciais da execução.
    cliente_weaviate = None
    pasta_documentos = "docs"

    if not os.path.exists(pasta_documentos):
        print(f"Erro! A pasta '{pasta_documentos}' não foi encontrada.")
        exit(1)

    # Cria o mapa hash -> arquivo para comparar pasta x banco. Objetivo é sincronizar o conteúdo da pasta com
    # o do banco
    pdfs = [f for f in os.listdir(pasta_documentos) if f.lower().endswith('.pdf')]
    hashes_pasta = {}
    for pdf in pdfs:
        caminho_arquivo = os.path.join(pasta_documentos, pdf)
        h = gerar_hash_arquivo(caminho_arquivo)
        hashes_pasta[h] = pdf

    print(f"Encontrados {len(pdfs)} arquivos PDF. Iniciando processamento...")

    try:
        # Conecta ao Weaviate e coleta hashes já cadastrados.
        cliente_weaviate = weaviate.connect_to_custom(
            http_host="weaviate",
            http_port=8080,
            http_secure=False,
            grpc_host="weaviate",
            grpc_port=50051,
            grpc_secure=False
        )
        
        hashes_banco = set()
        if cliente_weaviate.collections.exists("Documentos"):
            colecao = cliente_weaviate.collections.get("Documentos")
            agregacao = colecao.aggregate.over_all(group_by="hash_arquivo")
            hashes_banco = {
                str(agrupamento.grouped_by.value)
                for agrupamento in agregacao.groups
            }

            for hash_banco in hashes_banco:
                if hash_banco not in hashes_pasta:
                    print(f"Removendo arquivo do banco não encontrado na pasta.")
                    colecao.data.delete_many(where=Filter.by_property("hash_arquivo").equal(hash_banco))

        # Processa apenas PDFs novos (ainda não presentes no banco).
        todos_documentos_processados = []
        for hash_arquivo, nome_arquivo in hashes_pasta.items():
            if hash_arquivo not in hashes_banco:
                caminho_arquivo = os.path.join(pasta_documentos, nome_arquivo)
                try:
                    novos_documentos = processar_documento(caminho_arquivo, hash_arquivo)
                    todos_documentos_processados.extend(novos_documentos)
                except Exception as e:
                    print(f"Erro ao processar o arquivo {nome_arquivo}: {e}")

        if todos_documentos_processados:
            salvar_documentos(todos_documentos_processados, cliente_weaviate)
        else:
            print(f"Base de dados já está em sincronia com a pasta '{pasta_documentos}/'")

    except Exception as e:
        print(f"Falha na conexão ou operação com Weaviate: {e}")

    finally:
        # Garante o encerramento da conexão, mesmo em caso de erro.
        if cliente_weaviate:
            cliente_weaviate.close()
            print("Conexão com o Weaviate encerrada.")

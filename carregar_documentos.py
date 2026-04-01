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
from langchain_weaviate import WeaviateVectorStore
import weaviate
import os

def processar_documentos(caminho_pdf: str) -> list[Document]:
    print(f"Lendo e processando {caminho_pdf}...")
    conversor = DocumentConverter()
    
    resultado = conversor.convert(caminho_pdf)
    documento_docling = resultado.document
    
    chunker = HierarchicalChunker()
    
    chunks_docling = chunker.chunk(documento_docling)
    
    documentos_langchain = []

    for chunk in chunks_docling:
        texto = chunk.text
        item = chunk.meta.doc_items[0] if chunk.meta.doc_items else None

        if item and hasattr(item, 'prov') and item.prov:
            numero_pagina = item.prov[0].page_no
        else:
            numero_pagina = 0

        metadados = {
            "source": caminho_pdf,
            "titulo_secao": chunk.meta.headings[0] if chunk.meta.headings else "Sem Título",
            "pagina": int(numero_pagina)
        }
        
        documento_langchain = Document(page_content=texto, metadata=metadados)
        documentos_langchain.append(documento_langchain)
    
    print(f"Sucesso! PDF dividido em {len(documentos_langchain)} blocos contextuais.")
    return documentos_langchain

def salvar_documentos(documentos_langchain: list[Document]):
    embeddings = OllamaEmbeddings(
        model="mxbai-embed-large",
        base_url="http://localhost:11434"
    )

    weaviate_cliente = None
    try:
        weaviate_cliente = weaviate.connect_to_local()
        print(f"Iniciando a vetorização de {len(documentos_langchain)} documentos...")
        vector_store = WeaviateVectorStore.from_documents(
            documents=documentos_langchain,
            embedding=embeddings,
            client=weaviate_cliente,
            index_name="Documentos"
        )
    except Exception as e:
        print("Erro ao tentar salvar os documentos no banco de dados.")
    else:
        print("Sucesso! Os documentos foram salvos no banco de dados.")
    finally:
        if weaviate_cliente:
            weaviate_cliente.close()
            print("Conexão com o Weaviate encerrada.")
        

if __name__ == "__main__":
    pasta_documentos = "docs"
    todos_documentos_processados = []

    if not os.path.exists(pasta_documentos):
        print(f"Erro! A pasta '{pasta_documentos}' não foi encontrada.")
        exit(1)

    arquivos = os.listdir(pasta_documentos)
    pdfs = [f for f in arquivos if f.lower().endswith('.pdf')]

    if not pdfs:
        print(f"Erro! Nenhum PDF encontrado na pasta {pasta_documentos}")
    else:
        print(f"Encontrados {len(pdfs)} arquivos PDF. Iniciando processamento...")
        
        for pdf in pdfs:
            caminho_completo = os.path.join(pasta_documentos, pdf)
            try:
                novos_documentos = processar_documentos(caminho_completo)
                todos_documentos_processados.append(novos_documentos)
            except Exception as e:
                print(f"Erro ao processar o arquivo {pdf}: {e}")
        try:
            if todos_documentos_processados:
                salvar_documentos(todos_documentos_processados)
        except Exception as e:
            print(f"Erro ao salvar os documentos no banco de dados.")

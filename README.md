docker instalado

docker compose up -d
chmod +x setup_modelos.sh



Escolha: Llama3 e embeddinggemma:300m


# Arquitetura e Decisões Técnicas: Módulo de Ingestão de Documentos

Este documento descreve as decisões de arquitetura, fluxo de processamento e limitações conhecidas do script de ingestão de PDFs (`carregar_documentos.py`) para o banco de dados vetorial do projeto ChatRAG.

---

## 1. Visão Geral do Fluxo
O módulo é responsável por ler documentos PDF em uma diretório local (`docs/`), fatiá-los de forma semântica, convertê-los em representações matemáticas (embeddings) e persisti-los no banco de dados vetorial Weaviate. O script foi projetado para ser **idempotente**, ou seja, pode ser rodado múltiplas vezes de forma segura, mantendo a pasta local e o banco de dados sempre sincronizados.

## 2. Decisões Técnicas Adotadas

### 2.1. Identidade Desacoplada da Localização (Hashing)
* **Decisão:** Utilizamos um hash `SHA-256` gerado a partir dos bytes do arquivo como Identificador Único (ID) do documento, em vez do nome do arquivo ou do caminho da pasta.
* **Justificativa:** Previne a duplicação de dados caso um arquivo seja renomeado ou movido de pasta. O sistema reconhece o conteúdo, não a casca.
* **Implementação Técnica:** A leitura para a geração do hash é feita em blocos de 4KB (`f.read(4096)`), garantindo um uso de memória RAM extremamente baixo (O(1)), independentemente do tamanho do PDF.

### 2.2. Sincronização Inteligente (State Matching)
* **Decisão:** Antes de processar os PDFs, o script compara um "mapa de hashes" da pasta local contra os hashes já existentes no Weaviate.
* **Justificativa:** 1. Evita o reprocessamento custoso (CPU/GPU) de documentos já vetorizados.
  2. Identifica arquivos que foram deletados da pasta local e dispara comandos de exclusão (`delete_many`) no Weaviate, mantendo a base de conhecimento limpa (Prevenção de *Data Drift*).

### 2.3. Estratégia de Chunking em Duas Etapas
Enfrentamos o desafio de equilibrar a qualidade semântica dos cortes com os limites técnicos de hardware (Context Window). A solução adotada foi um pipeline de duas fases:
1. **Corte Estrutural (Docling):** O `HierarchicalChunker` respeita a anatomia do PDF, agrupando textos com base em Títulos e Subtítulos. A proveniência do metadado da página é garantida extraindo o `page_no` do primeiro tijolo original (`chunk.meta.doc_items[0]`).
2. **Corte de Segurança (LangChain):** Caso o Docling gere um bloco gigantesco (ex: um capítulo contínuo de 5 páginas sem títulos), aplicamos o `RecursiveCharacterTextSplitter` (limite de 4000 caracteres, overlap de 400).
* **Justificativa:** Essa segunda etapa atua como uma "válvula de segurança", impedindo que textos massivos causem o erro `status code: 400 (context length exceeded)` no modelo do Ollama.

### 2.4. Adoção do Modelo `EmbeddingGemma-300M`
* **Decisão:** Migração do modelo `mxbai-embed-large` para o `google/embeddinggemma-300m` (via integração direta Hugging Face no Ollama).
* **Justificativa:** O modelo Gemma entrega resultados no estado da arte (SoTA) para modelos abaixo de 500M de parâmetros, lidando excepcionalmente bem com a língua portuguesa e termos técnicos acadêmicos. Ele também oferece uma janela de contexto confortável de até 2048 tokens.

### 2.5. Padrão EAFP (Tratamento de Erros)
* **Decisão:** Uso rigoroso de `try/except` ao redor de operações de I/O de rede (comunicação com Docker/Weaviate/Ollama), combinado com `if/else` para lógica de negócios.
* **Justificativa:** Evita que falhas na infraestrutura local (Ollama indisponível, Weaviate reiniciando) quebrem a execução do script abruptamente (evitando vazamento de conexões/sockets). O bloco `finally` garante o encerramento seguro do cliente Weaviate.

---

## 3. Limitações e Pontos de Atenção

Apesar da robustez, a arquitetura atual possui limitações mapeadas que devem ser consideradas para escalabilidade futura:

1. **Inflexibilidade de Dimensões (Mudança de Modelos de IA):**
   * *Problema:* O Weaviate trava a dimensão dos vetores na criação da coleção. Se no futuro decidirmos mudar do `EmbeddingGemma-300M` (ex: 768 dimensões) para outro modelo com tamanho vetorial diferente, o banco recusará os dados.
   * *Workaround atual:* É necessário rodar um script externo de "Hard Reset" para deletar a coleção `Documentos` inteira antes de iniciar a nova ingestão.

2. **Dependência Crítica de Infraestrutura Local:**
   * *Problema:* O script não possui *fallbacks* (plano B) na nuvem. Se os containers Docker do Ollama ou do Weaviate não estiverem rodando na porta correta, o processo falha inteiramente. 
   * *Problema 2:* O Ollama exige que o modelo já tenha sido baixado no container (`docker exec [...] ollama pull ...`). O script Python não faz esse download automaticamente.

3. **Processamento Sequencial (Gargalo de I/O):**
   * *Problema:* O loop principal processa os PDFs um por vez de forma síncrona. 
   * *Impacto:* Para lotes massivos de centenas de PDFs pesados, o tempo de ingestão será longo. Em arquiteturas futuras, pode-se avaliar a implementação de paralelismo (`asyncio` ou filas como Celery/RabbitMQ) para acelerar a vetorização.

---

## 4. Tecnologias e Bibliotecas Empregadas
* **Linguagem:** Python 3.10+
* **Extração PDF:** `docling` (DocumentConverter, HierarchicalChunker)
* **Orquestração e Splitter:** `langchain` e `langchain_text_splitters`
* **Integração de LLM Local:** `langchain_ollama`
* **Vector Database:** `weaviate-client` v4 (via `langchain_weaviate`)

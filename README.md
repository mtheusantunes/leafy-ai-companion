# Leafy AI Companion - Assistente Virtual

Este projeto implementa uma arquitetura de Geração Aumentada por Recuperação (RAG) para atuar como um assistente virtual com acesso a uma base de conhecimento. A aplicação responde a dúvidas baseando-se estritamente em documentos adicionados à baseada de conhecimento em formato PDF, utilizando processamento de linguagem natural executado 100% localmente.

## 1. Como Configurar e Executar o Ambiente

O projeto é totalmente conteinerizado utilizando Docker. Siga os passos abaixo para iniciar a aplicação e baixar os modelos.

### 1.1 Pré-requisitos
Antes de começar, certifique-se de ter os seguintes itens instalados e disponíveis no seu sistema:
*   **Docker Desktop** (Windows/Mac) ou **Docker Engine + Docker Compose** (Linux).
*   **Recursos de Hardware:** Como o sistema roda modelos de IA localmente, recomenda-se pelo menos **8 GB de RAM livres** (idealmente 16 GB) para garantir que o contêiner do Ollama consiga carregar o modelo `llama3.1` em memória sem travamentos.
*   *(Opcional para aceleração por GPU Nvidia)*: Drivers da Nvidia atualizados e o [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) instalado para que o Docker reconheça a placa de vídeo.
*   *(Opcional para aceleração por GPU AMD)*: Drivers ROCm instalados no sistema host.

### 1.2. Subir os Contêineres (Escolha seu Perfil de Hardware)
A arquitetura suporta perfis diferentes dependendo do seu hardware. No terminal, execute o comando correspondente à sua máquina:

*   **Para execução via dispositivo padrão (CPU, definido em .env):**
    ```bash
    docker compose up -d
    ```
*  **Para execução via CPU:**
    ```bash
    docker compose --profile cpu up -d
    ```
*   **Para execução via GPU Nvidia (CUDA):**
    ```bash
    docker compose --profile nvidia up -d
    ```
*   **Para execução via GPU AMD (ROCm):**
    ```bash
    docker compose --profile amd up -d
    ```

### 1.3. Baixar os Modelos de IA
Com os contêineres rodando, faça o download dos modelos de LLM e de Embeddings no contêiner do Ollama. *(Nota: substitua `ollama-cpu` por `ollama-nvidia` ou `ollama-amd` se estiver usando aceleração gráfica)*:

```bash
docker compose exec ollama-{seu_profile} ollama pull llama3.1
ou qwen2.5:1.5b
docker compose exec ollama-{seu_profile} ollama pull embeddinggemma:300m
```

---

## 2. Ingerir e Vetorizar os Documentos
 Para processar a base de conhecimento, coloque seus arquivos PDF na pasta `docs/`. Em seguida, execute o script de processamento de documentos dentro do contêiner da aplicação para ler, extrair textos e enviá-los ao banco de dados:

```bash
docker compose exec app python carregar_documentos.py
```

* **Obs:** O zip já acompanha alguns documentos de exemplo.

---

## 3. Acessar a Interface Web
Abra o seu navegador e acesse a interface interativa do chatbot em:
**http://localhost:8501**

---

## 4. Decisões Técnicas e Arquitetura

O sistema foi desenhado para atender aos requisitos do desafio, focando em otimização de recursos, modularidade e alta precisão na recuperação de informações. Abaixo, estão detalhadas as justificativas para as escolhas tecnológicas da arquitetura:

### 4.1 Infraestrutura e Orquestração (Docker)
*   **Isolamento e Leveza:** A aplicação web roda em uma imagem base otimizada (`python:3.12-slim`). Dependências de sistema (como `libgl1` e `tesseract-ocr`) foram injetadas cirurgicamente no *build* para suportar as bibliotecas de visão computacional do Docling sem inflar o contêiner.
*   **Ambiente de Desenvolvimento Fluido:** O `docker-compose.yml` espelha o código via volumes locais para permitir atualizações em tempo real, mas utiliza volumes anônimos (`/app/venv` e `/app/__pycache__`) para isolar as dependências do contêiner do ambiente *host*, prevenindo conflitos de sistema operacional.
*   **Agnosticismo de Hardware:** A arquitetura foi construída com *Docker Profiles*, permitindo que o mesmo código rode perfeitamente em máquinas limitadas (apenas CPU) ou tire proveito máximo de aceleração de hardware (Nvidia CUDA ou AMD ROCm) sem alterar uma linha de código.

### 4.2 Ingestão Semântica e Chunking Híbrido
O processamento de PDFs (documentos) é historicamente complexo devido a quebras de página, tabelas e cabeçalhos. Adotou-se uma estratégia de "Fatiamento Híbrido":
*   **Fatiamento Semântico:** Em vez de cortar o texto cegamente por número de caracteres, utilizou-se o  `HierarchicalChunker` do Docling para ler a árvore estrutural do PDF. Ele agrupa o texto respeitando a hierarquia original do documento (capítulos, artigos, parágrafos), garantindo que o contexto não seja quebrado ao meio.
*   **Camada de Segurança Vetorial (`RecursiveCharacterTextSplitter`):** Documentos podem conter capítulos massivos que, mesmo agrupados semanticamente, excedem a janela de contexto (limite de tokens) dos modelos de *embedding*. Para evitar a perda de dados por truncamento silencioso ou erros de inferência, aplicou-se uma segunda camada recursiva (tamanho máximo de 4000 caracteres com sobreposição de 400). Isso garante a integridade matemática da vetorização, mantendo todos os blocos em um tamanho seguro e altamente denso para a busca.

### 4.3 Sincronização Inteligente de Arquivos
A atualização da base de conhecimento foi projetada para ser tolerante a falhas, desacoplada e otimizada em consumo de memória:
*   **Independência de Nomenclatura:** O sistema não confia em caminhos ou nomes de arquivos. Um *hash* criptográfico (SHA-256) é gerado a partir do conteúdo binário do PDF. Se um usuário renomear `Regulamento_v1.pdf` para `Regulamento_Final.pdf`, o sistema sabe que o conteúdo é idêntico e ignora o reprocessamento, economizando poder computacional.
*   **Eficiência de Memória RAM:** A leitura para a geração do *hash* é feita em blocos (chunks) binários de 4KB. Isso significa que a aplicação pode ingerir PDFs de centenas de megabytes sem estourar a memória do contêiner.
*   **Busca em Banco Otimizada:** Na etapa de sincronização, não são baixados os vetores do banco para comparar com a pasta. Utiliza-se uma consulta de agregação nativa do Weaviate (`aggregate.over_all(group_by="hash_arquivo")`) que retorna apenas um `Set` de hashes únicos. Como o cruzamento em memória é feito entre um `Set` e um Dicionário (Tabelas Hash), a complexidade algorítmica de verificação cai de $O(n^2)$ para $O(N)$, tornando a identificação de arquivos novos ou deletados eficiente.

### 4.4 Modelos de Inteligência Artificial Locais
A escolha da *stack* de IA priorizou o equilíbrio entre a qualidade das respostas e o peso do modelo na memória RAM/VRAM:
*   **LLM de Inferência (`llama3.1 - 8B`):** Escolhido por ser um modelo de código aberto com ótimo custo-benefício na categoria de 8 bilhões de parâmetros. Ele possui um alinhamento excepcional para seguir instruções estritas, o que é vital para obedecer às nossas regras de "não alucinar". Além disso, possui suporte nativo e fluente ao Português do Brasil. Foi estabelecida a `temperature=0.1` para reduzir drasticamente a aleatoriedade, garantindo que o modelo seja analítico, conservador e produza respostas altamente consistentes e previsíveis.
*   **Motor de Vetorização (`embeddinggemma:300m`):** Modelos de *embedding* gigantescos geram matrizes muito pesadas e lentas de consultar. O modelo da família Gemma com 300 milhões de parâmetros oferece um "ponto de equilíbrio" perfeito: é leve o suficiente para ser executado em CPUs comuns durante a ingestão de PDFs, mas denso o suficiente para capturar nuances semânticas complexas da língua portuguesa na hora da busca.

### 4.5 Banco de Dados Vetorial (Weaviate)
*   **Persistência:** O banco roda em seu próprio contêiner, com volumes montados garantindo que a base de dados não seja perdida ao reiniciar o servidor.
*   **Gerenciamento de Estado no Streamlit:** O cliente do Weaviate é instanciado através do decorador `@st.cache_resource`. Isso mantém uma conexão de alta performance persistente no servidor, impedindo que o banco sofra ataques de conexões repetidas toda vez que o usuário envia uma nova mensagem no chat ou atualiza a página.

### 4.6 Pipeline RAG e Prompting Restritivo
*   **LCEL (LangChain Expression Language):** A cadeia de geração foi construída utilizando a arquitetura moderna de tubos (*pipes*) do LangChain. Isso garante um fluxo de dados tipado, assíncrono e nativamente compatível com *streaming* de respostas.
*   **Protocolo Anti-Alucinação:** O prompt do sistema isola o contexto injetado dentro de *tags* XML (`<documentos_oficiais>`). O modelo `llama3.1` é condicionado a utilizar **exclusivamente** este escopo para compor a resposta, sendo programado com respostas padronizadas de recusa ("fallback") caso a pergunta escape do escopo ou contenha teor inapropriado. 

---

## 5. Limitações Conhecidas

*   **Ausência de Memória Conversacional:** O pipeline do LangChain foi desenhado para processar consultas isoladas. Embora a interface gráfica do Streamlit exiba o histórico de chat na tela, as mensagens anteriores não são reinjetadas no *prompt* do LLM (não há uso de *Conversation Buffer Memory*). Portanto, o assistente responde sempre de forma independente à pergunta atual e não compreende perguntas de seguimento que dependam de contexto passado (ex: *"Pode me explicar melhor o item 2 da sua última resposta?"*).
*   **Dependência de Hardware Local:** Como todo o processamento de inferência do LLM e a geração de embeddings (via Ollama) rodam localmente, o tempo de resposta do assistente está diretamente limitado à disponibilidade de memória RAM e VRAM (Placa de Vídeo) da máquina hospedeira.
*   **Tempo de Ingestão de Documentos:** A biblioteca Docling é extremamente precisa para ler estruturas complexas de PDFs, mas seu processamento pode ser significativamente lento em documentos que contenham dezenas ou centenas de páginas, especialmente por estar configurado para usar a CPU para maior compatibilidade.
*   **Contexto Fixo:** O pipeline do LangChain foi definido com uma restrição da busca vetorial a um número predefinido de trechos (`k=4`). Se a resposta a uma pergunta muito abrangente estiver fragmentada por muitas partes do documento, o assistente pode não recuperar todas as frações necessárias simultaneamente.

---

## 👨‍💻 Author

**Matheus Antunes Freire** 
* GitHub: [@mtheusantunes](https://github.com/mtheusantunes)

## 📄 License

Copyright (c) 2026 Matheus Antunes Freire. All rights reserved.

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. 
See the [LICENSE](LICENSE) file in the root directory for more details.

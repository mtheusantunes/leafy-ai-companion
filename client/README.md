# 🌱 Leafy AI Companion - Cliente Raspberry Pi

Este módulo contém o código do **cliente físico** que roda embarcado na sua plantinha através de um **Raspberry Pi** (ou qualquer computador Linux com microfone e alto-falante).

O cliente foi desenvolvido com **isolamento arquitetural total**: ele **não** depende de bibliotecas pesadas de IA (como PyTorch, Docling ou Weaviate). Ele é leve, consome pouca memória RAM e CPU, e se comunica exclusivamente via HTTP REST com o backend do Leafy (`POST /assistente`).

---

## 🛠️ Requisitos de Hardware na Plantinha

1. **Raspberry Pi** (Qualquer modelo 3, 4 ou 5 rodando Raspberry Pi OS 64-bit).
2. **Microfone USB** (ou placa de áudio I2S como ReSpeaker HAT).
3. **Alto-falante** (USB, P2 analógico ou Bluetooth).
4. Conexão de rede (Wi-Fi ou Ethernet) com o servidor onde o Leafy está rodando.

---

## 📦 Instalação no Raspberry Pi

### 1. Instalar pacotes de sistema para áudio
No terminal do seu Raspberry Pi:

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv portaudio19-dev python3-pyaudio espeak-ng alsa-utils
```

> **Dica:** O pacote `espeak-ng` fornece síntese de voz (TTS) 100% offline, extremamente rápida e leve para o Raspberry Pi em português (`pt-br`).

### 2. Criar um ambiente virtual isolado para o cliente
```bash
cd leafy-ai-companion/client
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar a Conexão
Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

Edite o `.env` e configure o endereço IP da sua máquina onde o servidor Leafy está rodando. Por exemplo:
```env
LEAFY_API_URL=http://192.168.1.100:8001/assistente
```
*(Se estiver rodando o servidor e o cliente no mesmo Raspberry Pi, use `http://localhost:8001/assistente`)*.

---

## 🚀 Como Executar

### Modo 1: Escuta e Fala Contínua (Padrão)
A plantinha fica escutando o microfone continuamente, processa com a Leslia e responde em voz alta:
```bash
python main.py --mode continuous
```

### Modo 2: Push-to-Talk (Aperte Enter para Falar)
Ideal para ambientes barulhentos ou quando quiser acionar manualmente a conversa:
```bash
python main.py --mode push_to_talk
```

### Modo 3: Modo Texto (SSH / Terminal Headless)
Permite conversar com a plantinha digitando no teclado e ouvindo a resposta no alto-falante:
```bash
python main.py --mode text
```

### Modo 4: Mensagem Única (Teste Rápido)
Envia uma única frase, fala a resposta e encerra:
```bash
python main.py --mode single --text "Oi Leslia, você gosta de sol?"
```

### Autoteste de Conexão e Áudio
```bash
python main.py --test
```

---

## ⚙️ Opções Avançadas de Linha de Comando

| Argumento | Descrição | Opções |
| :--- | :--- | :--- |
| `--api-url` | Sobrescreve a URL do backend | URL completa do endpoint `/assistente` |
| `--mode` | Modo de interação | `continuous`, `push_to_talk`, `text`, `single` |
| `--stt` | Motor de reconhecimento de voz | `auto`, `sr` (Google/SpeechRecognition), `keyboard`, `mock` |
| `--tts` | Motor de síntese de voz | `auto`, `espeak`, `pyttsx3`, `gtts`, `mock` |
| `--test` | Executa validação de ponta a ponta | Flag booleana |

#!/usr/bin/env python3
"""
Leafy AI Companion - Cliente Raspberry Pi
Orquestrador da interface física: microfone -> API do Leafy -> alto-falante.
"""
import argparse
import logging
import os
import sys
import time

# Adiciona o diretório raiz ao path caso seja executado isoladamente
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.config import ClientConfig, default_config
from client.api_client import LeafyAPIClient
from client.audio.listener import LeafyListener
from client.audio.speaker import LeafySpeaker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("LeafyClient.Main")


def banner():
    print("""
    ==================================================
        🌱 LEAFY AI COMPANION - CLIENTE RASPBERRY PI
        Sua plantinha inteligente ouvindo e falando!
    ==================================================
    """)


def parse_args():
    parser = argparse.ArgumentParser(description="Cliente Raspberry Pi do Leafy AI Companion")
    parser.add_argument(
        "--api-url",
        type=str,
        default=default_config.api_url,
        help="URL da API do assistente (ex: http://192.168.1.50:8001/assistente)"
    )
    parser.add_argument(
        "--mode",
        choices=["continuous", "push_to_talk", "text", "single"],
        default=default_config.trigger_mode,
        help="Modo de interação: continuous (voz contínua), push_to_talk (aperta tecla), text (teclado), single (uma mensagem)"
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Texto para envio no modo 'single'"
    )
    parser.add_argument(
        "--stt",
        choices=["auto", "sr", "keyboard", "mock"],
        default=default_config.stt_engine,
        help="Motor de reconhecimento de fala"
    )
    parser.add_argument(
        "--tts",
        choices=["auto", "espeak", "pyttsx3", "gtts", "mock"],
        default=default_config.tts_engine,
        help="Motor de sintetizador de voz"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Executa um autoteste de conectividade com a API e saída de voz e encerra"
    )
    return parser.parse_args()


def run_test(api_client: LeafyAPIClient, speaker: LeafySpeaker):
    print("\n🔍 Executando autoteste do cliente...")
    print(f"1. Testando conexão com a API em: {api_client.api_url}")
    sucesso, resp = api_client.send_message("Olá, você está me ouvindo?")
    if sucesso:
        print(f"   ✅ API respondeu com sucesso: {resp}")
        print("2. Testando saída de áudio (TTS)...")
        speaker.speak(resp)
        print("   ✅ Teste de áudio concluído!")
        return 0
    else:
        print(f"   ❌ Falha ao contatar a API: {resp}")
        print("   Dica: Verifique se o Docker com a API está rodando ('docker compose up -d').")
        return 1


def main():
    args = parse_args()
    banner()

    # Se o modo for text, forçamos o stt para keyboard
    stt_engine = "keyboard" if args.mode == "text" else args.stt

    api_client = LeafyAPIClient(api_url=args.api_url, timeout=default_config.request_timeout)
    speaker = LeafySpeaker(
        engine=args.tts,
        voice_rate=default_config.tts_voice_rate,
        language=default_config.tts_language
    )
    listener = LeafyListener(
        engine=stt_engine,
        language=default_config.stt_language,
        energy_threshold=default_config.energy_threshold,
        pause_threshold=default_config.pause_threshold
    )

    if args.test:
        sys.exit(run_test(api_client, speaker))

    if args.mode == "single":
        mensagem = args.text or "Olá Leslia, tudo bem com você?"
        print(f"📤 Enviando mensagem única: '{mensagem}'")
        sucesso, resposta = api_client.send_message(mensagem)
        if sucesso:
            speaker.speak(resposta)
        else:
            print(f"❌ Erro: {resposta}")
        return

    print(f"🌱 Modo de Operação: {args.mode.upper()}")
    print(f"📡 Conectado à API: {api_client.api_url}")
    print(f"🎤 Entrada (STT): {listener.active_engine}")
    print(f"🔊 Saída (TTS): {speaker.active_engine}")
    print("\n[Pressione Ctrl+C a qualquer momento para encerrar]\n")

    # Saudação inicial de boas-vindas
    speaker.speak("Olá! Sou a Leslia, sua plantinha companheira. Já estou ouvindo você.")

    try:
        while True:
            if args.mode == "push_to_talk":
                input("\n👉 [Pressione ENTER para falar com a plantinha...]")

            # Escuta o microfone ou teclado
            fala = listener.listen("Pode falar, estou ouvindo...")
            if not fala:
                continue

            # Envia para a API do Leafy
            print("⏳ [Leslia pensando...]")
            sucesso, resposta = api_client.send_message(fala)

            # Reproduz a resposta
            if sucesso:
                speaker.speak(resposta)
            else:
                msg_erro = "Desculpe, não consegui me conectar à minha base de pensamento agora."
                print(f"⚠️ {resposta}")
                speaker.speak(msg_erro)

            # Pequeno intervalo para evitar eco se o microfone captar o próprio alto-falante
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n🌿 Encerrando o Leafy Client. Até logo!")
        speaker.speak("Até logo! Vou continuar aqui tomando meu banho de sol.")


if __name__ == "__main__":
    main()

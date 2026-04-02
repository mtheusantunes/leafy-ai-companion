#!/bin/bash
if ! docker compose ps | grep -q "Up"; then
    echo "Erro: Os containers não parecem estar rodando. Execute 'docker compose up -d' primeiro."
    exit 1
fi
echo "Baixando modelos para o PIAGET..."
docker compose exec ollama ollama pull llama3.1
docker compose exec ollama ollama pull embeddinggemma:300m
echo "Ambiente pronto!"
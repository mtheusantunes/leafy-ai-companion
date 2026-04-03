
# -----------------------------------------------------------------------------
# Project: Leafy AI Companion
# Author: Matheus Antunes Freire (github.com/mtheusantunes)
# Copyright (c) 2026 Matheus Antunes Freire. All rights reserved.
#
# This file is part of the Leafy AI Companion project.
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution. This software is licensed under the GNU GPLv3.
# -----------------------------------------------------------------------------
FROM python:3.12-slim

# Impede o Python de gerar arquivos .pyc e força os logs a aparecerem na hora
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define a pasta de trabalho dentro do contêiner
WORKDIR /app

# Instala as dependências do sistema operacional
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxcb1 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Atualiza o pip e instala as dependências
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Expõe a porta padrão do Streamlit
EXPOSE 8501

# O comando padrão quando o contêiner ligar será subir o app web
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

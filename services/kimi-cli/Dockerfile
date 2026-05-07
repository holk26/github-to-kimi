FROM ubuntu:22.04

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    ssh \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    vim \
    nano \
    htop \
    tmux \
    zsh \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv (gestor de paquetes Python rápido)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Instalar Kimi CLI
RUN pip3 install kimi-cli

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copiar código de la API
COPY main.py .

# Crear directorio workspace
RUN mkdir -p /workspace

# Puerto para la API
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

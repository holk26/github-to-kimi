FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    vim \
    nano \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip

# Instalar uv (prerrequisito de Kimi CLI)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Asegurar que uv y tools estén en el PATH
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

# Instalar Kimi CLI usando uv
RUN /root/.local/bin/uv tool install kimi-cli

# Verificar instalación
RUN which kimi && kimi --version

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY main.py .

RUN mkdir -p /workspace/users

EXPOSE 8000

# Ejecutar Kimi Web en el puerto 8000, accesible desde cualquier host
CMD ["kimi", "web", "--host", "0.0.0.0", "--port", "8000", "--no-open", "--dangerously-allow-any-origin"]

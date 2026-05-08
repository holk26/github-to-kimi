FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache git curl nodejs npm bash

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm -rf /root/.cache/pip

# Install httpx explicitly
RUN pip install httpx==0.27.0

COPY main.py .
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]

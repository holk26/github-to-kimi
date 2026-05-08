FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache git curl nodejs npm bash

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm -rf /root/.cache/pip

COPY main.py .
COPY start.sh .
RUN chmod +x start.sh

# Force rebuild on every deploy
RUN echo "v2.0.0-$(date +%s)" > /app/.version

EXPOSE 8000

CMD ["./start.sh"]

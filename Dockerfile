FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir pyrogram==2.0.106 tgcrypto==1.2.5 aiohttp==3.9.3 ntgcalls==1.1.2 pytgcalls==1.4.1

COPY . .

CMD ["python", "bot.py"]

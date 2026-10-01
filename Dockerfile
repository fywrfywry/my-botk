FROM python:3.10-slim

# تثبيت الحزم الأساسية وأدوات النظام المطلوبة لمكتبة الصوت والفيديو
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تثبيت مكتبات بايثون
RUN pip install --no-cache-dir pyrogram tgcrypto pytgcalls aiohttp

COPY . .

CMD ["python", "main.py"]

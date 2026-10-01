FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir pyrogram tgcrypto pytgcalls aiohttp
COPY . .
CMD ["python", "main.py"]

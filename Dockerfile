FROM python:3.11-slim

# تثبيت مكتبات النظام الضرورية للبث وصوتيات الفيديوهات مثل ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ ملف المتطلبات أولاً لتسريع التثبيت
COPY requirements.txt .

# تثبيت مكتبات بايثون
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات البوت
COPY . .

# أمر تشغيل البوت
CMD ["python", "bot.py"]

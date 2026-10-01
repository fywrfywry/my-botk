FROM python:3.11-slim

# تثبيت الأدوات الأساسية وبيئة Node.js الضرورية لعمل البث (pytgcalls)
RUN apt-get update && apt-get install -y \
    git \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ ملفات المشروع
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# أمر تشغيل البوت
CMD ["python", "main.py"]

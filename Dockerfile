FROM python:3.9-slim

# Sistem paketlerini yükle
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libzbar-dev \
    libopencv-dev \
    python3-opencv \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizinini oluştur
WORKDIR /app

# Python gereksinimlerini kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY . .

# Logs dizinini oluştur
RUN mkdir -p /app/logs

# Port'u aç
EXPOSE 5001

# Health check için endpoint ekle
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5001/health || exit 1

# Uygulamayı başlat
CMD ["python", "qr_service.py"]

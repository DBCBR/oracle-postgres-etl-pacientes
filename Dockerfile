FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependências do sistema necessárias para Oracle Instant Client
RUN apt-get update \
    && apt-get install -y --no-install-recommends libaio1 unzip wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas arquivos necessários
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . /app

# Diretório opcional onde o Instant Client pode ser montado pelo time de infra
ENV ORACLE_INSTANT_CLIENT=/opt/oracle/instantclient_23_0

# Diretório para logs
RUN mkdir -p /app/logs
VOLUME [ "/app/logs" ]

# Por padrão executa o pipeline (dispatcher + performer --once)
CMD ["python", "run_pipeline.py"]

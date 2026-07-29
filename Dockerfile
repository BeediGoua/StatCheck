# Dockerfile minimal pour l'environnement Python StatCheck
FROM python:3.11-slim

# Configuration de l'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Installation des dépendances systèmes minimales (ex: pour compiler psycopg2)
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation de uv (le gestionnaire de paquets ultra-rapide)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Ces étapes sont commentées et seront activées au fur et à mesure de l'avancement :
# COPY pyproject.toml . (si on l'utilise plus tard)
# COPY requirements.txt . (ou installation directe via uv)
# RUN uv pip install --system sqlalchemy psycopg2-binary pandas

# Copie du code source
# COPY src/ ./src/
# COPY scripts/ ./scripts/

# Commande par défaut (ex: Lancement du robot d'ingestion)
# CMD ["python", "scripts/init_db.py"]

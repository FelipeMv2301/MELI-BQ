FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# CLI standalone de Tailwind (sin Node/npm) — mismo pin que en desarrollo (v3.4.17, coincide con
# la sintaxis de tailwind.config.js). Binario Linux, no se versiona (ver .gitignore).
RUN curl -sL -o /usr/local/bin/tailwindcss \
        https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64 \
    && chmod +x /usr/local/bin/tailwindcss

COPY . .

# Compila el CSS real (necesita el código ya copiado, escanea los .html) y junta los estáticos.
RUN tailwindcss -i static/css/tailwind-src.css -o static/css/app.css --minify \
    && python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "meliBQ.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

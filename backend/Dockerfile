FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    gcc \
    # Добавляем gosu для безопасного переключения пользователя
    gosu \
    && rm -rf /var/lib/apt/lists*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip==24.3.1 \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser

RUN mkdir -p /app/db && chown -R appuser:appgroup /app

# Эта папка всё равно будет перекрыта томом, но оставим для порядка
RUN mkdir -p /shared && chmod 1777 /shared

# ❗ Убираем USER appuser, чтобы контейнер стартовал от root и смог исправить права в entrypoint.
# Переключение на appuser произойдёт внутри entrypoint.sh с помощью gosu.
# USER appuser

EXPOSE 8080

ENTRYPOINT [ "./entrypoint.sh" ]
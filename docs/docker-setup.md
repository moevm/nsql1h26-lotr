# Как запуститься: докер и прочие вещи

### Запуск через Docker 

Перейти в корень проекта (/nsql1h26-lotr)

Скопируйте .env.example в .env и установите там свои перменные окружения (что за что отвечает - параграф ниже):
```bash
cp .env.example .env
```

Первый запуск или после изменений в `requirements.txt` / `Dockerfile`:
```bash
docker compose build && docker compose up
```

После изменений только в питонячьем коде:
```bash
docker compose restart backend
```

Остановить:
```bash
docker compose down
```

Остановить и удалить volumes (полный сброс БД, будет нужен если меняли пароль от Neo4j):
```bash
docker compose dowm -v
```

Если вы его запустили и видите подобный вывод:
```bash
lotr_backend | [entrypoint] Waiting for Neo4j...
lotr_backend | Neo4j is ready
lotr_backend | [entrypoint] Running Django migrations...
lotr_backend | [entrypoint] Installing neomodel labels and constraints...
lotr_backend | [entrypoint] Seed command not found yet — skipping.
lotr_backend | [entrypoint] Starting Gunicorn...
lotr_backend | [INFO] Listening at: http://0.0.0.0:8080
lotr_backend | [INFO] Worker 11: Neo4j pool reinitialized
lotr_backend | [INFO] Worker 12: Neo4j pool reinitialized
```
то всё супер. Вы молодец. Разрешаю вафельку скушать.

У вас должен открываться Swagger UI по адресу `http://localhost:8080/api/v1/docs/`. Если он пустой/неполный - всё нормально. Это не openapi.yml, это схема, сгенерированная из кода. Пока кода нет полностью или частично, схемы тоже не будет польностью или частично.

### Переменные окружения

| Переменная | Пример | Назначение |
|---|---|---|
| `NEO4J_PASSWORD` | `mypassword` | Пароль Neo4j. Используется в `NEO4J_AUTH` и healthcheck |
| `NEO4J_BOLT_URL` | `bolt://neo4j:mypassword@db:7687` | URL для neomodel внутри контейнера. `db` — имя сервиса в compose |
| `SECRET_KEY` | `django-insecure-...` | Django secret key. Любая длинная строка для dev |
| `DEBUG` | `True` | В проде `False`, в разработке `True` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,backend` | Разрешённые хосты |
| `DATABASE_URL` | `sqlite:////app/db/django.sqlite3` | Путь к SQLite внутри контейнера. Если запускаете локально, создайте локальную sqlite БДшку и укажите путь к ней |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Разрешённые origins для фронта |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | `15` | Время жизни access токена |
| `REFRESH_TOKEN_LIFETIME_DAYS` | `7` | Время жизни refresh токена |

### Локальный запуск

Может быть удобно в разработке - для написания миграций и отладки.
```bash
cd backend

# создать и активировать venv (если что вам придётся установить python3.12):
python3.12 -m venv venv
source venv/bin/activate

# установить зависимости:
pip install -r requirements.txt
pip install -r requirements-dev.txt

# SQLite для локального запуска - путь отличается от докера:
# в .env (или передать отдельно):
DATABASE_URL=sqlite:///./db/django.sqlite3

mkdir -p db

# Миграции:
python manage.py migrate

# Проверка конфигурации:
python manage.py check
```

Важно: `NEO4J_BOLT_URL` в `.env` указывает на `db:7687` (имя докер сервиса). При локальном запуске вне контейнера это не резолвится. Для локальной работы с Neo4j нужно либо пробросить порт, либо переопределить переменную:
```bash
NEO4J_BOLT_URL=bolt://neo4j:mypassword@localhost:7687 python manage.py shell
```

### Типизация на бэкенде

Если есть вопросы типа "ыыыы ну зачем нам типизация ааа", то ну я не знаю, мне так удобнее всегда, автодополнение нормально работать начинает, чувствуешь что не чушь делаешь какую-то.

Стратегия `strict = true` везде кроме `apps/pages/models.py` (для neomodel нет стабов). У всех `# type: ignore` должен быть комментарий  `# type: ignore[attr-defined] # neomodel no stubs`.

Во всех файлах с аннотациями - `from __future__ import annotations` первой строкой. Если забудете (IDE не подсветит или что-то такое), то увидите ошибку, которая будет ругаться на тайпхинт. 

Ещё не забудьте про расшрирения для VSCode типа `pylance` и `mypy type checker`. Ну если курс Яндекса проходили, то они у вас должны быть.

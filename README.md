# Развертывание системы проверки инженерной документации на сервере Proxmox

## Описание
Система состоит из нескольких компонентов, каждый из которых упакован в Docker‑контейнеры и разворачивается на базе Proxmox:

- **FastAPI** – REST‑API сервер, предоставляющий эндпоинты для загрузки документов, поиска по нормативным документам и получения отчетов.  
- **PostgreSQL** – реляционная база данных для хранения пользовательских учётных записей, истории запросов и служебных метаданных.  
- **ChromaDB** – векторное хранилище, использующееся для RAG‑поиска нормативных актов (НТД).  
- **Ollama** – локальный runner для_models (Llama‑3‑8B‑Instruct, Phi‑3‑Mini и др.), обслуживающий запросы к LLM‑модели в условиях ограниченного железного обеспечения.

## Требования к Proxmox
- **Виртуалка или контейнер** с минимум 4 ГБ ОЗУ, 2 CPU и 50 ГБ дискового пространства (рекомендуется «thin»‑размещение).  
- Официальный дистрибутив **Ubuntu 22.04 LTS** (или другая поддерживаемая ОС).  
- Доступ к внешней сети для скачивания образов Docker.  
- Установленный **Docker** + **Docker Compose** (см. раздел «Установка»).

## Пошаговая инструкция развертывания

### 1. Подготовка виртуального образa
1. В веб‑интерфейсе Proxmox создать новый VM (или контейнер).  
2. Рекомендуемые ресурсы:  
   - ОЗУ – 4 ГБ (можно увеличить после тестов).  
   - CPU – 2 ядерца (можно расширить).  
   - Диск – 50 GB (размер «thin», подключить к хранилищу).  
3. Установить **Ubuntu 22.04 LTS**, выполнить первоначальную настройку (сеть, обновления).

### 2. Установка Docker и Docker Compose
```bash
sudo apt update && sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
```
Проверить: `docker version && docker compose version`.

### 3. Клонирование репозитория
```bash
git clone https://github.com/gubarandrej-bit/claude.git
cd claude
```

### 4. Настройка переменных окружения
Создать файл **`.env`** в корне проекта со следующими переменными (пример):
```dotenv
POSTGRES_USER=verification_user
POSTGRES_PASSWORD=SuperSecretPassword123
POSTGRES_DB=verification_db

CHROMA_DB_SLIMIT=0          # отключить авто‑удаление старых чанков
OLLAMA_MODEL=llama3-8b       # выбранный локальный LLM
OLLAMA_HOST=http://localhost:11434

# При необходимости добавить дополнительные переменные,
# указанные в файле .env.example.
```

### 5. Запуск через Docker Compose
```bash
# Скачивание всех образов
docker compose pull

# Запуск всех сервисов в фоновом режиме
docker compose up -d
```

После старта проверьте статус контейнеров:
```bash
docker compose ps
docker compose logs -f   # просматривать логи в реальном времени
```

### 6. Проверка работоспособности
- Откройте в браузере `http://<IP‑адрес‑сервера>:8000/docs`.  
  Это интерактивный Swagger‑документ FastAPI, где можно выполнить тестовые запросы.  
- Примеры запросов:  
  - `POST /upload` – загрузка `.xls/.doc/.pdf/.dwg`.  
  - `GET /verify` – запуск проверочного цикла.  
  - `GET /models` – список доступных моделей.

### 7. Обслуживание и обновление
- **Обновление образов**: `docker compose pull && docker compose up -d`.  
- **Бекапы базы данных**:
  ```bash
  docker exec -t <postgres_container_name> pg_dump -U verification_user verification_db > backup_$(date +%F).sql
  ```
- **Мониторинг**: `docker stats` показывает загрузку CPU/Memory каждого контейнера.

## Настройка обратного прокси и HTTPS (опционально)

Для продакшн‑доступности рекомендуется разместить **Nginx** перед FastAPI и включить TLS‑сертификаты (Let's Encrypt):

```nginx
server {
    listen 443 ssl;
    server_name docs.example.com;

    ssl_certificate /etc/letsencrypt/live/docs.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/docs.example.com/privkey.pem;

    location / {
        proxy_pass http://host.docker.internal:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

После настройки запустить Certbot:
```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d docs.example.com
# Перезапустить Nginx
sudo systemctl restart nginx
```

## Вопросы и поддержка
- При проблемах с доступностью/производительностью проверьте логи: `docker compose logs -f`.  
- Метрики CPU/Memory можно наблюдать через `docker stats`.  
- Обратная связь приветствуется: открывайте **Issue** в репозитории.

---  
*Документ подготовлен дляcommit в репозиторий, чтобы любой администратор Proxmox мог быстро развернуть систему проверки в пределах выделенных ресурсов.*  
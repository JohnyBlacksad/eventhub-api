.PHONY: up down logs build ps clean

# Запустить всё (основной проект + логирование)
up:
	docker compose -f docker-compose.yml -f docker-compose.logging.yml up

# Запустить в фоновом режиме (detached)
up-d:
	docker compose -f docker-compose.yml -f docker-compose.logging.yml up -d

# Остановить и удалить контейнеры
down:
	docker compose -f docker-compose.yml -f docker-compose.logging.yml down

# Остановить, удалить контейнеры и volumes (полный сброс)
clean:
	docker compose -f docker-compose.yml -f docker-compose.logging.yml down -v

# Пересобрать и запустить
build:
	docker compose -f docker-compose.yml -f docker-compose.logging.yml up --build

# Показать статус контейнеров
ps:
	docker compose -f docker-compose.yml -f docker-compose.logging.yml ps

# Смотреть логи в реальном времени
logs:
	docker compose -f docker-compose.yml -f docker-compose.logging.yml logs -f

# Смотреть логи конкретного сервиса (пример: make logs-api SERVICE=api)
logs-service:
	docker compose -f docker-compose.yml -f docker-compose.logging.yml logs -f $(SERVICE)

# Restart all
restart: down up

# Restart конкретного сервиса (пример: make restart-service SERVICE=api)
restart-service:
	docker compose -f docker-compose.yml -f docker-compose.logging.yml restart $(SERVICE)
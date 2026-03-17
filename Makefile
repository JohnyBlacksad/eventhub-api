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


# Запустить все тесты
test:
	poetry run pytest

# Запустить только unit тесты
test-unit:
	poetry run pytest -m UNITS -v

# Запустить только integration тесты
test-integration:
	poetry run pytest -m INTEGRATION -v

# Запустить тесты с Allure отчётом
test-allure:
	@echo "Running tests with coverage..."
	poetry run pytest --cov=app \
		--cov-report=xml:./tests/reports/allure-results/coverage.xml \
		--cov-report=html:./tests/reports/coverage-html \
		--alluredir=./tests/reports/allure-results

	@echo "Generating Allure report..."
	allure generate --output ./allure-report ./tests/reports/allure-results

	@echo "Opening report..."
	allure open ./allure-report

# Сгенерировать отчёт из существующих результатов
allure-report:
	allure generate --output ./allure-report ./tests/reports/allure-results
	allure open ./allure-report

# Очистить Allure отчёты
allure-clean:
	rm -rf ./allure-report ./allure-history.jsonl ./tests/reports/allure-results ./tests/reports/coverage-html


# Проверка Quality Gate (локально)
quality-gate:
	@echo "Running Quality Gate check..."
	poetry run python scripts/quality_gate.py ./tests/reports/allure-results/coverage.xml

# Полная проверка для CI/CD
ci-check: test-allure quality-gate
	@echo "All checks passed!"
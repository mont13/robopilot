# Frontend service management
start:
	docker-compose up -d --build

stop:
	docker-compose down

restart: stop start

dev:
	docker-compose up --build

dev-detached:
	docker-compose up -d --build

build:
	docker-compose build

build-prod:
	docker-compose build --target production

shell:
	docker-compose exec frontend sh

logs:
	docker-compose logs -f frontend

install:
	docker-compose run --rm frontend yarn install

clean:
	docker-compose down
	docker system prune -f

help:
	@echo "Available commands:"
	@echo "  start/stop/restart - Service management"
	@echo "  dev/dev-detached   - Development modes"
	@echo "  build/build-prod   - Build operations"
	@echo "  shell/logs         - Container access"
	@echo "  install/clean      - Maintenance"

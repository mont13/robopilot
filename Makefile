# Main commands
startd:
	docker-compose -f docker-compose.yml up -d --build \
		&& docker-compose run --rm server poetry run alembic upgrade head

stopd:
	docker-compose -f docker-compose.yml down

# User management
create-admin:
	docker-compose -f docker-compose.yml run --rm server poetry run python create_admin.py

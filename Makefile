## Command to spin up the docker containers
docker-up:
	docker-compose -f deployment/docker-compose.yaml --env-file .env up -d

## Command to bring down the docker containers
docker-down:
	docker-compose -f deployment/docker-compose.yaml --env-file .env down

## Executes the pre-commit hooks on all files
run-pre-commit:
	pre-commit run -a

## Execute migrations for postgres
migrate:
	yoyo apply --database postgresql://btc_user:btc_user@localhost:5433/btc_exchange_data

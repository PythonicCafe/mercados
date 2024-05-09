lint:
	autoflake --in-place --recursive --remove-unused-variables --remove-all-unused-imports mercadobr
	isort mercadobr
	black -l 120 mercadobr

bash: 					# Run bash inside `main` container
	docker compose run --rm -it main bash

bash-root: 				# Run bash as root inside `main` container
	docker compose run --rm -itu root main bash

build: 					# Build containers
	docker compose build

container-clean: 		# Clean orphan containers
	docker compose down -v --remove-orphans

help:					# List all make commands
	@awk -F ':.*#' '/^[a-zA-Z_-]+:.*?#/ { printf "\033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | sort

kill:					# Force stop (kill) and remove containers
	docker compose kill
	docker compose rm --force

test:					# Execute `pytest` inside `main` container
	docker compose run --rm -it main pytest

test-v:					# Execute `pytest` with verbose option inside `main` container
	docker compose run --rm -it main pytest -vvv

.PHONY:	bash bash-root build container-clean help kill lint test test-v

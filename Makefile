TAGS_FILE = .tags

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

lint:					# Run linter script inside `main` container
	docker compose run --rm -it main /app/scripts/lint.sh

release:				# Build and release the package to PyPI
	rm -rf build dist
	docker compose run --rm -it main python setup.py sdist bdist_wheel
	docker compose run --rm -it main twine check dist/*
	docker compose run --rm -it main twine upload dist/*

tags:					# Generate tags file for the entire project (requires universal-ctags)
	@git ls-files | ctags -L - --tag-relative=yes --quiet --append -f "$(TAGS_FILE)"

test-release:			# Build and test-release the package (to test.pypi.org)
	rm -rf build dist
	docker compose run --rm -it main python setup.py sdist bdist_wheel
	docker compose run --rm -it main twine check dist/*
	docker compose run --rm -it main twine upload --repository-url https://test.pypi.org/legacy/ dist/*

test:					# Execute `pytest` inside `main` container
	docker compose run --rm -it main pytest --doctest-modules $(TEST_ARGS) mercados/ tests/

.PHONY:	bash bash-root build container-clean help kill lint release tags test-release test

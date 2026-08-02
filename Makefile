TAGS_FILE = .tags
ifeq ($(CI),true)
    DOCKER_EXEC_FLAGS = -T
else
    DOCKER_EXEC_FLAGS = -it
endif
COMPOSE = docker compose
COMPOSE_RUN = $(COMPOSE) run --rm $(DOCKER_EXEC_FLAGS)

ifeq ($(ENV_TYPE),development)
    MAIN_RUN =
    EXAMPLE_RUN = PYTHONPATH=/app
else
    MAIN_RUN = $(COMPOSE_RUN) main
    EXAMPLE_RUN = $(COMPOSE_RUN) --quiet-build -e PYTHONPATH=/app main
endif

bash: 					# Run bash inside `main` container
	$(MAIN_RUN) bash

bash-root: 				# Run bash as root inside `main` container
	$(COMPOSE_RUN) -u root main bash

build: 					# Build containers
	docker compose build

clean:					# Remove build/dist files
	rm -rf build dist

cloc:					# Count lines of code
	cloc mercados/ tests/

container-clean: 		# Clean orphan containers
	docker compose down -v --remove-orphans

help:					# List all make commands
	@awk -F ':.*#' '/^[a-zA-Z_ -]+:.*?#/ { printf "\033[36m%-15s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST) | sort

kill:					# Force stop (kill) and remove containers
	docker compose kill
	docker compose rm --force

lint:					# Run linter script inside `main` container
	$(MAIN_RUN) /app/scripts/lint.sh

man: VERSION := $(shell grep --color=no __version__ mercados/__init__.py | sed 's/.*"\([^"]\+\)"/\1/')
man:					# Create man page
	$(MAIN_RUN) argparse-manpage \
		--pyfile "mercados/__main__.py" \
		--function "_cria_parser" \
		--author "Álvaro Justen <alvaro@pythonic.cafe>" \
		--project-name "mercados" \
		--url "https://github.com/PythonicCafe/mercados/" \
		--output "docs/mercados.1" \
		--version "$(VERSION)"

release: UPLOADS_OPTS=
test-release: UPLOAD_OPTS=--repository-url https://test.pypi.org/legacy/
release test-release: clean man		# Build and release the package to PyPI/Test PyPI
	$(MAIN_RUN) python setup.py sdist bdist_wheel
	$(MAIN_RUN) twine check dist/*
	$(MAIN_RUN) twine upload $(UPLOAD_OPTS) dist/*

shell:					# Execute IPython inside `main` container
	$(MAIN_RUN) ipython

smoke-test:				# Run smoke test script inside `main` container
	$(MAIN_RUN) /app/scripts/smoke-test.sh

smoke-test-examples:	# Run each .py in exemplos/ as a smoke test inside `main` container
	@for example in exemplos/*.py; do \
		echo "Running $$example..."; \
		$(EXAMPLE_RUN) python "/app/$$example" || exit 1; \
	done

tags:					# Generate tags file for the entire project (requires universal-ctags)
	@git ls-files | ctags -L - --tag-relative=yes --quiet --append -f "$(TAGS_FILE)"

test:					# Execute `pytest` and coverage report inside `main` container
	$(MAIN_RUN) bash -c 'coverage run -m pytest $(TEST_ARGS) && coverage report'


.PHONY:	bash bash-root build clean cloc container-clean help kill lint release man shell smoke-test smoke-test-examples tags test-release test

lint:
	autoflake --in-place --recursive --remove-unused-variables --remove-all-unused-imports mercadobr
	isort mercadobr
	black mercadobr

.PHONY:	lint

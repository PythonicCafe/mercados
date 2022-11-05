lint:
	autoflake --in-place --recursive --remove-unused-variables --remove-all-unused-imports mercadobr
	isort mercadobr
	black -l 120 mercadobr

.PHONY:	lint

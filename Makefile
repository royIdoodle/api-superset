.PHONY: setup run db-init

setup:
	bash scripts/setup.sh

run:
	bash scripts/run.sh

db-init:
	bash scripts/db_init.sh



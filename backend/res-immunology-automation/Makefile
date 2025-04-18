# Generic makefile created for a poetry based python
.DEFAULT_GOAL := help
.PHONY: help 

DEST_REPO := dev

help: ## This prints help text for all the existing commands
	@grep -E '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%25s:\033[0m %s\n", $$1, $$2}'


build: ## Builds the python package with scripts and libraries
	@poetry build

publish: build ## Publishes the package (with libs and scripts) in the dev repo. 
	@poetry publish -r $(DEST_REPO)

install: build ## Installs the package locally. Use for dev testing. 
	@poetry install


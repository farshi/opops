
SHELL := /bin/bash
RED    := \033[0;31m
YELLOW := \033[1;33m

help: 
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
.DEFAULT_GOAL := help

usage: ## show usage for opops
	@echo "usage"

ansible: ## ansible operations
	@echo "ansible operations"

aws: ## docker operations
	@echo "commands for docker"

docker: ## docker operations
	@cat "files/docker.txt"
	@printf "\n\n${YELLOW} List of commands: \n\n"
	@cd $(OPOPS_HOME)/docker ; make help

mobile: ## mobile operations
	@echo "mobile operations"

packer: ## packer operations
	@echo "packer operations"

security: ## security operations
	@echo "security operations"

server: ## server operations
	@echo "server operations"

setup: ## setup operations
	@cat "files/setup.txt"

saveVar: ## setup operations
	@cat files/saveVar.txt

vars: ## Show currnet variable values


.PHONY: help 
.DEFAULT_GOAL := help



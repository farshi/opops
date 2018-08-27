help: 
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
.DEFAULT_GOAL := help

setup-mac-local: ## setup personal macOSx
	echo "setup personal macOSx "
	@./scripts/setup-mac.sh

setup-mac-agent: ## setup macOSx agent
	echo "setup macOSx go-Agent "
	@./scripts/setup-mac.sh

setup-linux-agent: ## setup linux agent
	echo "setup linux agent "
	@./scripts/setup-linux.sh

java-certs: ## Install Java Certs
	 @./scripts/install-java-cert.sh

remove-go-aws-creds: ## Remove AWS credentials from Go-Agent 
	@printf  "Remove AWS credentials from go-agent..."
	@rm -rf /var/go-agent/.aws/credentials
	@rm -rf /var/go-agent/.aws/config

 
install-awscli: ## install awscli
	@sh ./scripts/tools-installer.sh awscli   

 
check-tools-installed: ## check tools installed. comma seperated tools
	@sh ./scripts/tools-checker.sh  "pyhton2,docker,java8,packer,ruby"
	
.PHONY: help 
.DEFAULT_GOAL := help



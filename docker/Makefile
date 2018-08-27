
BUILD_BRANCH ?="develop"
SERVER_VERSION ?="latest"

# grep the version from the mix file
VERSION=$(shell ./scripts/version.sh)
PASSWORD=$(shell ./scripts/password.sh)

# HELP
# This will output the help for each task
# thanks to https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
.PHONY: help

help: ## List all commands for running atlas operate server in docker including package buildin
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help
update-java-image: ## Update java image from internet to apro
	@echo 'Udating java image in APRO'
	@docker pull java:8 ;\
	docker tag java:8 $(DOCKER_REPO)/java ;\
	docker push $(DOCKER_REPO)/java 

# DOCKER TASKS
# Build the container
build: ## Build the container
	docker build -t $(APP_NAME) $(Dockerfile) --build-arg AppEnv=$(AppEnv)

build-nc: ## Build the container without caching
	docker build --no-cache -t $(APP_NAME) $(Dockerfile) --build-arg AppEnv=$(AppEnv)

stop-atlas: ## Stop docker instance for atlas 
	-@docker ps | grep $(APP_NAME) | awk '{ print $$1 }' | xargs docker kill > /dev/null

clean-atlas-image:  stop-atlas ## Remove docker images for atlas 
	-@ docker images --filter=reference='atlas' --format "{{.ID}}" | xargs docker rmi --force

clean-all-images: ## Forced Clean docker images
	-@docker images -q | xargs docker rmi --force

pull-run-atlas: login  stop-atlas ## Pull atlas docker image and run in background
	@echo pulling and running docker for atlas opereate  $(DOCKER_REPO)/$(APP_NAME):$(SERVER_VERSION) ;\
	docker pull $(DOCKER_REPO)/$(APP_NAME)/$(BUILD_BRANCH):$(SERVER_VERSION) ;\
	docker run  -i -d -t --rm   -p=$(PORT):$(PORT) -e TZ=Australia/Sydney --name="$(APP_NAME)" $(DOCKER_REPO)/$(APP_NAME)/$(BUILD_BRANCH):$(SERVER_VERSION)  

run: ## Run container on port configured in `config.env`
	docker run -i -d -t --rm  -v "tmp:/tmp" --env-file=./config.env -p=$(PORT):$(PORT) -e TZ=Australia/Sydney --name="$(APP_NAME)" $(APP_NAME)
sleep-a-bit:
	@echo Waiting for server ..
	@sleep 80

smoke-test: sleep-a-bit check-atlas-running top-atlas

	
depricated-check-atlas-running:  
	@$(eval alive:= $(shell curl -s --insecure   --head  http://localhost:8080/atlasoperate/api/operate-server-build-summary  | head -1 | grep 200 )) 
	@alive="$(alive)" ;\
	while [ -z "$$alive" ] ; do \
		echo "waiting for Atlas operate to be up and running..." ;\
    	sleep 120 ;\
		url="http://localhost:8080/atlasoperate/api/operate-server-build-summary" ;\
		alive=`curl  -s --head  $$url | head -1 | grep '200' ` ;\
    done; echo "Atlas operate is running! "
	curl http://localhost:8080/atlasoperate/api/operate-server-build-summary


check-atlas-running: sleep-a-bit ## Check atlas app is running 
	@echo checking atlas is healthy and running ...
	@!(python ../common/scripts/atlas-ops.py -H  -url "localhost:8080" ) || ( echo "app is not running , see the logs in docker.log " ; docker logs atlas-operate-server > docker.log ; exit 1)
	docker logs atlas-operate-server > docker.log

up: login build run ## Run container on port configured in `config.env` (Alias to run)


release: login  build publish ## release by building and publishing the `{version}` and `latest`  to docker repo

# Docker publish
publish: publish-latest publish-version ## Publish the `{version}` ans `latest` tagged containers to docker repo

publish-latest: tag-latest ## Publish the `latest` taged container to docker repo
	@echo 'publish latest to $(DOCKER_REPO)'
	docker push $(DOCKER_REPO)/$(APP_NAME)/$(BUILD_BRANCH):latest

publish-version: tag-version ## Publish the `{version}` taged container to docker repo
	@echo 'publish $(VERSION) to $(DOCKER_REPO)'
	docker push $(DOCKER_REPO)/$(APP_NAME)/$(BUILD_BRANCH):$(VERSION)

# Docker tagging
tag: tag-latest tag-version ## Generate container tags for the `{version}` ans `latest` tags

tag-latest: ## Generate container `{version}` tag
	@echo 'create tag latest'
	docker tag $(APP_NAME) $(DOCKER_REPO)/$(APP_NAME)/$(BUILD_BRANCH):latest

tag-version: ## Generate container `latest` tag
	@echo 'create tag $(VERSION)'
	docker tag $(APP_NAME) $(DOCKER_REPO)/$(APP_NAME)/$(BUILD_BRANCH):$(VERSION)

# HELPERS

# generate script to login to aws docker repo
CMD_REPOLOGIN := "eval $$\( aws ecr"
ifdef AWS_CLI_PROFILE
CMD_REPOLOGIN += " --profile $(AWS_CLI_PROFILE)"
endif
ifdef AWS_CLI_REGION
CMD_REPOLOGIN += " --region $(AWS_CLI_REGION)"
endif
CMD_REPOLOGIN += " get-login --no-include-email \)"

ssh:
	docker exec -it atlas-operate-server   bash
logs:
	docker logs atlas-operate-server 

repo-ecr-login:  ## Login to AWS-ECR
	@sh login_aws.sh ;\
	eval $(CMD_REPOLOGIN)

login:  ## Login to  APRO docker repo

	@echo "login into $(DOCKER_REPO) ..." 		
	@docker login "$(DOCKER_REPO)"  --username "$(ARTIFACTORY_USERNAME)" --password "$(PASSWORD)" || (echo "login failed" ; exit 1)
	
	

version: ## Output the current version
	@echo $(VERSION)
	
password:
	@echo $(PASSWORD)

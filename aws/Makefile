# Author: Reza Farshi (reza.farshi@versent.com.au)
# Makefile for making aws AMIS and managing cloudformation stacks

BUILDNUM:=$(subst  .,,$(BUILD_NUMBER))

	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
.DEFAULT_GOAL := help

	
get_kms_key_id:  ## Getting KMS KEY ID from AWS account , Returns RT_KMS_KEY_ID
	@$(eval KMS_KEY_ID := $(shell aws cloudformation describe-stacks  --stack-name $(KMS_STACK)   --query 'Stacks[*].Outputs[*].[OutputKey,OutputValue]' --output text | grep -w  'outputKmsmobc'  |  awk -F ' ' '{print $$2}' ))
	@(test -n "${KMS_KEY_ID}" ) || (printf "${RED}Error, KMS_KEY_ID must be a valid string ${NC}\n" && exit 1)
	@$(OPOPS_HOME)/opops saveVar "RT_KMS_KEY_ID" "$(KMS_KEY_ID)"
	@echo "KMS Key ID:$(KMS_KEY_ID)"


get-vpc-id: ## Getting VPC_ID from AWS account , Returns RT_VPC_ID
	@$(eval VPC_ID := $(shell aws ec2 describe-vpcs   --filters "Name=tag:${VPC_TAG_KEY},Values=${VPC_TAG_VALUE}" --query 'Vpcs[0].VpcId' --output text | grep - ))
	@test -n "${VPC_ID}"  || ( echo "Could not VPC_ID for ${VPC_TAG_VALUE} " ; exit 1 )
	@echo "VPC_ID: `echo ${VPC_ID}`"
	@$(OPOPS_HOME)/opops saveVar "RT_VPC_ID" "$(VPC_ID)"


get-subnet-id:  ## Getting SUBNET_ID from AWS account , Returns RT_SUBNET_ID
	@$(eval SUBNET_ID := $(shell  aws ec2 describe-subnets --filters "Name=vpc-id,Values=$${VPC_ID},Name=tag:${SUBNET_TAG_KEY},Values=${SUBNET_TAG_VALUE}" --query 'Subnets[0].SubnetId' --output text  | grep - ))
	@test -n "${SUBNET_ID}"  || ( echo "Could not SUBNET_ID for ${SUBNET_TAG_VALUE}  " ; exit 1 )
	@echo "SUBNET_ID: `echo ${SUBNET_ID}`"
	@$(OPOPS_HOME)/opops saveVar "RT_SUBNET_ID" "$(SUBNET_ID)"

verify_ami_exist: AMI_NAME:="atlas-operate-ami-$(ATLAS_ENVIRONMENT)-$(GO_PIPELINE_LABEL)"

verify_ami_exist: ## check AtlasOperate AMI : atlas-operate-ami-$(ATLAS_ENVIRONMENT)-$(GO_PIPELINE_LABEL) exist  , Returns RT_AMI_ID
	$(eval AMI_ID:=$(shell ( aws ec2 describe-images  --filters "Name=name,Values=$(AMI_NAME)"  --query 'Images[0].ImageId' ) | grep - ) )
	@(test -n "${AMI_ID}" ) || ( echo "Could not find AMI_ID for $(AMI_NAME) ! "  )
	@(test -z "${AMI_ID}" ) || ( echo "AMI for this build exist , AMI ID: $(AMI_ID)" )
	@$(OPOPS_HOME)/opops saveVar "RT_AMI_ID" "$(AMI_ID)"


health-check: ## do heatlh-chek for ELB for stack $(StackName_ASG) 
	@echo "Checking ELB health.."
	@!(buildNumber=$(BUILDNUM) python ./scripts/elb-ops.py -H -s $(StackName_ASG) -d ${DOMAIN} ) || ( echo "health check failed "; exit 1)

clean: ## Remove the build/output directories 
	@mkdir -p ./build
	@rm -rf ./build/*
	@printf "temp build info is now cleaned!\n"


########################################
# Operate_Server Stack
########################################
check-stack-exists: ## Check stack exist for $(STACK_NAME)
	@printf "Check stack exist for $(STACK_NAME) ..."
	$(eval STACK_EXISTS := $(shell aws cloudformation describe-stacks   --stack-name $(STACK_NAME) | grep 'StackId'  ) )
	@test -z "${STACK_EXISTS}"  ||  echo stack_exist : $(STACK_EXISTS)


init-default-param: clean
	@echo  "Init param file for the stack ..."
	@mkdir -p ./build/envs/$(ATLAS_ENVIRONMENT)
	@mkdir -p ./cloudformation
	@cp -r ./envs/$(ATLAS_ENVIRONMENT) ./build/envs/

config-asg-vars:   init-default-param verify_ami_exist  ## Config vars in  /envs/[ENV]/default_paramas to be used by cloudformation
	@(test -n "${AMI_ID}" ) || ( echo "Could not find AMI_ID for $(AMI_NAME) ! " ; exit 1 )
	@echo -e "  ImageId: \"$(strip $(AMI_ID))\"" >> $(ENV_PARAM_FILE)
	@echo -e "  PipelineNumber: \"$(strip $(BUILDNUM))\"" >> $(ENV_PARAM_FILE)
	
	@$(eval STACK_NAME := $(StackName_ASG) )
	

create-update-atlas-asg-stack: config-asg-vars check-stack-exists gencfn ## Create Auto-scaling cloudformation stack for Atlas application
	@printf  "Creating/Updating operate-server stack...\r\n"
	@test -z "${STACK_EXISTS}"  || (printf "updating ASG stack ... \r\n" )
	@test -n "${STACK_EXISTS}"  || (printf "creating ASG stack ... \r\n" )
	@aws cloudformation  create-stack      --stack-name  $(StackName_ASG) --template-body \
    	file://`pwd`/cloudformation/aws-asg-alb.yml  --capabilities CAPABILITY_IAM  

	@sh ./scripts/cfn-pgcheck.sh  $(StackName_ASG)

find-previous-atlas-stack:
	@printf  "Finding previous cloudformation stack for Atlas...\r\n"
	@$(eval PREV_STACK_NAME := $(shell aws cloudformation  list-stacks --stack-status-filter 'CREATE_COMPLETE' 'UPDATE_COMPLETE'    --query 'reverse(sort_by(StackSummaries[*],&CreationTime)[].{ID:StackId , Name:StackName  , CRT:CreationTime})' --output json  | jq '.[].Name | select (contains ("atlas-${ATLAS_ENVIRONMENT}-asg-"))' |  sed -n 2p ))
	@echo ${PREV_STACK_NAME}
	
delete-previous-asg-stack: find-previous-atlas-stack ## Remove the Auto-scaling cloudformation stack for Atlas Application
	@echo "Deleting  operateserver stack"
	@test -z "${PREV_STACK_NAME}" ||  python ./scripts/cfn-decomission.py --stack  $(PREV_STACK_NAME) -y
	
	
########################################
# # Rds Stack
########################################

filter-atlas-rds: ## get RDS instance ARN if matches with $filter env variable and return RT_RDS_ARN
	@test -n "${filter}"  || (printf "filter must be a valid string , run aws  filter-atlas-asg filter="your-env-name" \r\n"  && exit 1 )
	@$(eval RDS_ARN := $(shell sh ./scripts/filter-rds.sh atlas-operate-rds-$(filter) | tail -1 ) )
	@test -n "${RDS_ARN}"  || (printf " Could not find ARN for this db name atlas-operate-rds-$(filter)  \r\n"  && exit 1 )
	@echo "RDS ARN for $(filter) environmet : $(RDS_ARN) "
	@$(OPOPS_HOME)/opops saveVar "RT_RDS_ARN" "$(RDS_ARN)"


list-all-atlas-rds: ## list all rds instances for atlas operate
	@sh ./scripts/filter-rds.sh "atlas-operate"

 
filter-atlas-asg: ## get autoscalin-group  NAME if matches with $filter env variable and return RT_ASG_ARN
	@test -n "$(filter)"  || (printf "filter must be provided as a valid string.run aws  filter-atlas-asg filter="your-env-name" \r\n"  && exit 1 )
	@$(eval ASG_NAME := $(shell sh ./scripts/filter-asg.sh atlas-$(filter)-aws | tail -1 ) )
	@test -n "${ASG_NAME}"  || (printf " Could not find ASG name with this pattern  atlas-$(filter)-aws   \r\n"  && exit 1 )

	@echo "ASG name for $(filter) environmet : $(ASG_NAME) "
	@$(OPOPS_HOME)/opops saveVar "RT_ASG_NAME" "$(ASG_NAME)"

list-all-atlas-asg: ## list all rds instances for atlas operate
	@sh ./scripts/filter-asg.sh "atlas-"

atlas-rds-start: filter-atlas-rds
	echo " Starting RDS for $(filter) "
	# do some coding to start rds
	echo "Waiting for Rds to start ..."
	#code for waiting
	echo "RDS for  $(filter) started "


atlas-rds-stop: filter-atlas-rds
	echo " Stopping RDS for $(filter) "


atlas-asg-update: filter-atlas-asg ## Update autoscaling group foratlas env in AWS for mentioned env in $filter . e.g filter=bit ,  var asg_min_size and desired_capacity required!
	@echo Updating ASG  for $(filter) Atlas Servers
	@test -n "$(desired_capacity)" || (printf "desired_capacity  must be provided as a valid string e.g desired_capacity=1  \r\n"  && exit 1 )
	@test -n "$(asg_min_size)"  || (printf "asg_min_size must be provided as a valid string. e.g asg_min_size=1  \r\n"  && exit 1 )
	aws autoscaling update-auto-scaling-group --auto-scaling-group-name $(ASG_NAME) --min-size $(asg_min_size)
	aws autoscaling set-desired-capacity --auto-scaling-group-name $(ASG_NAME) --desired-capacity $(desired_capacity)  --honor-cooldown


atlas-up: atlas-rds-start atlas-asg-update  ## Bring up atlas env in AWS for mentioned env in $filter . e.g filter=bit
	@echo "bringing $(filter) environment up "
	
########################################
# AWS Blue Green Switch 
########################################
blue-green: ## Switching from Blue to Green Env
	@echo "Blue-Green switch..."
	@buildNumber=$(BUILDNUM) python ./scripts/elb-ops.py -G -s $(StackName_ASG) -d ${DOMAIN}

########################################
# AWS Utils
########################################

login: ## Create AWS CLI session using Saml2aws
	@sh ./scripts/login_aws.sh


gencfn: init-default-param## Generate Cloudformation script using cfndsl tool
	@printf  "Generate cloudformation using cfn-dsl rake...\r\n"
	@sh ./scripts/gencfn.sh 


.PHONY: help gencfn aws_debug_check aws_check_environment  build-ami debug-ami aws_credential_check clean ami_build_pre_check
.DEFAULT_GOAL := help



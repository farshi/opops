#!/bin/bash

export ACCOUNT_TYPE="${ACCOUNT_TYPE:-np}"

export TOOLS_DIR=~/tools/

if [[  -z $OPERATE_SAML2AWS_USERNAME ]]; then
    printf "Enter your AD Username:"
    read  OPERATE_SAML2AWS_USERNAME && export OPERATE_SAML2AWS_USERNAME 
    
fi
if [[  -z $OPERATE_SAML2AWS_PASSWORD ]]; then
    printf " Enter your AD Password ($OPERATE_SAML2AWS_USERNAME):"
    read -s OPERATE_SAML2AWS_PASSWORD && export OPERATE_SAML2AWS_PASSWORD
fi

export domain="domain"

export OPERATE_SAML2AWS_USERNAME="$domain\\$OPERATE_SAML2AWS_USERNAME"

export AWS_PROFILE=saml
 
export AWS_DEFAULT_REGION=us-west-2

export SAML_ACCOUNT='AWS-NonProd'
 
export np_account=123456789
export pr_account=123456789

export role="developer-role"
export SAML2AWS_IAM_ROLE_ARN="arn:aws:iam:${np_account}:$:role/${role}"


if [[ "$ACCOUNT_TYPE" == "pr" ]]; then 
    export SAML_ACCOUNT='AWS-Prod'
    export SAML2AWS_IAM_ROLE_ARN="arn:aws:iam:${pr_account}:$:role/${role}"
fi


export saml2awsbin=`which saml2aws`
if [ -n $saml2awsbin ]; then
    TOOLS_DIR=$(dirname "$saml2awsbin")
else
    echo "please intall saml2aws and put in $TOOLS_DIR direcotry "
fi


echo $OPERATE_SAML2AWS_PASSWORD | ${TOOLS_DIR}/saml2aws  --account "${SAML_ACCOUNT}" --username "${OPERATE_SAML2AWS_USERNAME}" --iam-role-arn "${SAML2AWS_IAM_ROLE_ARN}" login

RETVAL=$?
if [[ ! $RETVAL -eq 0 ]]; then
    unset OPERATE_SAML2AWS_USERNAME
    unset OPERATE_SAML2AWS_PASSWORD
fi 

exit $RETVAL


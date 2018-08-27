
#!/bin/bash -e

#This script will chack the progress of cloudformation for a given stackname 
Stack_Name=$1

if [ -z "$AWS_PROFILE" ]; then
  AWS_PROFILE='saml'
fi
P="--profile $AWS_PROFILE"
echo "Using ${AWS_PROFILE} aws cli profile"

awsregion='ap-southeast-2'
inprogress=true
while $inprogress; do
   allres=$(aws $P --region $awsregion cloudformation describe-stack-events --stack-name $Stack_Name --query 'StackEvents[*].[ResourceType,LogicalResourceId,ResourceStatus]' --output text; printf x); allres=${allres%x}
   lastres=$(sed -n '/CREATE_COMPLETE/ p' <<< "${allres}"; printf x); lastres=${lastres%x}
   errres=$(sed -n '/CREATE_FAILED/ p' <<< "${allres}")
   newres=${lastres%"$prevres"}
   printf "%s" "${newres}"
   if [[ $newres == *'AWS::CloudFormation::Stack'* ]]; then echo "Step Complete"; inprogress=false; fi
   if [[ $errres == *'CREATE_FAILED'* ]]; then echo "Stack creation failed, exiting"; exit 1; fi
   prevres=$lastres
   sleep 3
done

echo "Create stack Complete, script finished successfully"


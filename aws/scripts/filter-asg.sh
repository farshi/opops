
#!/bin/bash
STR=$1
ARNS=$(aws autoscaling describe-auto-scaling-groups --query \
    "AutoScalingGroups[].AutoScalingGroupName" --output text)
for line in $ARNS; do
    #echo $line
    MATCHES=$( echo $line | grep  $STR)
    if [[ ! -z $MATCHES ]]; then
        echo $MATCHES
    fi
done


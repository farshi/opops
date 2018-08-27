
#!/bin/bash
STR=$1
ARNS=$(aws rds describe-db-instances --query "DBInstances[].DBInstanceArn" --output text)
for line in $ARNS; do
    #echo $line
    MATCHES=$( echo $line | grep  $STR)
    if [[ ! -z $MATCHES ]]; then
        echo $MATCHES
    fi
done

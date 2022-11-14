#!/bin/bash

FUNCTION_NAME=$1
ECR_URI=$2

info()
{
    echo "INFO: $1"
    return 1
}

aws lambda get-function --function-name $FUNCTION_NAME &> /dev/null || info "$FUNCTION_NAME was not deployed." || true

if [ $? = 0 ]; then
    echo "Updating Run Training Lambda..."
    aws lambda update-function-code --function-name $FUNCTION_NAME --image-uri $ECR_URI \
    || info "$FUNCTION_NAME lambda container was not updated."
    echo "Completed."
fi

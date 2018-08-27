#!/bin/bash

if [[ -n "${BUILD_NUMBER}" ]]; then
echo ${BUILD_NUMBER}
else
echo "latest"
fi

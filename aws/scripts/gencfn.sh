#!/bin/bash 
# Author: Reza Farshi (reza.farshi@versent.com.au)
# execute cfndsl

export unameOut=`uname -s`

case ${unameOut} in
    Linux*)     machine="linux";;
    Darwin*)    machine="Mac";;
    CYGWIN*)    machine="Cygwin";;
    MINGW*)     machine="MinGw";;
    *)          machine="UNKNOWN:${unameOut}"
esac
echo ${machine}


if [[ "$machine" = "linux" ]]; then 
    source /var/go-agent/.rvm/scripts/rvm
    rvm alias delete aws
    rvm alias create aws 2.4.2
    source $(rvm aws do rvm env --path)
    rvm gemset create aws
    ruby  --version
fi
cd cfndsl;rake --trace env=${ATLAS_ENVIRONMENT}

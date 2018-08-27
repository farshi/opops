#!/bin/bash

DIR="`dirname \"$0\"`"
FORCE_INSTALL="${FORCE_INSTALL:-$true}"
function Install_python(){

    grep -q "python_config_done" "${OPERATE_HOME}/stats"
    done_before=$?
    if [[ $done_before -eq 0   && "$FORCE_INSTALL" = "false" ]] ; then
         echo "python_config  done already! "
        return 0
    fi

    echo installing python packages
    export trusted_hosts="--trusted-host pypi.python.org  --trusted-host files.pythonhosted.org --trusted-host pypi.org --trusted-host pypi.python.org  "
    pip install ${trusted_hosts} pip setuptools
    pip install ${trusted_hosts} -r "${DIR}/../files/requirements.txt" 

    echo "python_config_done" >> "${OPERATE_HOME}/stats"

}

function doInit(){
    mkdir -p ~/.operate
    touch ~/.operate/stat
}

function Whitelist_docker_repo(){
    grep -q "docker_repo_whitelisted" "${OPERATE_HOME}/stats"
    done_before=$?
    if [[ $done_before -eq 0  && "$FORCE_INSTALL" = "false" ]] ; then
        echo "docker_repo_whitelisted done already! "
        return 0
    fi

    Entry="{\"insecure-registries\" : [\"${DOCKER_REPO}\" ]}"

    echo $Entry >  ~/.docker/daemon.json ;\
    echo " Whitelisting  ${DOCKER_REPO} repo " ;\
    osascript -e 'quit app "Docker"' ;\
    open -a Docker ;\
    printf "Restarting docker  ... " ;\
    sleep 20 ;\
    echo "Done!"
    echo "docker_repo_whitelisted" >> "${OPERATE_HOME}/stats"
}

doInit

Install_python
Whitelist_docker_repo
echo "Wait for docker dameon comes up ...."
sleep 30
echo "Tools are inplace and configured , good to go!"

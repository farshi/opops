#!/bin/sh
#set -o pipefail
# set -o nounset
# set -o xtrace


function Install_Python_Package(){
    python_package=$1
    grep -q "$python_package" "${OPERATE_HOME}/stats"
    done_before=$?
    if [[ "$done_before" -eq 0   && "$FORCE_INSTALL" = "false" ]] ; then
         echo "$python_package already has been instllaed! "
        exit 0
    fi

    echo Installing  $python_package ...
    export trusted_hosts="--trusted-host pypi.python.org  --trusted-host files.pythonhosted.org --trusted-host pypi.org --trusted-host pypi.python.org  "
    sudo pip install ${trusted_hosts} "$python_package"  &> /dev/null
    #pip install ${trusted_hosts} -r "${DIR}/../files/requirements.txt"
    echo "$python_package" >> "${OPERATE_HOME}/stats"
    echo "$python_package installed successfully! "

}

tool=$1

case "$tool" in
	pyhton2.7)
		;;
	java8)
		# java
		
		;;
	docker)
		# check docker
		
		;;
	ruby)
		# check ruby
		
		;;
	packer)
		# check packer
		
		;;
	ansible)
		# check ansible
		;;
	awscli)
		# check awscli
        Install_Python_Package awscli
		
		;;
    cfndsl)
    # check cfndsl
        ;;
    saml2aws)
    # check saml2aws
    
    ;;
	*)
		# Anything else (is there anything else?)
		echo "*** This tool checker not implemented" >&2
		exit 1
		;;
esac

# --- Finished
exit 0

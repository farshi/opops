#!/bin/sh
set -o pipefail
# set -o errexit
# set -o nounset
# set -o xtrace

export TERM="xterm-256color"

red=`tput setaf 1`
green=`tput setaf 2`
yellow=`tput setaf 3`
blue=`tput setaf 4`
white=`tput setaf 7`
reset=`tput sgr0`


function printToolStatus(){
	tool=$1
	status=$2
	version=$3
	if [[  "$status" -eq 0 ]] ; then
		printf "$green \xE2\x9C\x94 $yellow $tool\t: $Version \n"
	else
		printf "$red \xE2\x9C\x96 $yellow $tool \n"
	fi 
}


function checkToolsInstalled(){
tool=$1
tool_status=x
case "$tool" in

	pyhton2)
		#python 2
		tool_path=`which python` 
		if [[ -n "$tool_path" ]]  ; then 
			Version=`python -c 'import sys; version=sys.version_info[:3]; \
			 print("{0}.{1}.{2}".format(*version))'`
			echo $Version | grep -q  "2." 
			tool_status=$?
		fi
		;;
	pyhton3)
		#python 3
		tool_path=`which python` 
		if [[ -n "$tool_path" ]]  ; then 
			Version=`python -c 'import sys; version=sys.version_info[:3]; \
			 print("{0}.{1}.{2}".format(*version))'`
			echo $Version | grep -q  "3." 
			tool_status=$?
		fi
		;;

	java8)
		# java
		tool_path=`which java` 
		if [[ -n "$tool_path" ]]  ; then 
			Version=$($tool_path -version 2>&1 >/dev/null | grep 'java version' | awk '{print $3}' | tr -d '"')
			echo $Version | grep -q  "1.8.0" 
			tool_status=$?
		fi
		;;

	docker)
		# check docker
		tool_path=`which docker` 
		if [[ -n "$tool_path" ]]  ; then 
			Version=$($tool_path version --format '{{.Server.Version}}')
			tool_status=$?
		fi
		;;
	ruby)
		# check ruby
		
		;;
	packer)
		# check packer
		tool_path=`which packer` 
		if [[ -n "$tool_path" ]]  ; then 
			Version=$($tool_path -v)
			tool_status=$?
		fi
		
		;;
	ansible)
		# check ansible
		;;
	awscli)
		
		;;
    cfndsl)
    # check cfndsl
    	;;

    saml2aws)
    # check saml2aws
    
    ;;
	*)
		# Anything else (is there anything else?)
		echo "*** This tool checker not implemented , Volunteer?!" >&2
		exit 0
		;;
esac
if [[ "$tool_status" = "x" ]]; then
	echo "\n"
	printf "$red \xE2\x9C\x96"
	echo " Warning: $tool checker not implemented yet! Volunteer?"
	exit 0;
else
	printToolStatus $tool $tool_status $Version
fi
}
	#comma separated tools list. e.g : docker , java8 , awcli
	tools_list=$1
	echo "Checking for tools: $1 \n"
	for tool in $(echo $tools_list | sed "s/,/ /g")
	do
		checkToolsInstalled  "$tool"
	done



# --- Finished
exit 0

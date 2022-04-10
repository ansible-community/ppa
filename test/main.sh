#!/bin/bash
#
# Perform basic tests to verify that the Ansible package installed from ppa:ansible/ansible-* works as expected.
#

CliArg()
{
   # Display Help
   echo "Install Ansible from launchpad.net/~ansible ppa in a ubuntu container and run basic integration tests."
   echo
   echo "Usage: ./main.sh -c impish -p ansible"
   echo
   echo "options:"
   echo "c     Requires a valid Ubuntu code name. Eg: focal, impish, jammy."
   echo "p     Requires Ansible Launchpad PPA. Eg: ansible, testing-ansible, etc."
   echo "h     Print this Help."
   echo
}

# Get the options
while getopts 'c:p:h' option;
do
   case $option in
      h) CliArg
         exit;;
      c) CODE_NAME=$OPTARG;;
      p) PPA=$OPTARG;;
     \?) echo "Error: Invalid option"
         exit;;
   esac
done

if [[ ! ${CODE_NAME} || ! ${PPA} ]];
then
    echo "Type -h to display help."
    exit
fi

echo "\n\nUsing Docker Image: 'ubuntu:${CODE_NAME}'\n"
echo "Launchpad PPA: '${PPA}'\n\n"

docker container run --rm \
    --pull always \
    --name=${PPA}-${CODE_NAME} \
    -v $(pwd)/script.lib:/tmp/script.lib:ro \
    -v $(pwd)/test_vault.yml:/tmp/test_vault.yml:ro \
    -v $(pwd)/vault_pass:/tmp/vault_pass:ro \
    -e PPA=${PPA} \
    ubuntu:${CODE_NAME} /bin/bash /tmp/script.lib


#TODO
#
# 1.
# Format the output.

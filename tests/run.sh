#!/usr/bin/env bash

# References
# http://kvz.io/blog/2013/11/21/bash-best-practices/
# http://jvns.ca/blog/2017/03/26/bash-quirks/

# exit when a command fails
set -o errexit

# exit if any pipe commands fail
set -o pipefail

# exit when your script tries to use undeclared variables
#set -o nounset

# trace what gets executed
set -o xtrace

# Bash traps
# http://aplawrence.com/Basics/trapping_errors.html
# https://stelfox.net/blog/2013/11/fail-fast-in-bash-scripts/

SCRIPT_NAME="$0"
SCRIPT_PARAMS="$@"

error_handler() {
    echo
    echo " ########################################################## "
    echo
    echo " An error occurred in:"
    echo
    echo " - line number: ${1}"
    shift
    echo " - exit status: ${1}"
    shift
    echo " - command: ${@}"
    echo
    echo " The script will abort now. User input was: "
    echo
    echo " ${SCRIPT_NAME} ${SCRIPT_PARAMS}"
    echo
    echo " Please copy and paste this error and report it via Git Hub: "
    echo " https://github.com/cgat-developers/conda-deps/issues "
    echo " ########################################################## "
}

trap 'error_handler ${LINENO} $? ${BASH_COMMAND}' ERR INT TERM

# log installation information
log() {
    echo "# log | `hostname` | `date` | $1 "
}

# report error and exit
report_error() {
    echo
    echo $1
    echo
    echo "Aborting."
    echo
    exit 1
}

for f in `ls tests/*.py` ;
do
    env_f=`echo $f | sed 's/.py/.yml/g'`
    log " Comparing: python3 conda-deps.py $f"
    log " with: $env_f"
    diff <(python3 conda-deps.py $f) <(cat $env_f)
    if [[ "$?" -eq "0" ]] ; then
        log " Test succeeded for: $f!"
    else
        report_error " Test failed for: $f"
    fi
done

#!/bin/sh

function usage() {
    echo 'Commands:'
    echo ' - mypy - runs mypy checker in the main app'
    echo ' - tests - runs unit tests'
}

function run_mypy() {
    python -m mypy edgin_around.py edgin_around_server.py preview.py --show-error-codes $@
}

function run_mypy_tests() {
    python -m mypy test/test_*.py --show-error-codes $@
}

function run_tests() {
    python -m unittest $@
}

function run_pack_resources() {
    ZIPFILE=edgin_around_resources.zip
    rm -f $ZIPFILE
    zip -r $ZIPFILE res -x *.saml
}

if (( $# > 0 )); then
    command=$1
    shift

    case $command in
        'mypy')
            run_mypy $@
            ;;
        'tests')
            run_mypy && run_mypy_tests && run_tests $@
            ;;
        'pack-res')
            run_pack_resources
            ;;
        *)
            echo "Command \"$command\" unknown."
            echo
            usage
            ;;
    esac
else
    echo 'Please give a command.'
    echo
    usage
fi

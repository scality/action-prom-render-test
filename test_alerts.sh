#!/bin/bash

if [[ $# -lt 3 ]]; then
    echo "usage: $0 <test_file> <template_alert_file> <x-inputs>"
    exit 1
fi

TEST_FILE=${1}
TEMPLATE_ALERT=${2}
X_INPUTS=${3}

if [[ ! -f ${TEST_FILE} ]]; then
    echo "missing file: '${TEST_FILE}'"
    exit 1
fi

if [[ ! -f ${TEMPLATE_ALERT} ]]; then
    echo "missing file: '${TEMPLATE_ALERT}'"
    exit 1
fi

if [[ -z ${X_INPUTS} ]]; then
    echo "missing x-input values"
    exit 1
fi

# from now on any failling command should exit
set -vue

# render the alert
python alert_generator/alert_generator.py render --help

# check the resulting alert
python alert_generator/alert_generator.py check --help

# run alert tests using promtool
docker run --rm -t prom/prometheus:latest --version

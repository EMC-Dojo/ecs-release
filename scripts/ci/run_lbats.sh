#!/bin/bash

set -e -x -u

source $(pwd)/ecs-release/scripts/ci/utils.sh
check_param ECS_URL
check_param AWS_REGION
check_param AWS_ACCESS_KEY_ID
check_param AWS_SECRET_ACCESS_KEY
check_param BUCKET

sudo apt-get update
sudo apt-get install default-jdk
sudo apt-get install maven

pushd ecs-load-balancer-tests
    mvn clean test
popd

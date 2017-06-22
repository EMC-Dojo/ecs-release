#!/bin/bash

set -e -x -u

source $(pwd)/ecs-release/scripts/ci/utils.sh
check_param BOSH_TARGET
check_param BOSH_USERNAME
check_param BOSH_PASSWORD
check_param ENVIRONMENT_NAME
check_param DEPLOYMENTS_DIR
check_param INFRASTRUCTURE

if [ -z "$ENVIRONMENT_NAME" ]; then
  environment_path="${PWD}/${DEPLOYMENTS_DIR}"
else
  environment_path="${PWD}/${DEPLOYMENTS_DIR}/${ENVIRONMENT_NAME}"
fi

stubs_path="${environment_path}/stubs"
templates_path="${environment_path}/templates"
ecs_stubs="${PWD}/${DEPLOYMENTS_DIR}/ecs-release/stubs"

mkdir -p generated-manifest-ecs

pushd cf-release
  ./scripts/generate_deployment_manifest \
    ${INFRASTRUCTURE} \
    ${stubs_path}/cf/*.yml \
    > ../generated-manifest-ecs/cf-deployment.yml
popd

pushd ecs-release

cat > ${PWD}/ecsbroker-creds.yml << EOF
---
properties:
  ecsbroker:
    username: ${BOSH_USERNAME}
    password: ${BOSH_PASSWORD}
EOF

  ./scripts/generate_manifest.sh \
    ../generated-manifest-ecs/cf-deployment.yml \
    ${ecs_stubs}/director-uuid.yml \
    ${ecs_stubs}/iaas.yml \
    ${PWD}/ecsbroker-creds.yml

  mv ecsbroker-aws-manifest.yml ../generated-manifest-ecs/ecs-manifest.yml
popd

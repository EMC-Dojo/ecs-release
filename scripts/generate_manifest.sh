#!/bin/bash
#generate_manifest.sh

set -e

usage () {
    echo "Usage: generate_manifest.sh director-stub iaas-stub nfs-props-stub"
    echo " * default"
    exit 1
}

home="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. q&& pwd )"
templates=${home}/templates

if [[ "$1" == "aws" || -z $1 ]]
  then
    usage
fi

MANIFEST_NAME=ecsbroker-aws-manifest

spiff merge ${templates}/ecsbroker-aws-manifest.yml \
$1 \
$2 \
$3 \
> $PWD/$MANIFEST_NAME.yml

echo manifest written to $PWD/$MANIFEST_NAME.yml

# EMC Cloud Storage (BOSH release) [![slack.cloudfoundry.org](https://slack.cloudfoundry.org/badge.svg)](https://slack.cloudfoundry.org)

----
This repo is a [BOSH](https://github.com/cloudfoundry/bosh) release for
deploying software defined storage in the form of EMC Cloud Storage (ECS).
[ECS](https://www.emc.com/en-us/storage/ecs/index.htm) is a object storage platform that is designed for traditional and next-gen applications.

*Note:* Before deploying this release with BOSH, if you have not worked with BOSH take a look at [this](https://bit.ly/learn-bosh) tutorial!


## Deployment Requirements
This release expects the following items:
- git CLI
- BOSH CLI
- BOSH director version 257+ deployed
- BOSH director with the `enable_post_deploy: true` [flag](https://bosh.io/jobs/director?source=github.com/cloudfoundry/bosh#p=director.enable_post_deploy)
- BOSH director with a valid cloud-config that has a `disk_types` section with a valid `disk`
- BOSH **Ubuntu** stemcell

## Deployment Overview

ECS is deployed in a clustered configuration and currently this release only supports a 3 node cluster.

- clone this release and update submodules

```bash
git clone https://github.com/EMC-Dojo/ecs-release
cd ecs-release
git submodule update --init
```

- create the BOSH release and upload to the director

```bash
bosh -n create release
bosh -n upload release
```

- ensure a stemcell is uploaded and [upload](http://bosh.cloudfoundry.org/stemcells/) if needed 

```bash
bosh stemcells
````


## Deployment Examples: AWS and vSphere


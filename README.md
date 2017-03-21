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

- BOSH director with a valid cloud-config that has a `disk_types` section with a valid `disk`
- BOSH **Ubuntu** stemcell

## Deployment Overview

ECS is deployed in a clustered configuration and currently this release only supports a 3 node cluster.
This release has been tested with both vSphere and AWS.

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
```

## Deployment Manifest & Cloud-Config

A manifest template is available [here](templates/manifest.yml). You should not need to change anything, if all options are defined in your `BOSH` cloud-config. Example [vSphere](templates/vsphere-cloud-config.yml) and [AWS](templates/aws-cloud-config.yml) cloud-configs are provided as well.

- Once your manifest and cloud-config are setup, deploy!

```bash
bosh deploy
```

## Provisioning your ECS cluster (Optional)

After provisioning your ECS cluster with `BOSH` you will need to provision the cluster for use. If the allocated IP's are reachable by your browser you can provision ECS with the GUI. Navigate to the IP of the first node using `https` and login with `root`/`ChangeMe`.

If the IP is unreachable or if you prefer to automate this process, you are in luck! Included in this release is a `BOSH` errand that will provision the cluster for you. To run this, ensure you have not changed the username and password after deploying the cluster.

- Run the `BOSH` errand to provision the ECS cluster.

```bash
bosh run errand ecs_prov_errand
```

- Be patient this can take some time unless you provisioned exceedingly high performing VM's.


## Contact

Slack Channel:
Organization: http://cloudfoundry.slack.com
Channel: #persi

See you in the clouds!

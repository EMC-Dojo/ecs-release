#!/var/vcap/packages/python_2.7.13/bin/python

"""
This module
 - runs once before BOSH runs the ecs_container ctl start script
 - runs the docker daemon
 - loads the ecs image into docker
 - prepares the disk for use by ECS
"""

import sys
import os
import time

sys.path.insert(0, "/var/vcap/packages/ecs_community_edition/ecs-single-node/")
import step1_ecs_singlenode_install as CORE

# Config Time!
### Need to assign arg[1] to device here instead of passing it directly on line 88
### Need to assign vcap to user here instead of passing it directly on line 88

IMAGE = "/var/vcap/packages/ecs_community_edition/ecs-software-3.0.0.tar"
DOCKERVERSION = "1.12.6"

print "--- Parsed Configuration ---"
print "Docker Image: %s" % IMAGE
print "Docker Version: %s" % DOCKERVERSION

# Help us Helper Functions!

def install_docker_deps():
    """
    Add dependency to manage cgroups
    NEED TO FIX THIS IN THE FUTURE --> Find source and add as a dep to docker package
    """
    os.system("apt-get install cgroup-lite -y")

def startup_dockerd(device, user):
    """
    start docker daemon
    """
    docker_dir = prep_docker_disk(device)
    docker_log = "/var/vcap/sys/log/ecs_container/pre-start-docker.log"
    fhandle = open(docker_log, 'a')
    try:
        os.utime(docker_log, None)
    finally:
        fhandle.close()
        print "Docker Logs to %s!" % docker_log
    os.system("dockerd -D --graph %s --group %s >> %s 2>&1 &"
              % (docker_dir, user, docker_log))
    time.sleep(1)
    count = 0
    while not 'libcontainerd: containerd connection state change: READY' in open(docker_log).read():
        if count >= 30:
            print "Docker did not start after 30 seconds"
            sys.exit(1)

        else:
            time.sleep(1)
            count += 1

def load_docker_image():
    """
    Load docker image from disk
    """
    if not os.path.exists(IMAGE):
        print "The specified docker image file %s does not exist." % IMAGE
        sys.exit(1)
    CORE.docker_load_image(IMAGE)
    os.system("docker images")

def prep_docker_disk(device):
    """
    BOSH only provisions the disk on the IAAS, we need to:
    - Format the disk
    - Make a directory to mount disk to
    - Mount disk to directory
    """
    docker_dir = "/var/vcap/store/docker"
    os.system("mkfs.ext4 %s" % device)
    os.system("mkdir -p %s" % docker_dir)
    os.system("mount -t ext4 %s %s" % (device, docker_dir))
    return docker_dir

#def prep_ecs_disk(device):

install_docker_deps()
startup_dockerd(sys.argv[1], "vcap")
load_docker_image()

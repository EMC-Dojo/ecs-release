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
import subprocess

sys.path.insert(0, "/var/vcap/packages/ecs_community_edition/ecs-multi-node/")
import step1_ecs_multinode_install as CORE

# Config Time!
### Need to assign arg[1] to device here instead of passing it directly on line 88
### Need to assign vcap to user here instead of passing it directly on line 88

IMAGE = "/var/vcap/packages/ecs_community_edition/ecs-software-3.0.0.tar"
DOCKERVERSION = "1.12.6"
NETADAPTER = "eth0"
DOCKERDISK = sys.argv[1]
USER = "vcap"
IPS = [sys.argv[3], sys.argv[4], sys.argv[5]]
HOSTNAMES = ["ecs0", "ecs1", "ecs2"]
INSTANCEID = sys.argv[6]

find_disk_name = "ls -l %s" % sys.argv[2]
find_disk_name += r" | awk '{print $NF}' | sed -e 's/\/.*\///g'"

ecs_disk = subprocess.check_output(find_disk_name, shell=True)
ecs_disk = ecs_disk.strip()

print "--- Parsed Configuration ---"
print "Docker Image: %s" % IMAGE
print "Docker Version: %s" % DOCKERVERSION
print "Docker Disk: %s" % DOCKERDISK
print "Running Docker As: %s" % USER
print "Network Adapter: %s" % NETADAPTER
print "ECS Disk: %s" % ecs_disk
print "Cluster IPs: %s" % IPS
print "Cluster Hostnames: %s" % HOSTNAMES
print "Running Instance ID: %s" % INSTANCEID

# Help us Helper Functions!

def install_docker_deps():
    """
    Add dependency to manage cgroups
    NEED TO FIX THIS IN THE FUTURE --> Find source and add as a dep to docker package
    """
    os.system("apt-get install cgroup-lite -y")

def startup_dockerd(docker_device, user):
    """
    start docker daemon
    """
    docker_dir = prep_docker_disk(docker_device)
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

def load_docker_image(docker_image):
    """
    Load docker image from disk
    """
    if not os.path.exists(docker_image):
        print "The specified docker image file %s does not exist." % docker_image
        sys.exit(1)
    CORE.docker_load_image(docker_image)
    os.system("docker images")

def prep_docker_disk(docker_device):
    """
    BOSH only provisions the disk on the IAAS, we need to:
    - Format the disk
    - Make a directory to mount disk to
    - Mount disk to directory
    """
    docker_dir = "/var/vcap/store/docker"
    os.system("mkfs.ext4 %s" % docker_device)
    os.system("mkdir -p %s" % docker_dir)
    os.system("mount -t ext4 %s %s" % (docker_device, docker_dir))
    return docker_dir

def setup_ecs_networking(adapter, ips, hostnames, instanceid):
    """
    ECS Requires the /etc/hosts and /etc/hostname
    to contain all the nodes needed for the ECS cluster.
    For this release (single node), we only need our ip/hostname
    """
    print "Preparing Networking for ECS"
    os.system("hostname ecs%s" % (instanceid))
    CORE.network_file_func(adapter)
    CORE.seeds_file_func(ips)
    CORE.hosts_file_func(ips, hostnames)

def prep_ecs_disk(ecs_device):
    """
    ECS Requires the disk being provided to it be formated correctly,
    and then "Chunked" into bin folders.
    We call into ECS core Scripts to help us with this.

    ** We have to move the additional_prep script since the core
    libraries expect it to be in our current folder. **
    """
    print "Preparing Disks for ECS"
    ecs_disks = [ecs_device]
    CORE.prepare_data_disk_func(ecs_disks)
    os.system("cp /var/vcap/packages/ecs_community_edition/ecs-multi-node/additional_prep.sh .")
    os.system("ln -s /bin/grep /usr/bin/grep")
    CORE.run_additional_prep_file_func(ecs_disks)
    
install_docker_deps()
startup_dockerd(DOCKERDISK, USER)
load_docker_image(IMAGE)
setup_ecs_networking(NETADAPTER, IPS, HOSTNAMES, INSTANCEID)
prep_ecs_disk(ecs_disk)
CORE.directory_files_conf_func()
print "MADE IT TO THE END!!!"



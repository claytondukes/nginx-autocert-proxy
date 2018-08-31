#!/usr/bin/python

import sys
import os
import re
import time
import imp
import docker
import logging
import subprocess
import errno
from jinja2 import Environment, FileSystemLoader

fmt = "%(asctime)s [%(process)d] %(name)s %(levelname)s %(message)s"
logging.basicConfig(format=fmt)
logger = logging.getLogger('updater')
logger.setLevel(logging.DEBUG)

docker_client = docker.from_env()

_nginx_container = None
known_hosts = {}

def nginx_container():
    global _nginx_container

    if _nginx_container is None:
        logger.info("Finding my container...")
        # First find mine container to get docker-compose prefix
        with open('/proc/self/cgroup') as f:
            for line in f:
                m = re.search(r'\bcpu(?:acct)?:/docker/(.*)', line)
                if m:
                    my_container_id = m.group(1)
                    break
            else:
                raise RuntimeError(
                    "No container info found in /proc/self/cgroup, "
                    "make sure you run in docker container"
                )
        my_cnt = docker_client.containers.get(my_container_id)
        my_container_name = my_cnt.name
        logger.info("My container name: {}".format(my_container_name))
        m = re.match(r'(\w+)_updater_\d+', my_container_name)
        if not m:
            raise RuntimeError("Unrecognized container name: {}"
                    .format(my_container_name))
        prefix = m.group(1)
        _nginx_container = docker_client.containers.get(prefix + '_nginx_1')

    return _nginx_container

def signal_nginx():
    nginx = nginx_container()
    nginx.update()
    logger.info("nginx status: {}".format(nginx.status))
    if nginx.status == 'running':
        logger.info("Sending sighup to nginx ({})".format(nginx.name))
        nginx.kill('SIGHUP')
    else:
        logger.info("Starting nginx container ({})".format(nginx.name))
        nginx.start()

def update_nginx(params):
    env = Environment(loader=FileSystemLoader('/usr/src/app'))
    tpl = env.get_template('nginx.conf.tpl')
    tmp_path = '/etc/nginx/nginx.conf.tmp'
    with open(tmp_path, 'w') as f:
        tpl.stream(params).dump(f)
    os.rename(tmp_path, '/etc/nginx/nginx.conf')
    signal_nginx()

def has_cert(host):
    f = '/etc/letsencrypt/live/{}/fullchain.pem'.format(host)
    return os.path.exists(f)

def run_certbot(args):

    dev_null = open('/dev/null', 'r')

    cmd = ['certbot'] + args
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, stdin=dev_null, shell=False)
    logger.debug("Running {}".format(cmd))
    output = ''
    while proc.poll() is None:
        line = proc.stdout.readline()
        if line != '':
            line = line.rstrip()
            logger.debug("> {}".format(line))
            output += line + "\n"
        else:
            time.sleep(0.1)

    for line in proc.stdout:
        line = line.rstrip()
        logger.debug("> {}".format(line))
        output += line + "\n"

    if proc.returncode == 0:
        return True
    else:
        logger.error("command {} failed with status {}".format(
            cmd, proc.returncode))
        logger.error("output:\n{}".format(output))
        return False


def retrieve_cert(host):
    logger.info("Retrieving cert for host {}".format(host))
    webroot = '/data/wellknown/' + host

    try:
        os.mkdir(webroot)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise

    return run_certbot(['certonly',
        '--webroot', '-w', webroot,
        '-n', '--agree-tos',
        '-m', 'certbot@cduk.es',
        '-d', host
    ])

last_hosts_update = 0
last_renew = 0
HOSTS_FILE = "/etc/nginx/hosts.py"

def update():
    global last_hosts_update, last_renew
    st = os.stat(HOSTS_FILE)
    if st.st_mtime > last_hosts_update:
        hosts = imp.load_source('hosts', '/etc/nginx/hosts.py')
        for host, conf in hosts.HOSTS.iteritems():
            conf['cert_ready'] = has_cert(host)
            if not conf['cert_ready'] and retrieve_cert(host):
                conf['cert_ready'] = True
        update_nginx({'hosts': hosts.HOSTS, 'local_hosts': hosts.LOCAL_HOSTS})

        last_hosts_update = st.st_mtime

    # renew daily
    if time.time() - last_renew > 24*60*60:
        if run_certbot(['renew']):
            signal_nginx()
        last_renew = time.time()


try:
    while True:
        time.sleep(1)
        update()
except KeyboardInterrupt:
    print "Interrupted"
    exit(0)
except Exception as e:
    print "Error: {}".format(e)
    exit(1)

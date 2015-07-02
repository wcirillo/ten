""" fabric init file for controlling our deployments"""
#from __future__ import with_statement
from fabric.api import local, run, env
#from fabric.contrib.console import confirm

env.hosts = ['hsweb01:22', 'hsweb04:22', 'lb:22', 'controller:22']

HG_SERVER = "https://hg.strausdigital.com"
PROJ_HOME = "/home/django"

OS_PACKAGES_ALL = "install build-essential subversion ssl-cert  libpq-dev vim \
    python-dev python-setuptools postfix unzip git-core sysstat  linux-headers-generic\
    nfs-common ntp postgresql-client python2.6 python2.6-dev libxml2-dev python-memcache"
OS_PACKAGES_DBSERVER = "postgresql-8.4 proj-data proj-bin    postgresql-8.4-postgis postgis gdal-bin \
    postgresql-server-dev-8.4"
OS_PACKAGES_RABBIT = "erlang-os-mon erlang-snmp erlang-ssl erlang-inets erlang-public-key"

OS_PACKAGES_NGINX = "libapache2-mod-rpaf nginx libapache2-mod-wsgi libmemcache-dev epython-egenix-mxdatetime"
OS_PACKAGES_APACHE = "libapache2-mod-rpaf libapache2-mod-wsgi libmemcache-dev"

def hello(name="jerm"):
    """ dimple hello world demo """
    print("hello %s!" % name)

def prepare_deploy():
    """ pre-deployment preparations.. currently not used"""
    local("./manage.py test ")
    local("hg commit  && hg fetch && hg push")


def deploy():
    """ deploys code cahnged to listed servers and does a reload on each"""
    #local('ls')
    #run("source ~/.tenrc && cd $VIRT_HOME && source bin/activate && hg fetch && tenreloaod && tenhome")
    run("bash -c 'source ~/.tenrc &&  hg fetch && tenreload '") #cd /export/ten/10coupons-repo && hg fetch && celeryrestart
    #run("source .tenrc && tenreload")
    #run("tenreload")

def tenreload():
    """ runs tenreload on each listed server """
    run("bash -c 'source ~/.tenrc && tenreload '")

def tenrestart():
    """ runs tenrestart on each listed server """
    run("bash -c 'source ~/.tenrc && tenrestart '")


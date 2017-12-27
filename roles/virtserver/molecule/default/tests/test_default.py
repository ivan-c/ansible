import os
import requests
from testinfra.utils import ansible_runner

testinfra_hosts = ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']
).get_hosts('all')


def test_libvirtd_is_installed(host):
    libvirt = host.package("libvirt-daemon-system")
    assert libvirt.is_installed


def test_libvirt_running_and_enabled(host):
    libvirtd = host.service("libvirtd")
    assert libvirtd.is_enabled
    assert libvirtd.is_running


def test_apt_cacher_ng_running_and_enabled(host):
    apt_cacher_ng = host.service("apt-cacher-ng")
    assert apt_cacher_ng.is_enabled
    assert apt_cacher_ng.is_running


def test_apt_cacher_ng_response(host):
    response = requests.get("http://localhost:3142")
    assert 'virtual HTTP repository' in response.content

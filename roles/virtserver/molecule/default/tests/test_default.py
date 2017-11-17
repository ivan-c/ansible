import os
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

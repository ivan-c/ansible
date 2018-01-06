import os
import stat
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


def test_apt_cacher_ng_caching_provisioning(host):
    """Test whether VM guest used apt-cacher-ng on VM host during provisioning"""
    assert host.file("/var/log/apt-cacher-ng/apt-cacher.log").contains("base-installer")


def test_kvm_device(host):
    kvm_device_path = "/dev/kvm"
    assert stat.S_ISCHR(os.stat(kvm_device_path).st_mode)

    kvm_device = host.file(kvm_device_path)
    assert kvm_device.user == "root"
    assert kvm_device.group == "kvm"
    assert kvm_device.mode == 0o660

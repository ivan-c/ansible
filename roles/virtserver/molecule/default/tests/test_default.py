import os
import stat
from testinfra.utils import ansible_runner
import pytest

testinfra_hosts = ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']
).get_hosts('all')


def test_apt_cacher_ng_running_and_enabled(host):
    """Test apt-cacher-ng running on VM host"""
    apt_cacher_ng = host.service("apt-cacher-ng")
    assert apt_cacher_ng.is_enabled
    assert apt_cacher_ng.is_running


def test_apt_cacher_ng_caching_provisioning(host):
    """Test whether VM guest used apt-cacher-ng on VM host during provisioning"""
    apt_cacher_log = "/var/log/apt-cacher-ng/apt-cacher.log"

    assert host.file(apt_cacher_log).exists
    assert host.file(apt_cacher_log).contains("base-installer")


def test_libvirtd_is_installed(host):
    libvirt = host.package("libvirt-daemon-system")
    assert libvirt.is_installed


def test_kvm_device(host):
    """Test that KVM device has correct ownership and permissions"""
    kvm_device_path = "/dev/kvm"
    assert stat.S_ISCHR(os.stat(kvm_device_path).st_mode)

    kvm_device = host.file(kvm_device_path)
    assert kvm_device.user == "root"
    assert kvm_device.group == "kvm"
    assert kvm_device.mode == 0o660


def test_libvirt_running_and_enabled(host):
    libvirtd = host.service("libvirtd")
    assert libvirtd.is_enabled
    assert libvirtd.is_running


@pytest.mark.xfail
def test_vm_started(host):
    """Test that guest VM shutdown and restarted gracefully, after provisioning"""
    vars = host.ansible.get_variables()
    domain_log = "/var/log/libvirt/qemu/{inventory_hostname}.log".format(**vars)

    assert host.check_output(
        "virsh domstate --reason {inventory_hostname}".format(**vars)
    ) == 'running (booted)'

    assert host.file(domain_log).is_file
    assert host.file(domain_log).contains("shutting down, reason=shutdown")


@pytest.mark.xfail
@pytest.mark.parametrize("log_filename", [
    "/var/log/libvirt/libvirtd.log",
    "/var/log/libvirt/virtlogd.log",
    "/var/log/libvirt/qemu/{inventory_hostname}.log",
])
def test_libvirt_logs_no_errors(host, log_filename):
    """Test that there are no errors in libvirt logs"""
    vars = host.ansible.get_variables()
    log_filename = log_filename.format(**vars)

    assert host.file(log_filename).is_file
    try:
        assert not host.file(log_filename).contains("error")
    except:
        # Dump log on failure
        print "\n", host.file(log_filename).content
        raise

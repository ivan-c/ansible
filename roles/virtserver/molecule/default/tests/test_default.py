import os
import stat
from testinfra.utils import ansible_runner

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


def test_vm_started(host):
    """Test that guest VM shutdown and restarted gracefully, after provisioning"""
    vars = host.ansible.get_variables()
    domain_log = "/var/log/libvirt/qemu/{inventory_hostname}.log".format(**vars)

    assert host.check_output(
        "virsh domstate --reason {inventory_hostname}".format(**vars)
    ) == 'running (booted)'

    assert host.file(domain_log).is_file
    try:
        assert host.file(domain_log).contains("shutting down, reason=shutdown")
    # Dump log on failure
    except:
        print host.file(domain_log).content
        raise

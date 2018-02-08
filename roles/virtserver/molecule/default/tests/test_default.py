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


def test_libvirt_dmidecode(host):
    """Test libvirt is able to find dmidecode binary"""
    dmidecode = host.package("dmidecode")
    assert dmidecode.is_installed

    libvirtd_log = "/var/log/libvirt/libvirtd.log"
    assert host.file(libvirtd_log).is_file
    assert not host.file(libvirtd_log).contains("Failed to find path for dmidecode binary")


def test_dbus(host):
    """Test dbus service and availability for libvirt"""

    dbus = host.service("dbus")
    assert dbus.is_enabled
    assert dbus.is_running

    dbus_socket = '/var/run/dbus/system_bus_socket'
    assert host.file(dbus_socket).exists
    assert host.file(dbus_socket).is_socket


@pytest.mark.parametrize("method_name", [
    # https://github.com/libvirt/libvirt/blob/v3.0.0/src/util/virsystemd.c#L544
    "ListActivatableNames",
    # https://github.com/libvirt/libvirt/blob/v3.0.0/src/util/virsystemd.c#L548
    "ListNames",
])
def test_dbus_logind(host, method_name):
    """Test logind enabled and running via Dbus"""

    command = " ".join((
        "dbus-send",
        "--system",
        "--print-reply",
        "--dest=org.freedesktop.DBus",
        "/org/freedesktop/DBus",
        "'org.freedesktop.DBus.{}'".format(method_name),
    ))
    assert 'org.freedesktop.login1' in host.check_output(command)


def test_libvirt_dbus(host):
    """Test that libvirt successfully probed suspend types"""

    libvirtd_log = "/var/log/libvirt/libvirtd.log"
    assert host.file(libvirtd_log).is_file
    assert not host.file(libvirtd_log).contains("Cannot probe for supported suspend types")

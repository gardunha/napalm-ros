import base64
import socket
from pathlib import Path
from typing import List, Union

import paramiko


class SshClient:

    def __init__(
            self,
            host: str,
            username: str,
            host_key: str = None,
            private_key: Path = None,
            password: str = None,
            timeout: int = 10,
    ):
        self.client = None
        # Use an open count to this can be used in nested contexts
        # (handy when passing an already open client into functions)
        self._open_count = 0

        self.host = host
        self.username = username
        self.host_key = host_key
        self.private_key = private_key
        self.password = password
        self.timeout = timeout

    def __enter__(self):
        if not self.host_key:
            from napalm_ros.models import SshHostKey
            self.host_key = SshHostKey.objects.for_hostname(self.host).host_key
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        self._open_count += 1

        host_key_type, host_key_data = self.host_key.split(" ", 1)
        if host_key_type == "ssh-rsa":
            host_key = paramiko.RSAKey(data=base64.b64decode(host_key_data))  # noqa
        else:
            host_key = paramiko.ECDSAKey(data=base64.b64decode(host_key_data))  # noqa

        kwargs = {}
        if self.private_key:
            kwargs["pkey"] = paramiko.RSAKey.from_private_key_file(str(self.private_key))
        if self.password:
            kwargs["password"] = self.password

        self.client = paramiko.SSHClient()
        self.client.get_host_keys().add(self.host, host_key_type, host_key)

        self.client.connect(self.host, username=self.username, timeout=self.timeout, allow_agent=False, look_for_keys=False, **kwargs)

    def close(self):
        self._open_count -= 1
        if not self._open_count:
            self.client.close()

    def _assert_open(self):
        if not self._open_count:
            raise SshClientNotOpen("SSH client needs to be opened first. Call client.open()")

    def exec(self, command, **kwargs):
        self._assert_open()
        stdin, stdout, stderr = self.client.exec_command(command, **kwargs)
        return stdin, stdout, stderr, stdout.channel.recv_exit_status()

    def run(self, command, raise_exceptions=True) -> List[str]:
        """Like exec(), but just returns stdout for quick and easy use"""
        self._assert_open()
        stdin, stdout, stderr, exit_code = self.exec(command)
        if exit_code == 0 or not raise_exceptions:
            return [s.strip() for s in stdout.readlines()]
        else:
            error = (stderr.read() or stdout.read()).decode("utf8")
            raise SshCommandException(f"Error executing: {command}\nError: {error}")

    def write_file(self, path: Union[Path, str], data: bytes):
        """Write the given data to the specified path on the server"""
        self._assert_open()
        sftp_client: paramiko.SFTPClient = self.client.open_sftp()
        try:
            with sftp_client.open(str(path), "w") as f:
                f.write(data)
        finally:
            sftp_client.close()

    def read_file(self, path: str) -> bytes:
        """Read the data from the given path on the server"""
        self._assert_open()
        sftp_client: paramiko.SFTPClient = self.client.open_sftp()
        try:
            with sftp_client.open(path, "r") as f:
                return f.read()
        finally:
            sftp_client.close()


def get_fingerprint(host, port=22):
    ssh_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssh_socket.settimeout(5)
    ssh_socket.connect((host, port))

    with ssh_socket:
        transport = paramiko.Transport(ssh_socket)  # noqa
        # Out SSH client only supports ECDSA & RSA host keys, so only use those
        transport._preferred_keys = [
            "ecdsa-sha2-nistp256",
            "ecdsa-sha2-nistp384",
            "ecdsa-sha2-nistp521",
            "ssh-rsa",
        ]

        try:
            transport.start_client()
            ssh_key = transport.get_remote_server_key()
        finally:
            transport.close()

    printable_type = ssh_key.get_name()
    printable_key = base64.encodebytes(ssh_key.asbytes()).strip()
    return f"{printable_type} {printable_key.decode('utf8')}"


class SshClientAlreadyOpen(Exception):
    pass


class SshClientNotOpen(Exception):
    pass


class SshCommandException(Exception):
    pass

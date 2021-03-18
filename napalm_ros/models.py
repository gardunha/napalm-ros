from django.db import models

from napalm_ros.ssh_client import get_fingerprint


class SshHostKeyManager(models.Manager):

    def for_hostname(self, hostname: str):
        """Get a host key obj for the given hostname. Fetching the host key if necessary"""
        try:
            host_key = SshHostKey.objects.get(hostname=hostname)
        except SshHostKey.DoesNotExist:
            host_key = SshHostKey(hostname=hostname)

        if not host_key.host_key:
            host_key.fetch_host_key()

        return host_key


class SshHostKey(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    hostname = models.CharField(max_length=200, unique=True)
    host_key = models.TextField()

    objects = SshHostKeyManager()

    def __str__(self):
        return f"Key for {self.hostname}"

    def fetch_host_key(self, commit=True):
        self.host_key = get_fingerprint(self.hostname)
        if commit:
            self.save()

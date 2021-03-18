from django.contrib import admin
from .models import SshHostKey


@admin.register(SshHostKey)
class SshHostKeyAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'created_at')

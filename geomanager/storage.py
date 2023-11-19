import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):
    def exists(self, name):
        exists = os.path.lexists(self.path(name))
        if exists:
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return exists

import mimetypes
import posixpath

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    """Stores media files in a Supabase Storage bucket.

    Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY. The bucket
    (SUPABASE_BUCKET) must exist and be public for url() to work.
    """

    def __init__(self, bucket_name=None):
        self.bucket_name = bucket_name or settings.SUPABASE_BUCKET
        self._client = None

    @property
    def bucket(self):
        if self._client is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
                raise ImproperlyConfigured(
                    'SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set '
                    'to use SupabaseStorage.'
                )
            from supabase import create_client

            self._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        return self._client.storage.from_(self.bucket_name)

    def _save(self, name, content):
        content.seek(0)
        content_type = (
            getattr(content, 'content_type', None)
            or mimetypes.guess_type(name)[0]
            or 'application/octet-stream'
        )
        self.bucket.upload(
            name,
            content.read(),
            file_options={'content-type': content_type, 'upsert': 'true'},
        )
        return name

    def _open(self, name, mode='rb'):
        return ContentFile(self.bucket.download(name), name=name)

    def exists(self, name):
        folder, filename = posixpath.split(name)
        entries = self.bucket.list(folder, {'search': filename})
        return any(entry['name'] == filename for entry in entries)

    def delete(self, name):
        self.bucket.remove([name])

    def size(self, name):
        folder, filename = posixpath.split(name)
        for entry in self.bucket.list(folder, {'search': filename}):
            if entry['name'] == filename:
                return (entry.get('metadata') or {}).get('size', 0)
        return 0

    def url(self, name):
        return self.bucket.get_public_url(name)

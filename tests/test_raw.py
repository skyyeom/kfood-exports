import requests

from pipeline.raw import SupabaseRawStore


class StorageApi:
    """Stands in for Supabase Storage: records the upload and accepts it."""

    def __init__(self):
        self.headers, self.uploads = {}, []

    def post(self, url, data=None, timeout=None):
        self.uploads.append((url, dict(self.headers), data))
        r = requests.Response()
        r.status_code = 200
        return r


def test_uploads_raw_archive_to_the_private_bucket_with_service_credentials():
    store = SupabaseRawStore("https://proj.supabase.co/", "service-key")
    api = StorageApi()
    api.headers.update(store.session.headers)
    store.session = api

    path = store.put("raw/fx/run-1.zip", b"zip-bytes")

    [(url, headers, body)] = api.uploads
    assert url == "https://proj.supabase.co/storage/v1/object/raw/fx/run-1.zip"
    assert headers["apikey"] == "service-key" and headers["Authorization"] == "Bearer service-key"
    assert (body, path) == (b"zip-bytes", "storage://raw/fx/run-1.zip")

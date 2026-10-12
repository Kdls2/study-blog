# gunicorn.conf.py
# Suppress Server information disclosure
import gunicorn

gunicorn.SERVER = ""
gunicorn.SERVER_SOFTWARE = ""

try:
    from gunicorn.http import wsgi

    class HardenedResponse(wsgi.Response):
        def default_headers(self, *args, **kwargs):
            headers = super().default_headers(*args, **kwargs)
            return [h for h in headers if not h.lower().startswith("server:")]

    wsgi.Response = HardenedResponse
except Exception:
    pass

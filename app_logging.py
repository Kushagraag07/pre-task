# app_logging.py
import logging
import os
import sys
from pythonjsonlogger import jsonlogger

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# JSON formatter - include fields that python-json-logger will pick from record and extra
json_fmt = '%(asctime)s %(levelname)s %(name)s %(message)s'
formatter = jsonlogger.JsonFormatter(json_fmt)

# Stream handler to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

# Root logger
root = logging.getLogger()
root.setLevel(LOG_LEVEL)
# Replace handlers so logs from libraries go through JSON formatter
root.handlers = [handler]

# Configure gunicorn loggers to also use JSON formatter (access/error)
for name in ("gunicorn.error", "gunicorn.access"):
    gl = logging.getLogger(name)
    gl.setLevel(LOG_LEVEL)
    # remove existing handlers to avoid duplicate text handlers
    gl.handlers = []
    gl.propagate = False
    gl.addHandler(handler)

# reduce noisy libraries
logging.getLogger("urllib3").setLevel("WARNING")

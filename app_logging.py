# app_logging.py
import logging, os, sys
from pythonjsonlogger import jsonlogger

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(levelname)s %(name)s %(message)s'
)
handler.setFormatter(formatter)

root = logging.getLogger()
root.setLevel(LOG_LEVEL)
# Replace existing handlers so all libraries log via this JSON formatter
root.handlers = [handler]

# reduce noisy libs
logging.getLogger("urllib3").setLevel("WARNING")

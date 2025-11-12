import logging, os, sys, time
from pythonjsonlogger import jsonlogger


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


handler = logging.StreamHandler(sys.stdout)
formatter = jsonlogger.JsonFormatter(
"%(asctime)s %(levelname)s %(name)s %(message)s %(pathname)s %(lineno)d %(funcName)s %(process)d %(thread)d"
)
handler.setFormatter(formatter)


root = logging.getLogger()
root.setLevel(LOG_LEVEL)
root.handlers = [handler]
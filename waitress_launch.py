from waitress import serve
import scrabble
import sys
import logging
import datetime
from logging.handlers import RotatingFileHandler

# check log_file name validity
log_file_name = '/var/log/scrabble/' + datetime.datetime.today().strftime('%Y%m%d_%H%M%S_') + 'waitress.log'
try:
    with open(log_file_name, 'x') as tempfile:  # OSError if file exists or is invalid
        pass
except OSError as e:
    print("Invalid --log_file name: %s - %s" % (log_file_name, e))
    sys.exit(-1)

logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

handler_file = RotatingFileHandler(log_file_name, maxBytes=100000000, backupCount=5)
handler_file.setLevel(logging.DEBUG)
logger.addHandler(handler_file)

serve(scrabble.__hug_wsgi__, listen='127.0.0.1:8000', threads=128)

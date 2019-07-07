from waitress import serve
import scrabble
import hug
import logging
logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

serve(scrabble.__hug_wsgi__, listen='127.0.0.1:8000', threads=128)

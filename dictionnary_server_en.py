import argparse
import ipaddress
import logging
from logging.handlers import RotatingFileHandler
import sys
import traceback
import datetime
import pickle

import zmq

from dictionary import Trie


def listen_dict_server_queries(host_ip_address: str, tcp_port: str):
    """
    Listen to dictionary method request as json, execute them and return results back as json
    """
    # Validate IPV4 address and TCP port range   TODO move checks at argparse level
    try:
        ipaddress.ip_address(host_ip_address)
    except ValueError:
        logger.error("%s is not valid IP address", host_ip_address)
        raise Exception("%s is not valid IP address", host_ip_address)
    # valid TCP port value
    if not isinstance(tcp_port, str):
        logger.error("%s is not a character string", str(tcp_port))
        raise Exception("%s is not a character string", str(tcp_port))
    elif (int(tcp_port) > 49152) or (int(tcp_port) < 1000):
        # logger.error("%s port value must be in 1000 to 49152 range", str(port))
        raise Exception("%s port value must be in 1000 to 49152 range", str(tcp_port))

    trie = Trie()
    logger.info("loading dictionary....")
    # trie.load_from_json_word_list("word_list_15.json")  # TODO make dict file parameter
    trie.load_from_json_word_list("dictionnary-english-eliot21.json")  # TODO make dict file parameter
    logger.info("dictionary loaded")

    """ 
    start zmq listener as a ROUTER so that multiple zmq.REQ can be accepted in non blocking mode
    zmq.ROUTER accepts several open connections  simultaneously - each one is identified by an address that is
    provided in the first frame of the REQ message (for a simple REQ-REP there's no such address)
    
    in a further version this task can be made multiprocessed (4 processes if on Raspeberry) each process with its
    own copy of the dictionnary. And a loop on recv can dispatch the load to the 4 processes. ALgorythm should be that 
    new connection are taken only when one process is idle (LRU style)
     
    Due to GIL effect multi Threads is of no use since the dictionnary lookup task is only memory and cpu bound with no 
    external dependency - so it is about parallellism not about concurrency
    """

    zmq_context = zmq.Context()
    zmq_socket_listener = zmq_context.socket(zmq.ROUTER)
    zmq_socket_listener.bind("tcp://" + host_ip_address + ":" + tcp_port)
    logger.info("dictionary server listening on %s..." % str(tcp_port))

    while True:

        # get request
        address, empty, message = zmq_socket_listener.recv_multipart()
        method_str, kwargs = pickle.loads(message)
        logger.debug("query received : %s" % (method_str + "|" + str(kwargs)))
        if method_str not in ["possible_words_for_mask_with_rack",
                              "this_is_a_valid_word",
                              "possible_word_set_from_string"]:
            ret = (False,
                   "method %s is not implemented" % str(method_str))
            logger.warning("method %s is not implemented" % str(method_str))
        else:
            success = True
            try:
                res = getattr(trie, method_str)(**kwargs)
            except Exception:
                success = False
                e = traceback.format_exc()
                logger.error(e)

            ret = (success, res) if success else (success, e)

        # respond to request
        logger.debug("response sent : %s" % (method_str + "|" + str(ret)))
        zmq_socket_listener.send_multipart([address, empty, pickle.dumps(ret)])


if __name__ == "__main__":
    # parse arguments - tcp_port - console logging level - debug logging to file
    parser = argparse.ArgumentParser(description='Launch dictionary server process')

    parser.add_argument('--tcp_port', default=5556, type=int, choices=range(1001, 49152),
                        help='tcp port listening on loopback address')
    parser.add_argument('--console_log_level', default="Info", type=str.lower,
                        choices=["debug", "info", "warning", "error", "critical"],
                        help='console messages logging level: None, Info, Debug (default: info)')
    parser.add_argument('--log_file', default='dictionary-server-en.log',
                        help='logging file (default: dictionary-server.log)')
    parser.add_argument('--log_file_level', default='Info', type=str.lower,
                        choices=["debug", "info", "warning", "error", "critical"],
                        help='logging file level (default: info)')

    args = parser.parse_args()

    LOG_LEVEL_DICT = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }

    # check log_file name validity
    log_file_name = '/var/log/scrabble/' + datetime.datetime.today().strftime('%Y%m%d_%H%M%S_') + args.log_file
    try:
        with open(log_file_name, 'x') as tempfile:  # OSError if file exists or is invalid
            pass
    except OSError as e:
        print("Invalid --log_file name: %s - %s" % (args.log_file, e))
        sys.exit(-1)

    # Set logging
    # 2 handlers : one on console and one on file with logging level according to argument passed to program
    formatter = logging.Formatter("%(asctime)s :: %(funcName)s :: %(levelname)s :: %(message)s")

    handler_console = logging.StreamHandler()
    handler_console.setFormatter(formatter)
    handler_console.setLevel(LOG_LEVEL_DICT[args.console_log_level])

    logger = logging.getLogger("dictionary")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler_console)

    handler_file = RotatingFileHandler(log_file_name, maxBytes=100000000, backupCount=5)
    # handler_file = logging.FileHandler(args.log_file, mode="a", encoding="utf-8")  # TODO log file name & rotation
    handler_file.setFormatter(formatter)
    handler_file.setLevel(LOG_LEVEL_DICT[args.log_file_level])
    logger.addHandler(handler_file)

    logger.info("info: launching server...")
    logger.debug("debug: launching server...")
    listen_dict_server_queries('127.0.0.1', str(args.tcp_port))
    print("this should not print")

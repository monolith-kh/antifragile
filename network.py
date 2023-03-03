# -*- coding: utf-8 -*-

import logging
import threading
import time
from socket import socket

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s\t%(levelname)s:\t%(message)s')
logger = logging.getLogger('Network')

DEFAULT_BUFFER_SIZE = 1024

class Network(object):
    def __init__(self):
        self.buffer_size = DEFAULT_BUFFER_SIZE
    
    def init(self, sock: socket, receive_function):
        self._sock = sock
        self._receive_function = receive_function
        logger.debug(self._sock)
        logger.debug(self._receive_function)

    def start(self):
        def on_start_event():
            while True:
                logger.debug('prepare loop')
                logger.debug(self._sock)
                buf = self._receive_function()
                if buf:
                    logger.debug(buf)
                    logger.debug('post loop')
                time.sleep(2)

        threading.Thread(target=on_start_event, name='on_start_event').start()

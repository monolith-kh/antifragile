#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import signal
import logging
import time

from fbs.pilot import Request, Response, Command, Player, Players, Sender
from packet import request_packet_builder, response_packet_builder

DEFAULT_BUFFER_SIZE = 1024

def test(addr, logger=logging.getLogger('Test')):
    host, port = addr

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        life = True
        def shutdown_handler(sig, frame):
            global life
            life = False
            sock.setblocking(False)
            print("")
    
        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)
    
        logger.debug("before request")
    
        sock.connect(addr)
    
        logger.debug("before loop")
    
        while life:
            try:
                logger.debug("loop")
                buf = sock.recv(DEFAULT_BUFFER_SIZE)
                if buf:
                    logger.info(buf)
                    req = Request.Request.GetRootAsRequest(buf, 0)
                    logger.info(req.Timestamp())
                    logger.info(req.Command())
                    logger.info(req.Sender())
                    logger.info(req.Data())
                    logger.info("----------")
                    if req.Command() == Command.Command.welcome:
                        res = response_packet_builder(Command.Command.welcome) 
                        logger.debug(res)
                    elif req.Command() == Command.Command.player_status:
                        pass
                    else:
                        pass
                    sock.sendall(res)
                else:
                    logger.debug('wait')
                time.sleep(2)
            except BlockingIOError:
                break
            except KeyboardInterrupt:
                logger.info('keyboard interrupt')
                break


if __name__ == "__main__":
    DEFAULT_HOST, DEFAULT_PORT = '0.0.0.0', 9997

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s\t%(levelname)s:\t%(message)s')
    logger = logging.getLogger("MainThread")

    host = DEFAULT_HOST
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    test((host, port))

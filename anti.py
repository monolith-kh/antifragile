# -*- coding: utf-8 -*-

import logging
import socketserver
import threading
import signal
from typing import List, Optional, Dict, Any

from network import Network

from fbs.pilot import Command, Sender, Request, Response, Player, Data

from packet import request_packet_builder, response_packet_builder


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 9997
DEFAULT_BUFFER_SIZE = 1460

LOG_LEVEL_MAINTHREAD = logging.DEBUG
LOG_LEVEL_ANTI_MANAGER = logging.DEBUG
LOG_LEVEL_ANTI_TCP_HANDLER = logging.DEBUG
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(name)s\t%(levelname)s:\t%(message)s')

socketserver.TCPServer.allow_reuse_address = True

class AntiManager():

    def __init__(self):
        self.__clients = []
        host = DEFAULT_HOST
        port = DEFAULT_PORT
        buffer_size = DEFAULT_BUFFER_SIZE
        clients = self.__clients
        self._logger = logging.getLogger('Anti Manager')
        self._logger.setLevel(LOG_LEVEL_ANTI_MANAGER)

        class TCPSocketHandler(socketserver.BaseRequestHandler):
            __LOGGER = logging.getLogger('Anti TCPHandler')
            __LOGGER.setLevel(LOG_LEVEL_ANTI_TCP_HANDLER)
            __LOGGER.info('Start')

            def handle(self):
                self.__LOGGER.debug(self.request)
                self.handle_contact(self.request)
                threading.Thread(target=self.handle_receive, args=(self.request, ) , name='handle_receive').start()
                threading.Thread(target=self.handle_send, args=(self.request, ), name='handle_send').start()

            def handle_contact(self, client):
                self.__LOGGER.info('Start Contact')
                req = request_packet_builder(Command.Command.welcome, Sender.Sender.server)
                client.send(req)

                buf = client.recv(DEFAULT_BUFFER_SIZE)
                self.__LOGGER.debug(buf)
                res= Response.Response.GetRootAsResponse(buf, 0)
                self.__LOGGER.debug(res.Timestamp())
                self.__LOGGER.debug(res.Command())
                self.__LOGGER.debug(res.ErrorCode())
                self.__LOGGER.debug(res.Data())
                if res.Command() == Command.Command.welcome and res.ErrorCode() == 0:
                    player = Player.Player()
                    player.Init(res.Data().Bytes, res.Data().Pos)
                    self.__LOGGER.debug(player.Uid())
                    self.__LOGGER.debug(str(player.Username()))
                    self.__LOGGER.debug(str(player.ImageUrl()))
                    self.__LOGGER.debug(player.Score())
                    self.__LOGGER.debug(player.Status())
                else:
                    self.__LOGGER.debug('Error command')
                clients.append(client)
                self.__LOGGER.info('Contact Finished')
                self.__LOGGER.debug(clients)

            def handle_receive(self, client):
                self.__LOGGER.info('Start Receive')
                self.__LOGGER.debug(client)
                while True:
                    buf = client.recv(DEFAULT_BUFFER_SIZE)
                    self.__LOGGER.debug(buf)

            def handle_send(self, client):
                self.__LOGGER.info('Start Send')
                self.__LOGGER.debug(client)


        class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
            pass

        self.__server = ThreadedTCPServer((host, port), TCPSocketHandler)

    def start(self):
        threading.Thread(target=self.__server.serve_forever, name='AntiManager').start()
        self._logger.info('Start Server')

    def stop(self):
        self._logger.info('Shutdown AntiManager')

        # for display in self.__clients:
        #     display.stop()

        self.__server.shutdown()

if __name__ == '__main__':

    
    logger = logging.getLogger('MainThread')
    logger.setLevel(LOG_LEVEL_MAINTHREAD)
    logger.info('Start')
    server = AntiManager()

    def shutdown_handler(sig, frame):
        server.stop()

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    server.start()

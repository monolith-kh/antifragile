# -*-  coding: utf-8 -*-

import sys
import time
import click

from twisted.internet import protocol, reactor
from twisted.logger import Logger, globalLogPublisher, FilteringLogObserver, LogLevel, LogLevelFilterPredicate, textFileLogObserver

from ringggo_packet import Header, PositionObject, PositionNoti, Packet

LOG_LEVELS = dict(
    debug=LogLevel.debug,
    info=LogLevel.info,
    warn=LogLevel.warn,
    error=LogLevel.error,
    critical=LogLevel.critical
)

class Rtls(protocol.DatagramProtocol):
    log = Logger()

    def __init__(self, host, port, cars = {}):
        self.host = host
        self.port = port
        self.cars = cars

    def startProtocol(self):
        self.log.info('New connection')
        self.transport.connect(self.host, self.port)
        self.log.info('connected')

        packet = Packet(
            sender=Header.SENDER_ADMIN,
            code=Header.PK_POSITION_LISTEN)
        self.transport.write(packet.to_bytes())

    def stopProtocol(self):
        self.log.info('Disconnected')

    def datagramReceived(self, data, addr):
        self.log.debug('received {} from {}'.format(data, addr))
        p = Packet.from_bytes(data)
        self.log.debug('header code: {}'.format(p.header.code))
        for c in p.body:
            self.cars[c.object_number] = dict(
                x=c.position_noti.position_x,
                y=c.position_noti.position_y
            )
            self.log.debug('{}, {}, {}'.format(c.object_number, c.position_noti.position_x, c.position_noti.position_y))
        self.log.info('car list: {cars}'.format(cars=self.cars))
        # packet = Packet(
        #     sender=Header.SENDER_ADMIN,
        #     code=Header.PK_POSITION_LISTEN_STOP)
        # self.transport.write(packet.to_bytes())

    def connectionRefused(self):
        self.log.info('No one listening')

@click.command()
@click.option('--host', default='192.168.40.254', type=click.STRING, required=True, help='set host (default: localhost)')
@click.option('--port', default=9999, type=click.INT, required=True, help='set port (default: 9999)')
@click.option('--log-level', default='info', type=click.Choice(['debug', 'info', 'warn', 'error', 'critical'], case_sensitive=False), help='set log level (default: info)')
def main(host, port, log_level):
    log = Logger('MainThread')
    predicate = LogLevelFilterPredicate(defaultLogLevel=LOG_LEVELS.get(log_level))
    observer = FilteringLogObserver(textFileLogObserver(outFile=sys.stdout), [predicate])
    observer._encoding = 'utf-8'
    globalLogPublisher.addObserver(observer)

    log.info('Let\'s go RINGGGO Rtls')
    reactor.listenUDP(0, Rtls(host, port, {}))
    reactor.run()

if __name__ == '__main__':
    main()

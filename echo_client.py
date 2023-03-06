# -*- coding: utf-8 -*-

import click
from faker import Faker

from twisted.internet import reactor, protocol

from packet import request_packet_builder, response_packet_builder
from fbs.pilot import Command, Sender, Request, Response, Player, Data
import player_model


class EchoClient(protocol.Protocol):
    def __init__(self, uid):
        faker = Faker('ko_KR')
        self.uid = uid
        self.username = faker.name()
        self.user = player_model.Player(
            uid=self.uid,
            username=self.username,
            image_url = 'http://{}'.format(self.username),
            score = 100 + self.uid,
            status = player_model.PlayerStatus.idle
        )
        print(self.user)

    def connectionMade(self):
        print('Connected')
        #self.transport.write(u'Hellom, world!'.encode('utf-8'))

    def dataReceived(self, buf):
        print('Server said: {}'.format(buf))
        req = Request.Request.GetRootAsRequest(buf, 0)
        print(req.Timestamp())
        print(req.Command())
        print(req.Sender())
        print(req.Data())
        print("----------")
        if req.Command() == Command.Command.welcome and req.Sender() == Sender.Sender.server:
            res = response_packet_builder(Command.Command.welcome, error_code=0, data=self.user) 
            print(res)
            self.transport.write(bytes(res))
            print('success contact: {}'.format(self.user.username))
        elif req.Command() == Command.Command.ping and req.Sender() == Sender.Sender.server:
            res = response_packet_builder(Command.Command.ping, error_code=0) 
            print(res)
            self.transport.write(bytes(res))
            print('ping command')
            pass
        else:
            print('Wrong request')
        # self.transport.loseConnection()

    def connectionLost(self, reason):
        print('Connection list.')
        print(reason)

class EchoFactory(protocol.ClientFactory):
    def __init__(self, uid):
        self.uid = uid 
        print(uid)

    def buildProtocol(self, addr):
        print('addr: {}, uid: {}'.format(addr, self.uid))
        return EchoClient(self.uid)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed.')
        print(reason)
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print('Connection lost.')
        print(reason)
        reactor.stop()

@click.command()
@click.option('--host', default='localhost', type=click.STRING, required=True, help='set server host')
@click.option('--port', default=1234, type=click.INT, required=True, help='set server port')
@click.option('--uid', type=click.INT, required=True, help='set uid for player')
def main(host, port, uid):
    ef = EchoFactory(uid)
    reactor.connectTCP(host, port, ef)
    reactor.run()

if __name__ == '__main__':
    main()

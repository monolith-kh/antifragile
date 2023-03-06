# -*-  coding: utf-8 -*-

import time

import click
import faker

from twisted.internet import protocol, reactor, endpoints, task

from packet import request_packet_builder, response_packet_builder
from fbs.pilot import Command, Sender, Request, Response, Player, Data
import player_model


class Echo(protocol.Protocol):
    def __init__(self, users):
        self.users = users
        self.name = None
        self.state = 'WHOAREYOU'

    def connectionMade(self):
        print('New connection')
        req = request_packet_builder(Command.Command.welcome, Sender.Sender.server)
        print(req)
        self.transport.write(bytes(req))

    def connectionLost(self, reason):
        if self.name in self.users:
            del self.users[self.name]
            print('connection lost: {}'.format(self.name))

    def dataReceived(self, buf):
        if self.state == 'WHOAREYOU':
            self._handle_WHOAREYOU(buf)
        else:
            self._handle_CONNECT(buf)
    
    def _handle_WHOAREYOU(self, buf):
        print(buf)
        res= Response.Response.GetRootAsResponse(buf, 0)
        print(res.Timestamp())
        print(res.Command())
        print(res.ErrorCode())
        print(res.Data())
        if res.Command() == Command.Command.welcome and res.ErrorCode() == 0:
            player = Player.Player()
            player.Init(res.Data().Bytes, res.Data().Pos)
            pm = player_model.Player(
                uid=player.Uid(),
                username=player.Username(),
                image_url=player.ImageUrl(),
                score=player.Score(),
                status=player.Status())
            print(pm)
            self.name = pm.username
            self.users[self.name] = self
            self.state = 'CONNECT'
            print(self.users)
        else:
            print('Error command')

    def _handle_CONNECT(self, buf):
        print(buf)
        res= Response.Response.GetRootAsResponse(buf, 0)
        print(res.Timestamp())
        print(res.Command())
        print(res.ErrorCode())
        print(res.Data())
        if res.Command() == Command.Command.ping and res.ErrorCode() == 0:
            print('response ping command OK')
        else:
            print('wrong command')
        # message = '{}: {}'.format(self.name, data)
        # print(message) 
        # for name, protocol in self.users.items():
        #     if protocol != self:
        #         protocol.transport.write(message.encode('utf-8'))


class EchoFactory(protocol.Factory):
    def __init__(self):
        self.users = {}

    def buildProtocol(self, addr):
        print(addr)
        return Echo(self.users)
    
    def startFactory(self):
        print('start factory')

    def stopFactory(self):
        print('stop factory')

def run_ping_task(users):
    print(users)
    for u in users.values():
        print(u)
        req = request_packet_builder(Command.Command.ping, Sender.Sender.server)
        print(req)
        u.transport.write(bytes(req))
    return

def cbLoopDone(result):
    print(result)

def ebLoopFailed(failure):
    print(failure.getBriefTraceback())

@click.command()
@click.option('--port', default=1234, type=click.INT, required=True, help='set port')
@click.option('--ping-interval', default=5.0, type=click.FLOAT, help='set interval of ping(seconds)')
def main(port, ping_interval):
    ep = endpoints.TCP4ServerEndpoint(reactor, port)
    ef = EchoFactory()
    ep.listen(ef)

    loop = task.LoopingCall(run_ping_task, ef.users)
    loop_deferred = loop.start(ping_interval)
    loop_deferred.addCallback(cbLoopDone)
    loop_deferred.addErrback(ebLoopFailed)

    reactor.run()

if __name__ == '__main__':
    main()
    
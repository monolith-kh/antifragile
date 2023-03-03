# -*-  coding: utf-8 -*-

from twisted.internet import protocol, reactor, endpoints

from packet import request_packet_builder, response_packet_builder
from fbs.pilot import Command, Sender, Request, Response, Player, Data
import player_model

PORT = 1234

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

    def _handle_CONNECT(self, data):
        message = '{}: {}'.format(self.name, data)
        print(message) 
        for name, protocol in self.users.items():
            if protocol != self:
                protocol.transport.write(message.encode('utf-8'))


class EchoFactory(protocol.Factory):
    def __init__(self):
        self.users = {}

    def buildProtocol(self, addr):
        return Echo(self.users)


def main():
    # endpoints.serverFromString(reactor, 'tcp:1234').listen(EchoFactory())
    ep = endpoints.TCP4ServerEndpoint(reactor, PORT)
    ep.listen(EchoFactory())
    reactor.run()

if __name__ == '__main__':
    main()

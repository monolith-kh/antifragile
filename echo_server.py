# -*-  coding: utf-8 -*-

from datetime import datetime

import click

from twisted.internet import protocol, reactor, endpoints, task

from packet import request_packet_builder, response_packet_builder
from fbs.pilot import Command, Sender, Request, Response, Player, Data
import player_model
import bubble_model


class State(object):
    welcome = 0
    connect = 1

class Echo(protocol.Protocol):
    def __init__(self, users, players, bubbles):
        self.users = users
        self.user = None
        self.players = players
        self.bubbles = bubbles
        self.state = State.welcome

    def connectionMade(self):
        print('New connection')
        req = request_packet_builder(Command.Command.welcome, Sender.Sender.server)
        print(req)
        self.transport.write(bytes(req))

    def connectionLost(self, reason):
        print(reason)
        if self.user.uid in self.users:
            del self.users[self.user.uid]
            for p in self.players.players:
                if p.uid == self.user.uid:
                    self.players.players.remove(p)
                    print('connection lost: {}'.format(self.user.username))
                    break

    def dataReceived(self, buf):
        print('Receive Data')
        print(buf)
        if self.state == State.welcome:
            self._handle_welcome(buf)
        elif self.state == State.connect:
            self._handle_connect(buf)
        else:
            print('wrong state')
    
    def _handle_welcome(self, buf):
        res= Response.Response.GetRootAsResponse(buf, 0)
        print(res.Timestamp())
        print(res.Command())
        print(res.ErrorCode())
        print(res.Data())
        if res.Command() == Command.Command.welcome and res.ErrorCode() == 0:
            player = Player.Player()
            player.Init(res.Data().Bytes, res.Data().Pos)
            self.user = player_model.Player(
                uid=player.Uid(),
                username=player.Username(),
                image_url=player.ImageUrl(),
                score=player.Score(),
                status=player.Status())
            print(self.user)
            self.users[self.user.uid] = self
            self.players.players.append(self.user)
            self.state = State.connect
            print(self.users)
            print(self.players)
        else:
            print('Error command')

    def _handle_connect(self, buf):
        req = Request.Request.GetRootAsRequest(buf, 0)
        print(req.Timestamp())
        print(req.Command())
        print(req.Sender())
        print(req.Data())
        if req.Command() == Command.Command.ping:
            print('request ping command OK')
        elif req.Command() == Command.Command.bubble_get and req.Sender() == Sender.Sender.client:
            print('request bubble_get command OK')
            res = response_packet_builder(Command.Command.bubble_get, error_code=0, data=self.bubbles.bubbles[3]) 
            print(res)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.bubble_status and req.Sender() == Sender.Sender.client:
            print('request bubble_status command OK')
            res = response_packet_builder(Command.Command.bubble_status, error_code=0, data=self.bubbles.bubbles) 
            print(res)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.player_get and req.Sender() == Sender.Sender.client:
            print('request player_get command OK')
            res = response_packet_builder(Command.Command.player_get, error_code=0, data=self.user) 
            print(res)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.player_status and req.Sender() == Sender.Sender.client:
            print('request player_status command OK')
            res = response_packet_builder(Command.Command.player_status, error_code=0, data=self.players.players) 
            print(res)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.game_ready and req.Sender() == Sender.Sender.client:
            print('request game_ready command OK')
            self.user.status = player_model.PlayerStatus.ready
            for p in self.players.players:
                if p.uid == self.user.uid:
                    p.status = player_model.PlayerStatus.ready
            res = response_packet_builder(Command.Command.game_ready, error_code=0) 
            print(res)
            self.transport.write(bytes(res))
        else:
            print('request wrong command')
        # message = '{}: {}'.format(self.name, data)
        # print(message) 
        # for name, protocol in self.users.items():
        #     if protocol != self:
        #         protocol.transport.write(message.encode('utf-8'))


class EchoFactory(protocol.ServerFactory):
    def __init__(self):
        self.users = {}
        self.players = player_model.Players()
        self.bubbles = generate_bubbles()

    def buildProtocol(self, addr):
        print(addr)
        return Echo(self.users, self.players, self.bubbles)
    
    def startFactory(self):
        print('start factory')

    def stopFactory(self):
        print('stop factory')

def run_ping_task(users, players, bubbles):
    print('ping task: {}'.format(datetime.now()))
    print(users)
    print(players)
    print(bubbles)
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

BUBBLE_COUNT = 10
BUBBLE_POS_OFFSET = 140

def generate_bubbles() -> bubble_model.Bubbles:
    bs_obj = bubble_model.Bubbles()
    for i in range(BUBBLE_COUNT):
        vec = bubble_model.Vec2(x=i*BUBBLE_POS_OFFSET, y=0)
        bm = bubble_model.Bubble(
            uid=i,
            pos_cur=vec,
            pos_target=vec,
            speed=0.0,
            type=bubble_model.BubbleType.normal)
        bs_obj.bubbles.append(bm)
    return bs_obj

@click.command()
@click.option('--port', default=1234, type=click.INT, required=True, help='set port(default: 1234)')
@click.option('--ping', default=0.0, type=click.FLOAT, help='set interval of ping(default: 0.0 seconds)')
def main(port, ping):
    ep = endpoints.TCP4ServerEndpoint(reactor, port)
    ef = EchoFactory()
    ep.listen(ef)

    if ping:
        loop = task.LoopingCall(run_ping_task, ef.users, ef.players, ef.bubbles)
        loop_deferred = loop.start(ping, False)
        loop_deferred.addCallback(cbLoopDone)
        loop_deferred.addErrback(ebLoopFailed)

    print('start tcp server')
    print('connect to {} port'.format(port))
    reactor.run()

if __name__ == '__main__':
    main()

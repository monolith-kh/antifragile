# -*- coding: utf-8 -*-

import time
from datetime import datetime
import click
from faker import Faker

from twisted.internet import reactor, protocol, endpoints, task

from packet import request_packet_builder, response_packet_builder
from fbs.pilot import Command, Sender, Request, Response, Player, Players, Data, Bubble, Bubbles, BubbleType, Joycon
import player_model
import bubble_model
import joycon_model


class State(object):
    welcome = 0
    connect = 1

class EchoClient(protocol.Protocol):
    def __init__(self, uid):
        self.state = State.welcome
        faker = Faker('ko_KR')
        username = faker.name()
        self.user = player_model.Player(
            uid=uid,
            username=username,
            image_url = 'http://{}.png'.format(username),
            score = 100 + uid,
            status = player_model.PlayerStatus.idle
        )
        print(self.user)

    def connectionMade(self):
        print('Connected')
        
    def dataReceived(self, buf):
        print('Receive Data')
        print('Server said: {}'.format(buf))
        if len(buf) == int.from_bytes(buf[0:2], 'big'):
            print('valid packet size')
        else:
            print('!!! invalid packet size !!! header: {}, packet: {}'.format(int.from_bytes(buf[0:2], 'big'), len(buf)))
            return
        if self.state == State.welcome:
            self._handle_welcome(buf[2:])
        elif self.state == State.connect:
            self._handle_connect(buf[2:])
        else:
            print('wrong state')

    def _handle_welcome(self, buf):
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
            self.state = State.connect
        else:
            print('Wrong request')

    def _handle_connect(self, buf):
        req = Request.Request.GetRootAsRequest(buf, 0)
        print(req.Timestamp())
        print(req.Command())
        print(req.Sender())
        print(req.Data())
        print("----------")
        if req.Command() == Command.Command.ping and req.Sender() == Sender.Sender.server:
            res = response_packet_builder(Command.Command.ping, error_code=0) 
            print(res)
            self.transport.write(bytes(res))
            print('response ping command')
        elif req.Command() == Command.Command.bubble_get:
            bubble = Bubble.Bubble()
            bubble.Init(req.Data().Bytes, req.Data().Pos)
            pos_cur = bubble_model.Vec2(
                x=bubble.PosCur().X(),
                y=bubble.PosCur().Y()
            )
            pos_target = bubble_model.Vec2(
                x=bubble.PosTarget().X(),
                y=bubble.PosTarget().Y()
            )
            bm = bubble_model.Bubble(
                uid=bubble.Uid(),
                pos_cur=pos_cur,
                pos_target=pos_target,
                speed=bubble.Speed(),
                type=bubble.Type()
            )
            print(bm)
        elif req.Command() == Command.Command.bubble_status:
            bubbles = Bubbles.Bubbles()
            bubbles.Init(req.Data().Bytes, req.Data().Pos)
            print(bubbles.BubblesLength())
            for i in range(bubbles.BubblesLength()):
                pos_cur = bubble_model.Vec2(
                    x=bubbles.Bubbles(i).PosCur().X(),
                    y=bubbles.Bubbles(i).PosCur().Y()
                )
                pos_target = bubble_model.Vec2(
                    x=bubbles.Bubbles(i).PosTarget().X(),
                    y=bubbles.Bubbles(i).PosTarget().Y()
                )
                bm = bubble_model.Bubble(
                    uid=bubbles.Bubbles(i).Uid(),
                    pos_cur=pos_cur,
                    pos_target=pos_target,
                    speed=bubbles.Bubbles(i).Speed(),
                    type=bubbles.Bubbles(i).Type()
                )
                print(bm)
        elif req.Command() == Command.Command.player_get:
            player = Player.Player()
            player.Init(req.Data().Bytes, req.Data().Pos)
            self.user.uid = player.Uid()
            self.user.username = player.Username()
            self.user.image_url = player.ImageUrl()
            self.user.score = player.Score()
            self.user.status = player.Status()
            print(self.user)
        elif req.Command() == Command.Command.player_status:
            players = Players.Players()
            players.Init(req.Data().Bytes, req.Data().Pos)
            print(players.PlayersLength())
            for i in range(players.PlayersLength()):
                pm = player_model.Player(
                    uid=players.Players(i).Uid(),
                    username=players.Players(i).Username(),
                    image_url=players.Players(i).ImageUrl(),
                    score=players.Players(i).Score(),
                    status=players.Players(i).Status()
                )
                print(pm)
        elif req.Command() == Command.Command.game_ready:
            print('response game_ready command')
        elif req.Command() == Command.Command.joycon:
            joycon = Joycon.Joycon()
            joycon.Init(req.Data().Bytes, req.Data().Pos)
            print('right gyro x: {}'.format(joycon.RightGyroX()))
            print('right a button: {}'.format(joycon.RightA()))
        elif req.Command() == Command.Command.shoot:
            print('shoot event')
        elif req.Command() == Command.Command.reload:
            print('reload event')
        else:
            print('wrong command')

    def connectionLost(self, reason):
        print('Connection lost.')
        print(reason)
        reactor.stop()

class EchoFactory(protocol.ClientFactory):
    def __init__(self, uid):
        self.uid = uid 
        self.proto = None
        print('uid: {}'.format(uid))

    def buildProtocol(self, addr):
        print('addr: {}, uid: {}'.format(addr, self.uid))
        self.proto = EchoClient(self.uid) 
        return self.proto

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

def run_game_ready_task(factory):
    print('game ready task: {}'.format(datetime.now()))
    print(factory)
    req = request_packet_builder(Command.Command.game_ready, Sender.Sender.client)
    print(req)
    if factory.proto:
        factory.proto.transport.write(bytes(req))

def run_player_status_task(factory):
    print('player status task: {}'.format(datetime.now()))
    print(factory)
    req = request_packet_builder(Command.Command.player_status, Sender.Sender.client)
    print(req)
    if factory.proto:
        factory.proto.transport.write(bytes(req))

def run_player_get_task(factory):
    print('player get task: {}'.format(datetime.now()))
    print(factory)
    req = request_packet_builder(Command.Command.player_get, Sender.Sender.client)
    print(req)
    if factory.proto:
        factory.proto.transport.write(bytes(req))

def run_bubble_status_task(factory):
    print('bubble status task: {}'.format(datetime.now()))
    print(factory)
    bubbles = generate_bubbles()
    req = request_packet_builder(Command.Command.bubble_status, Sender.Sender.client, bubbles.bubbles)
    print(req)
    if factory.proto:
        factory.proto.transport.write(bytes(req))

def run_bubble_get_task(factory):
    print('bubble get task: {}'.format(datetime.now()))
    print(factory)
    req = request_packet_builder(Command.Command.bubble_get, Sender.Sender.client)
    print(req)
    if factory.proto:
        factory.proto.transport.write(bytes(req))

def run_send_loop_task(factory):
    print('send loop task: {}'.format(datetime.now()))
    print(factory)
    req = request_packet_builder(Command.Command.ping, Sender.Sender.client)
    print(req)
    if factory.proto:
        factory.proto.transport.write(bytes(req))

def cbLoopDone(result):
    print(result)

def ebLoopFailed(failure):
    print(failure.getBriefTraceback())

@click.command()
@click.option('--host', default='localhost', type=click.STRING, required=True, help='set server host(default: localhost)')
@click.option('--port', default=1234, type=click.INT, required=True, help='set server port(default: 1234)')
@click.option('--uid', type=click.INT, required=True, help='set uid for player')
def main(host, port, uid):
    ep = endpoints.TCP4ClientEndpoint(reactor, host, port)
    ef = EchoFactory(uid)
    ep.connect(ef)

    loop_game_ready = task.LoopingCall(run_game_ready_task, ef)
    loop_game_ready_deferred = loop_game_ready.start(11.5, False)
    loop_game_ready_deferred.addCallback(cbLoopDone)
    loop_game_ready_deferred.addErrback(ebLoopFailed)

    loop_player_status = task.LoopingCall(run_player_status_task, ef)
    loop_player_status_deferred = loop_player_status.start(2.0, False)
    loop_player_status_deferred.addCallback(cbLoopDone)
    loop_player_status_deferred.addErrback(ebLoopFailed)

    loop_player_get = task.LoopingCall(run_player_get_task, ef)
    loop_player_get_deferred = loop_player_get.start(7.0, False)
    loop_player_get_deferred.addCallback(cbLoopDone)
    loop_player_get_deferred.addErrback(ebLoopFailed)

    loop_bubble_status = task.LoopingCall(run_bubble_status_task, ef)
    loop_bubble_status_deferred = loop_bubble_status.start(4.0, False)
    loop_bubble_status_deferred.addCallback(cbLoopDone)
    loop_bubble_status_deferred.addErrback(ebLoopFailed)

    loop_bubble_get = task.LoopingCall(run_bubble_get_task, ef)
    loop_bubble_get_deferred = loop_bubble_get.start(9.0, False)
    loop_bubble_get_deferred.addCallback(cbLoopDone)
    loop_bubble_get_deferred.addErrback(ebLoopFailed)

    loop_ping = task.LoopingCall(run_send_loop_task, ef)
    loop_ping_deferred = loop_ping.start(10.0, False)
    loop_ping_deferred.addCallback(cbLoopDone)
    loop_ping_deferred.addErrback(ebLoopFailed)

    reactor.run()

if __name__ == '__main__':
    main()

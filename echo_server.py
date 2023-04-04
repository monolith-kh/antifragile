# -*-  coding: utf-8 -*-

import sys
from datetime import datetime

import click

from twisted.internet import protocol, reactor, endpoints, task
from twisted.logger import Logger, globalLogPublisher, FilteringLogObserver, LogLevel, LogLevelFilterPredicate, textFileLogObserver

from packet import request_packet_builder, response_packet_builder
from fbs.pilot import Command, Sender, Request, Response, Player, Data, Bubbles, Bubble
import player_model
import bubble_model

LOG_LEVELS = dict(
    debug=LogLevel.debug,
    info=LogLevel.info,
    warn=LogLevel.warn,
    error=LogLevel.error,
    critical=LogLevel.critical
)

class State(object):
    welcome = 0
    connect = 1

class Echo(protocol.Protocol):
    log = Logger()

    def __init__(self, users, players, bubbles):
        self.users = users
        self.user = None
        self.players = players
        self.bubbles = bubbles
        self.state = State.welcome

    def connectionMade(self):
        self.log.info('New connection')
        req = request_packet_builder(Command.Command.welcome, Sender.Sender.server)
        self.log.debug('Request: {}'.format(str(req)))
        self.transport.write(bytes(req))

    def connectionLost(self, reason):
        self.log.info(str(reason))
        if self.user.uid in self.users:
            del self.users[self.user.uid]
            for p in self.players.players:
                if p.uid == self.user.uid:
                    self.players.players.remove(p)
                    self.log.info('connection lost: {}'.format(self.user.username))
                    break

    def dataReceived(self, buf):
        if self.user:
            self.log.info('{} {} Receive Data'.format(self.user.uid, self.user.username))
        else:
            self.log.info('Receive Data')
        self.log.debug('Bytes: {}'.format(str(buf)))
        if self.state == State.welcome:
            self._handle_welcome(buf)
        elif self.state == State.connect:
            self._handle_connect(buf)
        else:
            self.log.warn('wrong state')
    
    def _handle_welcome(self, buf):
        res= Response.Response.GetRootAsResponse(buf, 0)
        self.log.debug('Timestamp: {}'.format(str(res.Timestamp())))
        self.log.debug('Command: {}'.format(str(res.Command())))
        self.log.debug('ErrorCode: {}'.format(str(res.ErrorCode())))
        self.log.debug('Data: {}'.format(str(res.Data())))
        if res.Command() == Command.Command.welcome:
        #if res.Command() == Command.Command.welcome and res.ErrorCode() == 0:
            player = Player.Player()
            player.Init(res.Data().Bytes, res.Data().Pos)
            self.user = player_model.Player(
                uid=player.Uid(),
                username=player.Username(),
                image_url=player.ImageUrl(),
                score=player.Score(),
                status=player.Status())
            self.log.info(str(self.user))
            self.users[self.user.uid] = self
            self.players.players.append(self.user)
            self.state = State.connect
            self.log.debug(str(self.users))
            self.log.debug(str(self.players))
        else:
            self.log.warn('Error command')

    def _handle_connect(self, buf):
        req = Request.Request.GetRootAsRequest(buf, 0)
        self.log.debug('Timestamp: {}'.format(str(req.Timestamp())))
        self.log.debug('Command: {}'.format(str(req.Command())))
        self.log.debug('Sender: {}'.format(str(req.Sender())))
        self.log.debug('Data: {}'.format(str(req.Data())))
        if req.Command() == Command.Command.ping:
            self.log.info('request ping command OK')
        elif req.Command() == Command.Command.bubble_get and req.Sender() == Sender.Sender.client:
            self.log.info('request bubble_get command OK')
            res = response_packet_builder(Command.Command.bubble_get, error_code=0, data=self.bubbles.bubbles[3]) 
            self.log.debug('response data: {}'.format(str(res)))
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.bubble_status and req.Sender() == Sender.Sender.client:
            self.log.info('request bubble_status command OK')
            res = response_packet_builder(Command.Command.bubble_status, error_code=0, data=self.bubbles.bubbles) 
            self.log.debug('response lenth: {}'.format(len(res)))
            self.log.debug('response data: {}'.format(str(res)))
            self.log.debug('response lenth(bytes): {}'.format(len(bytes(res))))
            self.log.debug('response data(bytes): {}'.format(str(bytes(res))))
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.player_get and req.Sender() == Sender.Sender.client:
            self.log.info('request player_get command OK')
            res = response_packet_builder(Command.Command.player_get, error_code=0, data=self.user) 
            self.log.debug('response data: {}'.format(str(res)))
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.player_status and req.Sender() == Sender.Sender.client:
            self.log.info('request player_status command OK')
            res = response_packet_builder(Command.Command.player_status, error_code=0, data=self.players.players) 
            self.log.debug('response data: {}'.format(str(res)))
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.game_ready and req.Sender() == Sender.Sender.client:
            self.log.info('request game_ready command OK')
            self.user.status = player_model.PlayerStatus.ready
            for p in self.players.players:
                if p.uid == self.user.uid:
                    p.status = player_model.PlayerStatus.ready
            res = response_packet_builder(Command.Command.game_ready, error_code=0) 
            self.log.debug('response data: {}'.format(str(res)))
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.game_start and req.Sender() == Sender.Sender.client:
            self.log.info('request game_start command OK')
            self.user.status = player_model.PlayerStatus.game
            for p in self.players.players:
                p.status = player_model.PlayerStatus.game
            res = response_packet_builder(Command.Command.game_start, error_code=0) 
            self.log.debug('response data: {}'.format(str(res)))
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.game_finish and req.Sender() == Sender.Sender.client:
            self.log.info('request game_finish command OK')
            self.user.status = player_model.PlayerStatus.idle
            for p in self.players.players:
                p.status = player_model.PlayerStatus.idle
            res = response_packet_builder(Command.Command.game_finish, error_code=0) 
            self.log.debug('response data: {}'.format(str(res)))
            self.transport.write(bytes(res))
        else:
            self.log.warn('request wrong command')
        # message = '{}: {}'.format(self.name, data)
        # print(message) 
        # for name, protocol in self.users.items():
        #     if protocol != self:
        #         protocol.transport.write(message.encode('utf-8'))


class EchoFactory(protocol.ServerFactory):
    log = Logger()
    def __init__(self):
        self.users = {}
        self.players = player_model.Players()
        self.bubbles = generate_bubbles()

    def buildProtocol(self, addr):
        self.log.info(str(addr))
        return Echo(self.users, self.players, self.bubbles)
    
    def startFactory(self):
        self.log.info('start factory')

    def stopFactory(self):
        self.log.info('stop factory')

class ScheduleTask:
    log = Logger()
    @classmethod
    def run_ping_task(cls, users, players, bubbles):
        cls.log.info('ping task: {}'.format(datetime.now()))
        cls.log.info(str(players))
        cls.log.info(str(bubbles))
        for u in users.values():
            req = request_packet_builder(Command.Command.ping, Sender.Sender.server)
            cls.log.debug(str(req))
            u.transport.write(bytes(req))

    @classmethod
    def cbLoopDone(cls, result):
        cls.log.info(result)

    @classmethod
    def ebLoopFailed(cls, failure):
        cls.log.error(failure.getBriefTraceback())

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
@click.option('--port', default=1234, type=click.INT, required=True, help='set port (default: 1234)')
@click.option('--ping', default=0.0, type=click.FLOAT, help='set interval of ping (default: 0.0 seconds)')
@click.option('--log-level', default='info', type=click.Choice(['debug', 'info', 'warn', 'error', 'critical'], case_sensitive=False), help='set log level (default: info)')
def main(port, ping, log_level):
    log = Logger('MainThread')
    predicate = LogLevelFilterPredicate(defaultLogLevel=LOG_LEVELS.get(log_level))
    observer = FilteringLogObserver(textFileLogObserver(outFile=sys.stdout), [predicate])
    observer._encoding = 'utf-8'
    globalLogPublisher.addObserver(observer)

    ep = endpoints.TCP4ServerEndpoint(reactor, port)
    ef = EchoFactory()
    ep.listen(ef)

    if ping:
        loop = task.LoopingCall(ScheduleTask.run_ping_task, ef.users, ef.players, ef.bubbles)
        loop_deferred = loop.start(ping, False)
        loop_deferred.addCallback(ScheduleTask.cbLoopDone)
        loop_deferred.addErrback(ScheduleTask.ebLoopFailed)

    log.info('Let\'s go ANTIFRAGILE')
    reactor.run()

if __name__ == '__main__':
    main()

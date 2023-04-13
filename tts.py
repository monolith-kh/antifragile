# -*-  coding: utf-8 -*-

import sys
import time
from datetime import datetime

import click

from twisted.internet import protocol, reactor, endpoints, task
from twisted.logger import Logger, globalLogPublisher, FilteringLogObserver, LogLevel, LogLevelFilterPredicate, textFileLogObserver

from packet import request_packet_builder, response_packet_builder
from fbs.pilot import Command, Sender, Request, Response, Player, Data, Bubbles, Bubble, Joycon
import player_model
import bubble_model
import joycon_model

from ringggo_packet import Header, PositionObject, PositionNoti, Packet

from pyjoycon import get_R_id, get_L_id
from rumble import RumbleJoyCon, RumbleData

LOG_LEVELS = dict(
    debug=LogLevel.debug,
    info=LogLevel.info,
    warn=LogLevel.warn,
    error=LogLevel.error,
    critical=LogLevel.critical
)


class Singleton(type):
    __instances = {}

    def __call__(self, *args, **kwargs):
        if self not in self.__instances:
            self.__instances[self] = super().__call__(*args, **kwargs)
        return self.__instances[self]


VENDOR_ID = 1406
PRODUCT_ID_LEFT = 8198
PRODUCT_ID_RIGHT = 8199

class JoyconService(metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        joycon_r_id = get_R_id()
        if isinstance(joycon_r_id, tuple) and len(joycon_r_id) == 3 and joycon_r_id[0] == VENDOR_ID and joycon_r_id[1] == PRODUCT_ID_RIGHT and joycon_r_id[2]:
            self.joycon_r = RumbleJoyCon(*joycon_r_id) 
            print('[joycon right] connected')
            print(joycon_r_id)
        else:
            self.joycon_r = None
            print('[joycon right] failed')
        joycon_l_id = get_L_id()
        if isinstance(joycon_l_id, tuple) and len(joycon_l_id) == 3 and joycon_l_id[0] == VENDOR_ID and joycon_l_id[1] == PRODUCT_ID_LEFT and joycon_l_id[2]:
            self.joycon_l = RumbleJoyCon(*joycon_l_id) 
            print('[joycon left] connected')
            print(joycon_l_id)
        else:
            self.joycon_l = None
            print('[joycon left] failed')

    def is_connect_right(self):
        if isinstance(self.joycon_r, RumbleJoyCon) and get_R_id() == (self.joycon_r.vendor_id, self.joycon_r.product_id, self.joycon_r.serial):
            return True
        else:
            return False

    def is_connect_left(self):
        if isinstance(self.joycon_l, RumbleJoyCon) and get_L_id() == (self.joycon_l.vendor_id, self.joycon_l.product_id, self.joycon_l.serial):
            return True
        else:
            return False

    def get_info_right(self):
        if self.is_connect_right():
            return {
                'vendor_id': self.joycon_r.vendor_id,
                'product_id': self.joycon_r.product_id,
                'serial': self.joycon_r.serial,
            }
        else:
            return {}

    def get_info_left(self):
        if self.is_connect_left():
            return {
                'vendor_id': self.joycon_l.vendor_id,
                'product_id': self.joycon_l.product_id,
                'serial': self.joycon_l.serial,
            }
        else:
            return {}

    def set_paring_right(self):
        if self.is_connect_right():
            return True
        else:
            joycon_r_id = get_R_id()
            if joycon_r_id[0]:
                self.joycon_r = RumbleJoyCon(*joycon_r_id) 
                return True
            else:
                return False

    def set_paring_left(self):
        if self.is_connect_left():
            return True
        else:
            joycon_l_id = get_L_id()
            if joycon_l_id[0]:
                self.joycon_l = RumbleJoyCon(*joycon_l_id) 
                return True
            else:
                return False

    def get_status_right(self):
        if self.is_connect_right():
            return self.joycon_r.get_status()
        else:
            return {}

    def get_status_left(self):
        if self.is_connect_left():
            return self.joycon_l.get_status()
        else:
            return {}

    def set_rumble_right(self, freq,  amp):
        if self.is_connect_right():
            self.joycon_r.enable_vibration()
            rd = RumbleData(freq/2, freq, amp)
            self.joycon_r._send_rumble(rd.GetData())

    def set_rumble_left(self, freq, amp):
        if self.is_connect_left():
            self.joycon_l.enable_vibration()
            rd = RumbleData(freq/2, freq, amp)
            self.joycon_l._send_rumble(rd.GetData())

    def set_rumble_simple_right(self):
        if self.is_connect_right():
            self.joycon_r.enable_vibration()
            self.joycon_r.rumble_simple()

    def set_rumble_simple_left(self):
        if self.is_connect_left():
            self.joycon_l.enable_vibration()
            self.joycon_l.rumble_simple()


class RtlsService(metaclass=Singleton):
    def __init__(self, *args, **kwargs):
        self.cars = dict()
    
    def get_bubbles(self) -> bubble_model.Bubbles:
        bs_obj = bubble_model.Bubbles()
        for k, v in self.cars.items():
            vec = bubble_model.Vec2(x=v['x'], y=v['y'])
            bm = bubble_model.Bubble(
                uid=k,
                pos_cur=vec,
                pos_target=vec,
                speed=0.0,
                type=bubble_model.BubbleType.event)
            bs_obj.bubbles.append(bm)
        return bs_obj


class RtlsProtocol(protocol.DatagramProtocol):
    log = Logger()

    def __init__(self, host, port):
        self.host = host
        self.port = port
        RtlsService()

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
            RtlsService().cars[c.object_number] = dict(
                x=c.position_noti.position_x,
                y=c.position_noti.position_y
            )
            self.log.debug('{}, {}, {}'.format(c.object_number, c.position_noti.position_x, c.position_noti.position_y))
        self.log.debug('car list: {cars}'.format(cars=RtlsService().cars))
        # packet = Packet(
        #     sender=Header.SENDER_ADMIN,
        #     code=Header.PK_POSITION_LISTEN_STOP)
        # self.transport.write(packet.to_bytes())

    def connectionRefused(self):
        self.log.info('No one listening')


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
        self.log.info('Bytes Length: {}'.format(len(buf)))
        self.log.debug('Bytes: {}'.format(str(buf)))
        pac_size = int.from_bytes(buf[0:2], 'big')
        if len(buf) == pac_size:
            self.log.info('valid packet size ===  header: {}, packet: {}'.format(pac_size, len(buf)))
            pac = buf[2:]
        elif len(buf) > pac_size:
            self.log.warn('!!! large packet size <<< header: {}, packet: {}'.format(pac_size, len(buf)))
            pac = buf[:pac_size][2:]
        else:
            self.log.warn('!!! small packet size >>> header: {}, packet: {}'.format(pac_size, len(buf)))
            return
        if self.state == State.welcome:
            self._handle_welcome(pac)
        elif self.state == State.connect:
            self._handle_connect(pac)
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
        self.log.debug('Handler: {}, {}, {}, {}'.format(str(req.Timestamp()), str(req.Command()), str(req.Sender()), str(req.Data())))
        if req.Command() == Command.Command.ping:
            self.log.info('request ping command OK')
            res = bytearray()
        elif req.Command() == Command.Command.bubble_get and req.Sender() == Sender.Sender.client:
            self.log.info('request bubble_get command OK')
            res = response_packet_builder(Command.Command.bubble_get, error_code=0, data=self.bubbles.bubbles[3])
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.bubble_status and req.Sender() == Sender.Sender.client:
            self.log.info('request bubble_status command OK')
            res = response_packet_builder(Command.Command.bubble_status, error_code=0, data=RtlsService().get_bubbles().bubbles)
            # res = response_packet_builder(Command.Command.bubble_status, error_code=0, data=self.bubbles.bubbles)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.player_get and req.Sender() == Sender.Sender.client:
            self.log.info('request player_get command OK')
            res = response_packet_builder(Command.Command.player_get, error_code=0, data=self.user)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.player_status and req.Sender() == Sender.Sender.client:
            self.log.info('request player_status command OK')
            res = response_packet_builder(Command.Command.player_status, error_code=0, data=self.players.players)
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.game_ready and req.Sender() == Sender.Sender.client:
            self.log.info('request game_ready command OK')
            self.user.status = player_model.PlayerStatus.ready
            for p in self.players.players:
                if p.uid == self.user.uid:
                    p.status = player_model.PlayerStatus.ready
            res = response_packet_builder(Command.Command.game_ready, error_code=0) 
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.game_start and req.Sender() == Sender.Sender.client:
            self.log.info('request game_start command OK')
            self.user.status = player_model.PlayerStatus.game
            for p in self.players.players:
                p.status = player_model.PlayerStatus.game
            res = response_packet_builder(Command.Command.game_start, error_code=0) 
            self.transport.write(bytes(res))
        elif req.Command() == Command.Command.game_finish and req.Sender() == Sender.Sender.client:
            self.log.info('request game_finish command OK')
            self.user.status = player_model.PlayerStatus.idle
            for p in self.players.players:
                p.status = player_model.PlayerStatus.idle
            res = response_packet_builder(Command.Command.game_finish, error_code=0) 
            self.transport.write(bytes(res))
        else:
            self.log.warn('request wrong command')
        self.log.info('response lenth: {}'.format(len(res)))
        self.log.debug('response data: {}'.format(str(res)))

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

    BULLET_MAX = 5
    FRAME = 60
    GYRO_Y_THRESHOLD = -5000
    RELOAD_TIME_OFFSET = 1.5

    prev_zr = 0
    reload_time = time.time()

    @classmethod
    def run_ping_task(cls, users, players, bubbles):
        cls.log.info('ping task: {}'.format(datetime.now()))
        cls.log.info(str(players))
        # cls.log.info(str(bubbles))
        # cls.log.info(str(RtlsService().get_bubbles()))
        for u in users.values():
            req = request_packet_builder(Command.Command.ping, Sender.Sender.server)
            cls.log.debug(str(req))
            u.transport.write(bytes(req))

            res = response_packet_builder(Command.Command.bubble_status, error_code=0, data=RtlsService().get_bubbles().bubbles)
            u.transport.write(bytes(res))


    @classmethod
    def run_joycon_task(cls, users):
        cls.log.debug('joycon task: {}'.format(datetime.now()))
        left = JoyconService().get_status_left()
        right = JoyconService().get_status_right()
        if left and right:
            joycon = joycon_model.Joycon(
                right_y=right['buttons']['right']['y'],
                right_x=right['buttons']['right']['x'],
                right_a=right['buttons']['right']['a'],
                right_b=right['buttons']['right']['b'],
                right_r=right['buttons']['right']['r'],
                right_zr=right['buttons']['right']['zr'],
                right_horizontal=right['analog-sticks']['right']['horizontal'],
                right_vertical=right['analog-sticks']['right']['vertical'],
                right_accel_x=right['accel']['x'],
                right_accel_y=right['accel']['y'],
                right_accel_z=right['accel']['z'],
                right_gyro_x=right['gyro']['x'],
                right_gyro_y=right['gyro']['y'],
                right_gyro_z=right['gyro']['z'],
                right_battery_charging=right['battery']['charging'],
                right_battery_level=right['battery']['level'],
                right_home=right['buttons']['shared']['home'],

                left_down=left['buttons']['left']['down'],
                left_up=left['buttons']['left']['up'],
                left_right=left['buttons']['left']['right'],
                left_left=left['buttons']['left']['left'],
                left_l=left['buttons']['left']['l'],
                left_zl=left['buttons']['left']['zl'],
                left_horizontal=left['analog-sticks']['left']['horizontal'],
                left_vertical=left['analog-sticks']['left']['vertical'],
                left_accel_x=left['accel']['x'],
                left_accel_y=left['accel']['y'],
                left_accel_z=left['accel']['z'],
                left_gyro_x=left['gyro']['x'],
                left_gyro_y=left['gyro']['y'],
                left_gyro_z=left['gyro']['z'],
                left_battery_charging=left['battery']['charging'],
                left_battery_level=left['battery']['level']
            )
            for u in users.values():
                req = request_packet_builder(Command.Command.joycon, Sender.Sender.server, joycon)
                cls.log.debug(str(req))
                u.transport.write(bytes(req))
        else:
            cls.log.error('check paring joycon left: {}, right: {}'.format(left, right))

    @classmethod
    def run_joycon_event_task(cls, users):
        cls.log.debug('joycon event task: {}'.format(datetime.now()))
        left = JoyconService().get_status_left()
        right = JoyconService().get_status_right()
        if left and right:
            if right['gyro']['y'] < cls.GYRO_Y_THRESHOLD and (time.time() - cls.reload_time) > cls.RELOAD_TIME_OFFSET:
                cls.reload_time = time.time()
                cls.log.info('reload event')
                JoyconService().set_rumble_right(1.2, 0.3)
                JoyconService().set_rumble_left(0.5, 0.5)
                for u in users.values():
                    req = request_packet_builder(Command.Command.reload, Sender.Sender.server)
                    cls.log.debug(str(req))
                    u.transport.write(bytes(req))
            if right['buttons']['right']['zr'] == 1 and cls.prev_zr == 0:
                cls.log.info('shoot event')
                JoyconService().set_rumble_right(1.2, 0.3)
                JoyconService().set_rumble_left(0.5, 0.5)
                for u in users.values():
                    req = request_packet_builder(Command.Command.shoot, Sender.Sender.server)
                    cls.log.debug(str(req))
                    u.transport.write(bytes(req))
            if right['buttons']['right']['zr'] == 0 and cls.prev_zr == 1:
                cls.log.info('shoot release event')
                for u in users.values():
                    req = request_packet_builder(Command.Command.shoot_release, Sender.Sender.server)
                    cls.log.debug(str(req))
                    u.transport.write(bytes(req))
            cls.prev_zr = right['buttons']['right']['zr']
        else:
            print('disconnected')
            if JoyconService().set_paring_left():
                print('paired left')
            if JoyconService().set_paring_right():
                print('paired right')


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
@click.option('--rtls', default='192.168.40.254:9999', type=click.STRING, required=True, help='set rtls host:port(default: 192.168.40.254:9999)')
@click.option('--joycon', is_flag=True, help='get status of joycon(left/right)')
def main(port, ping, log_level, rtls, joycon):
    log = Logger('MainThread')
    predicate = LogLevelFilterPredicate(defaultLogLevel=LOG_LEVELS.get(log_level))
    observer = FilteringLogObserver(textFileLogObserver(outFile=sys.stdout), [predicate])
    observer._encoding = 'utf-8'
    globalLogPublisher.addObserver(observer)

    JoyconService()

    ep = endpoints.TCP4ServerEndpoint(reactor, port)
    ef = EchoFactory()
    ep.listen(ef)

    if ping:
        loop_ping = task.LoopingCall(ScheduleTask.run_ping_task, ef.users, ef.players, ef.bubbles)
        loop_ping_deferred = loop_ping.start(ping, False)
        loop_ping_deferred.addCallback(ScheduleTask.cbLoopDone)
        loop_ping_deferred.addErrback(ScheduleTask.ebLoopFailed)

    if joycon:
        loop_joycon = task.LoopingCall(ScheduleTask.run_joycon_task, ef.users)
        loop_joycon_deferred = loop_joycon.start(0.1, False)
        loop_joycon_deferred.addCallback(ScheduleTask.cbLoopDone)
        loop_joycon_deferred.addErrback(ScheduleTask.ebLoopFailed)

    loop_joycon_event = task.LoopingCall(ScheduleTask.run_joycon_event_task, ef.users)
    loop_joycon_event_deferred = loop_joycon_event.start(0.1, False)
    loop_joycon_event_deferred.addCallback(ScheduleTask.cbLoopDone)
    loop_joycon_event_deferred.addErrback(ScheduleTask.ebLoopFailed)

    log.info('Let\'s go ANTIFRAGILE')
    rhost, rport = rtls.split(':')
    reactor.listenUDP(0, RtlsProtocol(rhost, int(rport)))
    reactor.run()

if __name__ == '__main__':
    main()

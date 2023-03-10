# -*- coding: utf-8 -*-

import time
import flatbuffers
from fbs.pilot import Request, Response, Command, Player, Players, Sender, PlayerStatus, Bubble, Bubbles, BubbleType, Vec2
from typing import List, Optional, Dict, Any


def request_packet_builder(command: Command.Command, sender: Sender.Sender, data: Optional[Any] = None) -> bytes:
    builder = flatbuffers.Builder(0)
    timestamp = int(time.time() * 1000)
    data_pos: int = 0
    if command == Command.Command.welcome:
        pass
    elif command == Command.Command.ping:
        pass
    elif command == Command.Command.player_status:
        Players.PlayersStartPlayersVector(builder, 4)
        for i in range(4):
            username = builder.CreateString('player {}'.format(i+1))
            image_url = builder.CreateString('image url {}'.format(i+1))
            Player.PlayerStart(builder)
            Player.PlayerAddUid(builder, i+1)
            Player.PlayerAddUsername(builder, username)
            Player.PlayerAddImageUrl(builder, image_url)
            Player.PlayerAddScore(builder, 0)
            Player.PlayerAddStatus(builder, PlayerStatus.PlayerStatus.idle)
            p = Player.PlayerEnd(builder)
            builder.PrependUOffsetTRelative(p)
        players = builder.EndVector()
    else:
        pass

    Request.RequestStart(builder)
    Request.RequestAddTimestamp(builder, timestamp)
    Request.RequestAddCommand(builder, command)
    Request.RequestAddSender(builder, sender)

    Request.RequestAddData(builder, data_pos)

    request_pos = Request.RequestEnd(builder)

    builder.Finish(request_pos)

    return builder.Output()


def response_packet_builder(command: Command.Command, error_code: int = 0, data: Optional[Any] = None) -> bytes:
    builder = flatbuffers.Builder(0)
    timestamp = int(time.time() * 1000)
    data_pos: int = 0
    if command == Command.Command.welcome:
        username = builder.CreateString(data.username)
        image_url = builder.CreateString(data.image_url)
        Player.PlayerStart(builder)
        Player.PlayerAddUid(builder, data.uid)
        Player.PlayerAddUsername(builder, username)
        Player.PlayerAddImageUrl(builder, image_url)
        Player.PlayerAddScore(builder, data.score)
        Player.PlayerAddStatus(builder, data.status)
        data_pos = Player.PlayerEnd(builder)
    elif command == Command.Command.ping:
        pass
    elif command == Command.Command.bubble_get:
        Bubble.BubbleStart(builder)
        Bubble.BubbleAddUid(builder, data.uid)
        pos_cur = Vec2.CreateVec2(builder, data.pos_cur.x, data.pos_cur.y)
        Bubble.BubbleAddPosCur(builder, pos_cur)
        pos_target = Vec2.CreateVec2(builder, data.pos_target.x, data.pos_target.y)
        Bubble.BubbleAddPosTarget(builder, pos_target)
        Bubble.BubbleAddSpeed(builder, data.speed)
        Bubble.BubbleAddType(builder, data.type)
        data_pos = Bubble.BubbleEnd(builder)
    elif command == Command.Command.bubble_status:
        bubbles_list = []
        for d in data:
            Bubble.BubbleStart(builder)
            Bubble.BubbleAddUid(builder, d.uid)
            pos_cur = Vec2.CreateVec2(builder, d.pos_cur.x, d.pos_cur.y)
            Bubble.BubbleAddPosCur(builder, pos_cur)
            pos_target = Vec2.CreateVec2(builder, d.pos_target.x, d.pos_target.y)
            Bubble.BubbleAddPosTarget(builder, pos_target)
            Bubble.BubbleAddSpeed(builder, d.speed)
            Bubble.BubbleAddType(builder, d.type)
            bubbles_list.append(Bubble.BubbleEnd(builder))
        Bubbles.BubblesStartBubblesVector(builder, len(bubbles_list))
        for b in bubbles_list:
            builder.PrependUOffsetTRelative(b)
        vector_pos = builder.EndVector()
        Bubbles.BubblesStart(builder)
        Bubbles.BubblesAddBubbles(builder, vector_pos)
        data_pos = Bubbles.BubblesEnd(builder)
    else:
        pass

    Response.ResponseStart(builder)
    Response.ResponseAddTimestamp(builder, timestamp)
    Response.ResponseAddCommand(builder, command)
    Response.ResponseAddErrorCode(builder, error_code)

    Response.ResponseAddData(builder, data_pos)

    response_pos = Response.ResponseEnd(builder)

    builder.Finish(response_pos)

    return builder.Output()


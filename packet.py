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
    elif command == Command.Command.bubble_get:
        pass
    elif command == Command.Command.bubble_status:
        pass
    elif command == Command.Command.player_get:
        pass
    elif command == Command.Command.player_status:
        pass
    else:
        pass

    Request.RequestStart(builder)
    Request.RequestAddTimestamp(builder, timestamp)
    Request.RequestAddCommand(builder, command)
    Request.RequestAddSender(builder, sender)

    Request.RequestAddData(builder, data_pos)

    request_pos = Request.RequestEnd(builder)

    builder.Finish(request_pos)

    res_body = builder.Output()
    return bytearray((len(res_body)+2).to_bytes(2, 'big')+res_body)



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
    elif command == Command.Command.player_get:
        username = builder.CreateString(data.username)
        image_url = builder.CreateString(data.image_url)
        Player.PlayerStart(builder)
        Player.PlayerAddUid(builder, data.uid)
        Player.PlayerAddUsername(builder, username)
        Player.PlayerAddImageUrl(builder, image_url)
        Player.PlayerAddScore(builder, data.score)
        Player.PlayerAddStatus(builder, data.status)
        data_pos = Player.PlayerEnd(builder)
    elif command == Command.Command.player_status:
        players_list = []
        for d in data:
            username = builder.CreateString(d.username)
            image_url = builder.CreateString(d.image_url)
            Player.PlayerStart(builder)
            Player.PlayerAddUid(builder, d.uid)
            Player.PlayerAddUsername(builder, username)
            Player.PlayerAddImageUrl(builder, image_url)
            Player.PlayerAddScore(builder, d.score)
            Player.PlayerAddStatus(builder, d.status)
            players_list.append(Player.PlayerEnd(builder))
        Players.PlayersStartPlayersVector(builder, len(players_list))
        for p in players_list:
            builder.PrependUOffsetTRelative(p)
        vector_pos = builder.EndVector()
        Players.PlayersStart(builder)
        Players.PlayersAddPlayers(builder, vector_pos)
        data_pos = Players.PlayersEnd(builder)
    else:
        pass

    Response.ResponseStart(builder)
    Response.ResponseAddTimestamp(builder, timestamp)
    Response.ResponseAddCommand(builder, command)
    Response.ResponseAddErrorCode(builder, error_code)

    Response.ResponseAddData(builder, data_pos)

    response_pos = Response.ResponseEnd(builder)

    builder.Finish(response_pos)

    res_body = builder.Output()
    return bytearray((len(res_body)+2).to_bytes(2, 'big')+res_body)

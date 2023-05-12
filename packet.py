# -*- coding: utf-8 -*-

import time
import flatbuffers
from fbs.pilot import Request, Response, Command, Player, Players, Sender, PlayerStatus, Bubble, Bubbles, BubbleType, Vec2, Joycon
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
        pass
    elif command == Command.Command.player_get:
        pass
    elif command == Command.Command.player_status:
        pass
    elif command == Command.Command.joycon:
        Joycon.JoyconStart(builder)
        Joycon.JoyconAddRightY(builder, data.right_y)
        Joycon.JoyconAddRightX(builder, data.right_x)
        Joycon.JoyconAddRightA(builder, data.right_a)
        Joycon.JoyconAddRightB(builder, data.right_b)
        Joycon.JoyconAddRightR(builder, data.right_r)
        Joycon.JoyconAddRightZr(builder, data.right_zr)
        Joycon.JoyconAddRightHorizontal(builder, data.right_horizontal)
        Joycon.JoyconAddRightVertical(builder, data.right_vertical)
        Joycon.JoyconAddRightAccelX(builder, data.right_accel_x)
        Joycon.JoyconAddRightAccelY(builder, data.right_accel_y)
        Joycon.JoyconAddRightAccelZ(builder, data.right_accel_z)
        Joycon.JoyconAddRightGyroX(builder, data.right_gyro_x)
        Joycon.JoyconAddRightGyroY(builder, data.right_gyro_y)
        Joycon.JoyconAddRightGyroZ(builder, data.right_gyro_z)
        Joycon.JoyconAddRightBatteryCharging(builder, data.right_battery_charging)
        Joycon.JoyconAddRightBatteryLevel(builder, data.right_battery_level)
        Joycon.JoyconAddRightHome(builder, data.right_home)

        Joycon.JoyconAddLeftDown(builder, data.left_down)
        Joycon.JoyconAddLeftUp(builder, data.left_up)
        Joycon.JoyconAddLeftRight(builder, data.left_right)
        Joycon.JoyconAddLeftLeft(builder, data.left_left)
        Joycon.JoyconAddLeftL(builder, data.left_l)
        Joycon.JoyconAddLeftZl(builder, data.left_zl)
        Joycon.JoyconAddLeftHorizontal(builder, data.left_horizontal)
        Joycon.JoyconAddLeftVertical(builder, data.left_vertical)
        Joycon.JoyconAddLeftAccelX(builder, data.left_accel_x)
        Joycon.JoyconAddLeftAccelY(builder, data.left_accel_y)
        Joycon.JoyconAddLeftAccelZ(builder, data.left_accel_z)
        Joycon.JoyconAddLeftGyroX(builder, data.left_gyro_x)
        Joycon.JoyconAddLeftGyroY(builder, data.left_gyro_y)
        Joycon.JoyconAddLeftGyroZ(builder, data.left_gyro_z)
        Joycon.JoyconAddLeftBatteryCharging(builder, data.left_battery_charging)
        Joycon.JoyconAddLeftBatteryLevel(builder, data.left_battery_level)

        data_pos = Joycon.JoyconEnd(builder)
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
        pass
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

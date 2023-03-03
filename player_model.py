# -*- coding: utf-8 -*-

from pydantic import BaseModel
from typing import List, Optional
from enum import IntEnum

import flatbuffers
import fbs.pilot.Player


class PlayerStatus(IntEnum):
    idle = 0
    ready = 1
    game = 2

class Player(BaseModel):
    uid: int
    username: str
    image_url: str
    score: int
    status: PlayerStatus

    def to_fbs(self):
        builder = flatbuffers.Builder(0)
        username = builder.CreateString(self.username)
        image_url = builder.CreateString(self.image_url)
        fbs.pilot.Player.PlayerStart(builder)
        fbs.pilot.Player.PlayerAddUid(builder, self.uid)
        fbs.pilot.Player.PlayerAddUsername(builder, username)
        fbs.pilot.Player.PlayerAddImageUrl(builder, image_url)
        fbs.pilot.Player.PlayerAddScore(builder, self.score)
        fbs.pilot.Player.PlayerAddStatus(builder, self.status)
        player = fbs.pilot.Player.PlayerEnd(builder)
        builder.Finish(player)
        return builder.Output()

class Players(BaseModel):
    players: Optional[List[Player]] = []

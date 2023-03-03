# -*- coding: utf-8 -*-

from pydantic import BaseModel
from typing import List, Optional
from enum import IntEnum

import flatbuffers
import fbs.pilot.Bubble


class BubbleType(IntEnum):
    normal = 0
    event = 1

class Vec2(BaseModel):
    x: float
    y: float

class Bubble(BaseModel):
    uid: int
    pos_cur: Vec2
    pos_target: Vec2
    speed: float
    type: BubbleType

    def to_fbs(self):
        builder = flatbuffers.Builder(0)
        fbs.pilot.Bubble.BubbleStart(builder)
        fbs.pilot.Bubble.BubbleAddUid(builder, self.uid)
        fbs.pilot.Bubble.BubbleAddPosCur(builder, self.pos_cur)
        fbs.pilot.Bubble.BubbleAddPosTarget(builder, self.pos_target)
        fbs.pilot.Bubble.BubbleAddSpeed(builder, self.speed)
        fbs.pilot.Bubble.BubbleAddType(builder, self.type)
        bubble = fbs.pilot.Bubble.BubbleEnd(builder)
        builder.Finish(bubble)
        return builder.Output()

class Bubbles(BaseModel):
    bubbles: Optional[List[Bubble]] = []

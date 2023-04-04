# -*- coding: utf-8 -*-

import struct
from dataclasses import dataclass

from ._byteable import _Byteable
from .header import Header


@dataclass(frozen=True)
class __PositionNoti:
    timestamp: int
    position_x: int
    position_y: int
    acc_x: int
    acc_y: int
    head_angle: int


class PositionNoti(_Byteable, __PositionNoti):
    DEFAULT_HEADER = Header.PK_POSITION_NOTI
    LISTABLE = False
    BYTES_LENGTH = 18

    __STRUCT = struct.Struct('<Qhhhhh')

    __bytes: bytes = bytes()


    def to_bytes(self):
        if len(self.__bytes) == 0:
            self.__bytes = self.__STRUCT.pack(
                    self.timestamp,
                    self.position_x,
                    self.position_y,
                    self.acc_x,
                    self.acc_y,
                    self.head_angle)

        return self.__bytes


    def from_bytes(source):
        (
                timestamp,
                position_x,
                position_y,
                acc_x,
                acc_y,
                head_angle) = PositionNoti.__STRUCT.unpack(source)

        result = PositionNoti(
                timestamp=timestamp,
                position_x=position_x,
                position_y=position_y,
                acc_x=acc_x,
                acc_y=acc_y,
                head_angle=head_angle)
        result.__bytes = source

        return result


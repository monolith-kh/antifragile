# -*- coding: utf-8 -*-

import struct
from dataclasses import dataclass

from ._byteable import _Byteable


@dataclass(frozen=True)
class __PositionInfo:
    object_number: int
    timestamp: int
    position_x: int
    position_y: int
    position_z: int
    rotation_x: int
    rotation_y: int
    rotation_z: int


class PositionInfo(_Byteable, __PositionInfo):
    BYTES_LENGTH = 28

    __STRUCT = struct.Struct('<HQiiihhh')

    __bytes: bytes = bytes()


    def to_bytes(self):
        if len(self.__bytes) == 0:
            self.__bytes = PositionInfo.__STRUCT.pack(
                    self.object_number,
                    self.timestamp,
                    self.position_x,
                    self.position_y,
                    self.position_z,
                    self.rotation_x,
                    self.rotation_y,
                    self.rotation_z)

        return self.__bytes


    def from_bytes(source):
        (
                object_number,
                timestamp,
                position_x,
                position_y,
                position_z,
                rotation_x,
                rotation_y,
                rotation_z) = PositionInfo.__STRUCT.unpack(source)

        result = PositionInfo(
                object_number=object_number,
                timestamp=timestamp,
                position_x=position_x,
                position_y=position_y,
                position_z=position_z,
                rotation_x=rotation_x,
                rotation_y=rotation_y,
                rotation_z=rotation_z)
                
        result.__bytes = source
        return result


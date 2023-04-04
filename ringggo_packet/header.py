# -*- coding: utf-8 -*-

import struct
from dataclasses import dataclass

from ._byteable import _Byteable


@dataclass(frozen=True)
class __Header:
    code: int
    sender: int
    length: int
    car_number: int


class Header(_Byteable, __Header):
    BYTES_LENGTH = 8

    PK_POSITION_NOTI        = 0xD1
    PK_POSITION_REMOVE      = 0xD2
    PK_POSITION_LISTEN      = 0xD3
    PK_POSITION_LISTEN_STOP = 0xD4
    PK_POSITION_OBJECTS     = 0xD5
    PK_POSITION_RELAY       = 0xD6
    PK_POSITION_RELAY_STOP  = 0xD7
    
    SENDER_SERVER   = 3
    SENDER_ADMIN    = 4
    SENDER_CAR      = 6
    SENDER_RTLS     = 7
    
    __STRUCT = struct.Struct('<BBHHxx')

    __bytes: bytes = bytes()


    def to_bytes(self):
        if len(self.__bytes) == 0:
            self.__bytes = self.__STRUCT.pack(
                    self.code,
                    self.sender,
                    self.length,
                    self.car_number)

        return self.__bytes


    def from_bytes(source):
        (
                code,
                sender,
                length,
                car_number) = Header.__STRUCT.unpack(source)
        result = Header(
                code=code,
                sender=sender,
                length=length,
                car_number=car_number)
        result.__bytes = source

        return result


# -*- coding: utf-8 -*-

import operator
from dataclasses import dataclass
from functools import reduce

from ._byteable import _Byteable
from .header import Header
from .position_object import PositionObject
from .position_noti import PositionNoti


@dataclass(frozen=True)
class __Packet:
    header: Header
    body: bytes


class Packet(_Byteable, __Packet):
    BYTES_LENGTH = 8

    __bytes: bytes = bytes()

    __inited = False

    __class_to_header_map = {}
    __header_to_class_map = {}
    __header_to_defaultbody_map = {}


    @staticmethod
    def __init():
        if not Packet.__inited:
            Packet.__inited = True

            Packet.register_body(PositionObject)
            Packet.register_body(PositionNoti)


    @staticmethod
    def register_body(body: _Byteable):
        Packet.__class_to_header_map[body] = body.DEFAULT_HEADER
        Packet.__header_to_class_map[body.DEFAULT_HEADER] = body
        if body.LISTABLE:
            Packet.__header_to_defaultbody_map[body.DEFAULT_HEADER] = []
        else:
            Packet.__header_to_defaultbody_map[body.DEFAULT_HEADER] = {}


    def __init__(self, sender=Header.SENDER_SERVER, header=None, body=_Byteable(), code=None, car_number=0):
        Packet.__init()

        body_bytes = bytes()
        if isinstance(body, bytes):
            body_bytes = body
        elif isinstance(body, list):
            body_bytes = reduce(operator.concat, map(lambda value: value.to_bytes(), body), b'')
        else:
            body_bytes = body.to_bytes()


        if header == None:
            if code == None:
                sample = body
                if isinstance(body, list) and len(body) > 0:
                    sample = sample[0]
    
                code = self.__class_to_header_map.get(type(sample))
                if code == None:
                    print(self.__class_to_header_map)
                    raise
    
    
            header = Header(
                    code=code,
                    sender=sender,
                    length=Header.BYTES_LENGTH + len(body_bytes),
                    car_number=car_number)

        self.__bytes = header.to_bytes() + body_bytes
        self.BYTES_LENGTH = len(self.__bytes)
        
        super().__init__(header=header, body=body)


    def to_bytes(self):
        return self.__bytes


    def from_bytes(source, body_convert=True):
        Packet.__init()

        header_bytes = source[0:8]
        body_bytes = source[8:]

        header = Header.from_bytes(header_bytes)
        body_length = header.length

        body = None
        if body_convert:
            body_class = Packet.__header_to_class_map.get(header.code, _Byteable)
            body = Packet.__header_to_defaultbody_map.get(header.code, {}).copy()

            if isinstance(body, list):
                objects_count = int(body_length / body_class.BYTES_LENGTH)
                for idx in range(0, objects_count):
                    start_pos = idx * body_class.BYTES_LENGTH
                    end_pos = (idx + 1) * body_class.BYTES_LENGTH
                    object_bytes = body_bytes[start_pos:end_pos]
                    body.append(body_class.from_bytes(object_bytes))
            else:
                body = body_class.from_bytes(body_bytes)
        else:
            body = body_bytes[0:body_length]

        result = Packet(
                header=header,
                body=body)
        result.__bytes = source
        result.BYTES_LENGTH = len(source)

        return result


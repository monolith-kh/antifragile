# -*- coding: utf-8 -*-

class _Byteable:
    DEFAULT_HEADER = None
    BYTES_LENGTH = 0
    LISTABLE = False


    def from_bytes(source):
        return _Byteable()


    def to_bytes(self):
        return bytes()

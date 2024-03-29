# automatically generated by the FlatBuffers compiler, do not modify

# namespace: pilot

import flatbuffers
from flatbuffers.compat import import_numpy
np = import_numpy()

class Player(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = Player()
        x.Init(buf, n + offset)
        return x

    @classmethod
    def GetRootAsPlayer(cls, buf, offset=0):
        """This method is deprecated. Please switch to GetRootAs."""
        return cls.GetRootAs(buf, offset)
    # Player
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # Player
    def Uid(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0

    # Player
    def Username(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

    # Player
    def ImageUrl(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(8))
        if o != 0:
            return self._tab.String(o + self._tab.Pos)
        return None

    # Player
    def Score(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(10))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0

    # Player
    def Status(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(12))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int8Flags, o + self._tab.Pos)
        return 0

def PlayerStart(builder): builder.StartObject(5)
def Start(builder):
    return PlayerStart(builder)
def PlayerAddUid(builder, uid): builder.PrependInt32Slot(0, uid, 0)
def AddUid(builder, uid):
    return PlayerAddUid(builder, uid)
def PlayerAddUsername(builder, username): builder.PrependUOffsetTRelativeSlot(1, flatbuffers.number_types.UOffsetTFlags.py_type(username), 0)
def AddUsername(builder, username):
    return PlayerAddUsername(builder, username)
def PlayerAddImageUrl(builder, imageUrl): builder.PrependUOffsetTRelativeSlot(2, flatbuffers.number_types.UOffsetTFlags.py_type(imageUrl), 0)
def AddImageUrl(builder, imageUrl):
    return PlayerAddImageUrl(builder, imageUrl)
def PlayerAddScore(builder, score): builder.PrependInt32Slot(3, score, 0)
def AddScore(builder, score):
    return PlayerAddScore(builder, score)
def PlayerAddStatus(builder, status): builder.PrependInt8Slot(4, status, 0)
def AddStatus(builder, status):
    return PlayerAddStatus(builder, status)
def PlayerEnd(builder): return builder.EndObject()
def End(builder):
    return PlayerEnd(builder)
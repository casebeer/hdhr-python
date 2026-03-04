'''
Based on
https://github.com/Silicondust/libhdhomerun/blob/b0e5d5f5c8e2bf37dea34beb014e08ebb598ebf6/hdhomerun_pkt.h
'''
import struct
import zlib

from dataclasses import dataclass, field
from enum import Enum
from typing import List

import logging
logger = logging.getLogger(__name__)


class PacketType(Enum):
    DISCOVER_REQ = 0x0002
    DISCOVER_RPY = 0x0003
    GETSET_REQ = 0x0004
    GETSET_RPY = 0x0005
    UPGRADE_REQ = 0x0006
    UPGRADE_RPY = 0x0007

class PayloadTag(Enum):
    DEVICE_TYPE = 0x01
    DEVICE_ID = 0x02
    GETSET_NAME = 0x03
    GETSET_VALUE = 0x04
    GETSET_LOCKKEY = 0x15
    ERROR_MESSAGE = 0x05
    TUNER_COUNT = 0x10
    LINEUP_URL = 0x27
    STORAGE_URL = 0x28
    DEVICE_AUTH_BIN_DEPRECATED = 0x29
    BASE_URL = 0x2A
    DEVICE_AUTH_STR = 0x2B
    STORAGE_ID = 0x2C
    MULTI_TYPE = 0x2D

class DeviceType(Enum):
    TUNER = bytes.fromhex("00000001")
    STORAGE = bytes.fromhex("00000005")
    WILDCARD = bytes.fromhex("FFFFFFFF")

class DeviceId(Enum):
    WILDCARD = bytes.fromhex("FFFFFFFF")

@dataclass
class PayloadField:
    '''
    uint8_t tag
    1 or 2 bytes custom format length
    <length> bytes NUL terminated string
    '''
    tag: PayloadTag
    value: bytes
    length: int = 0

    def getTotalLength(self):
        # self.length is len(value) only
        fieldLength = self.length + (3 if self.length > 127 else 2)
        return fieldLength

    @classmethod
    def parse(cls, data: bytes):
        tag, = struct.unpack('B', data[0:1])
        length = cls.readLength(data[1:3])

        valueOffset = 2 if length <= 127 else 3

        value = data[valueOffset:valueOffset + length]
        logger.debug(f"PayloadField(0x{tag:x}, {length}, {value})")

        return cls(
            tag=PayloadTag(tag),
            length=length, # length of value only, not whole field
            value=value,
        )

    def unparse(self):
        valueLength = len(self.value)
        lengthLength = 2 if valueLength + 2 > 127 else 1
        fieldLength = valueLength + lengthLength + 1
        data = bytearray(fieldLength)
        data[0:1] = struct.pack('B', self.tag.value)
        data[1:1 + lengthLength] = PayloadField.writeLength(valueLength)
        data[1 + lengthLength:1 + lengthLength + valueLength] = self.value
        return data

    @staticmethod
    def readLength(data: bytes):
        '''
        Read 1 or 2 bytes per custom length format
        '''
        if data[0] & 0x80 > 0:
            # two byte length field
            length = \
                (data[0] & 0x7f) |\
                (data[1] << 7)
        else:
            # one byte length field
            length = data[0] & 0x7f
        return length

    @staticmethod
    def writeLength(length):
        if length > 127:
            # two byte length field
            return struct.pack('BB', (length & 0x7f) | 0x80, (length >> 7) & 0xff)
        else:
            # one byte length field
            return struct.pack('B', length & 0x7f)


@dataclass
class Payload:
    fields: list = field(default_factory=list)

    @classmethod
    def parse(cls, data:bytes):
        offset = 0
        fields = []

        while offset < len(data):
            field = PayloadField.parse(data[offset:])
            fields.append(field)
            offset += field.getTotalLength()
            logger.debug(f"Payload fields offset += {field.getTotalLength()}")

        return cls(fields=fields)

    def unparse(self):
        data = bytearray()
        for field in self.fields:
            data.extend(field.unparse())
        return data

@dataclass
class Packet:
    packetType: PacketType
    payload: Payload
    payloadLength: int = 0
    crc: int = 0
    #computedCrc: int = 0

    @classmethod
    def parse(cls, data):
        packetType, payloadLength = struct.unpack('>HH', data[:4])
        # 2x2 bytes header + payloadLength
        crcOffset = payloadLength + 4

        # n.b. docs say little-endian, TODO: verify
        crc, = struct.unpack('<I', data[crcOffset:crcOffset + 4])

        computedCrc = zlib.crc32(data[0:crcOffset])

        if computedCrc != crc:
            raise ValueError(
                f'Packet has invalid CRC: {crc}, expected {computedCrc}'
            )

        payloadBytes = data[4:4 + payloadLength]

        return cls(
            packetType=PacketType(packetType),
            payloadLength=payloadLength,
            payload=Payload.parse(payloadBytes),
            crc=crc,
        )

    def unparse(self):
        payloadBytes = self.payload.unparse()
        # compute payload length and packet CRC and return binary data
        payloadLength = len(payloadBytes)

        packet = bytearray(payloadLength + 8)
        packet[0:2] = struct.pack('>H', self.packetType.value)
        packet[2:4] = struct.pack('>H', payloadLength)
        packet[4:payloadLength + 4] = payloadBytes

        packetCrc = zlib.crc32(packet[0:payloadLength + 4])
        # hdhomerun_pkt.h says "Ethernet style 32-bit CRC)"
        # but also little-endian, which may be contradictory
        packet[payloadLength + 4:payloadLength + 8] =\
        struct.pack('<I', packetCrc)

        return packet


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    #packet = unparsePacket(PacketType.GETSET_REQ.value, bytes())
    packet = Packet(packetType=PacketType.GETSET_REQ, payload=Payload()).unparse()
    print(packet.hex())
    print(Packet.parse(packet))
    print(Packet.parse(packet).unparse().hex())

    def testLength(length):
        lengthBytes = PayloadField.writeLength(length)
        readLength = PayloadField.readLength(lengthBytes)
        print(f"length {length} => {lengthBytes.hex()} => {readLength}")
        assert length == readLength

    testLength(120)
    # 250d = 0xfa00
    # struct.pack('>H', (250 & 0xff80) >> 7).hex() = "0001"
    # struct.pack('>H', (250 & 0x7f)).hex()        = "007a"
    # so 250 should become fa01
    testLength(250)

    payload = Payload()
    payload.fields = [ PayloadField(tag=tag, value=bytes("12345\0", encoding='ascii')) for tag in PayloadTag ]

    payloadBytes = payload.unparse()
    parsedPayload = Payload.parse(payloadBytes)

    print(payload)
    print(payloadBytes.hex())
    print(parsedPayload)

    # responses back from hdhr extend
    # 0005002205204552524f523a206d616c666f726d65642067657473657420726571756573740037494141
    # 0005001a030d2f7379732f76657273696f6e000409323032353036323300053b1257
    responses = [
        "0005002205204552524f523a206d616c666f726d65642067657473657420726571756573740037494141",
        "0005001a030d2f7379732f76657273696f6e000409323032353036323300053b1257",
    ]

    for response in [bytes.fromhex(r) for r in responses]:
        print(response.hex())

        packet = Packet.parse(response)

        print(packet)


import logging
import socket
import asyncio
import pprint
import struct
import os

import hdhr

logger = logging.getLogger(__name__)

DISCOVER_IPV6_LINKLOCAL_MULTICAST = "ff02::176"
DISCOVER_IPV6_SITELOCAL_MULTICAST = "ff05::176"

DISCOVER_IPV4_BROADCAST = "255.255.255.255"

BIND_ADDRESS = "0.0.0.0"
BIND_PORT = 65001

DEFAULT_TARGET_ADDRESS = ""
TARGET_PORT = 65001

BUFFER_SIZE = 1460
ENCODING = "utf-8"

def processResponse(response):
    name = None
    value = None
    #print(response)
    responseFields = {}
    for field in response.payload.fields:
        if field.tag == hdhr.PayloadTag.GETSET_NAME:
            name = field.value[:-1].decode(ENCODING)
        elif field.tag == hdhr.PayloadTag.GETSET_VALUE:
            value = field.value[:-1].decode(ENCODING)
            #pprint.pprint({ name: value })
            responseFields[name] = value
            name, value = None, None
        elif field.tag == hdhr.PayloadTag.ERROR_MESSAGE:
            value = field.value[:-1].decode(ENCODING)
            logger.error(f"ERROR: {value}")
            responseFields[name]: value
            value = None
        elif field.tag == hdhr.PayloadTag.TUNER_COUNT:
            value, = struct.unpack('B', field.value)
            responseFields[field.tag.name] = value
        elif field.tag in (
            hdhr.PayloadTag.DEVICE_TYPE,
            hdhr.PayloadTag.MULTI_TYPE,
        ):
            value, = struct.unpack('>I', field.value)
            responseFields[field.tag.name] = value
        elif field.tag == hdhr.PayloadTag.DEVICE_ID:
            value = field.value.hex()
            responseFields[field.tag.name] = value
        elif field.tag in (
            hdhr.PayloadTag.DEVICE_AUTH_STR,
            hdhr.PayloadTag.BASE_URL,
            hdhr.PayloadTag.LINEUP_URL,
        ):
            logger.debug(f"Decoding value for field {field.tag.name}...")
            responseFields[field.tag.name] = field.value.decode(ENCODING)

        else:
            logger.error(f"UNHANDLED RESPONSE TAG: {field.tag.name}")
    return responseFields

class DiscoverProtocol(asyncio.DatagramProtocol):
    def datagram_received(self, data, addr):
        if data:
            print(f"Received {len(data)} bytes from {addr}")
            print(data.hex())
            packet = hdhr.Packet.parse(data)
            print(packet)

            # minimal discovery response contains
            # DEVICE_TYPE uint32_t and DEVICE_ID uint32_t fields
            # HDTC-US2 also provides fields
            #  - MULTI_TYPE uint32_t
            #  - DEVICE_AUTH_STR str, no NUL termination
            #  - TUNER_COUNT uint8_t
            #  - BASE_URL str, no NUL termination
            #  - LINEUP_URL str, no NUL termination
            # Additional fields with new tag numbers may be added in the future.
            # TODO: Fix parsing of unknown TAGs

            pprint.pprint(processResponse(packet))

        else:
            print("No data from {addr}")
    def connection_made(self, transport):
        self.transport = transport
        payload = hdhr.Payload(
            fields=[
                hdhr.PayloadField(
                    tag=hdhr.PayloadTag.DEVICE_TYPE,
                    value=hdhr.DeviceType.WILDCARD.value,
                ),
                hdhr.PayloadField(
                    tag=hdhr.PayloadTag.DEVICE_ID,
                    value=hdhr.DeviceId.WILDCARD.value,
                ),
            ]
        )

        packet = hdhr.Packet(
            packetType=hdhr.PacketType.DISCOVER_REQ,
            payload=payload,
        )

        print("Sending packet...")
        #self.transport.sendto(b"Hello, world")
        self.transport.sendto(packet.unparse())

async def main(host, port):
    loop = asyncio.get_running_loop()

    # discover protocol is a request/response to UDP 65001
    # requests can be sent to a unicast, multicast, or broadcast IP on port 65001
    # responses will be sent to the sender's IP at port 65001
    transport, protocol = await loop.create_datagram_endpoint(
        DiscoverProtocol,
        local_addr=(BIND_ADDRESS, BIND_PORT),
        remote_addr=(host, port),
    )

    try:
        await asyncio.sleep(300)
    finally:
        transport.close

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    host = os.environ.get('HOST', DEFAULT_TARGET_ADDRESS)
    port = int(os.environ.get('PORT', TARGET_PORT))

    asyncio.run(main(host, port))

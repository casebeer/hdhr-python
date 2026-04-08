
import logging
import socket
import asyncio
import pprint
import struct
import ipaddress
import os
import re

from . import hdhr

logger = logging.getLogger(__name__)

DISCOVER_IPV6_LINKLOCAL_MULTICAST = "ff02::176"
DISCOVER_IPV6_SITELOCAL_MULTICAST = "ff05::176"

IPV4_BROADCAST = "255.255.255.255"
IPV6_LINKLOCAL_MULTICAST_ALL_HOSTS = "ff02::1"

BIND_ADDRESS = "::"
BIND_PORT = 65001

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

    # add "hostname" field parsed from BASE_URL
    url = responseFields.get('BASE_URL')
    matches = re.match(r'\w+://([^:/]+)', url)

    if matches and len(matches.groups()) > 0:
        responseFields["hostname"] = matches.group(1)
    else:
        responseFields["hostname"] = None

    return responseFields

class UdpProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        super().__init__()
        self.transport = None
        self._receiveBuffer = asyncio.Queue() # OK outside async

    def datagram_received(self, data, addr):
        logging.debug(f'Got {len(data)} byte UDP packet from {addr}')
        self._receiveBuffer.put_nowait((data, addr)) # n.b. exception if Queue full

    def connection_made(self, transport):
        # ready to send packets
        self.transport = transport

    def close(self):
        '''
        Terminate the UDP listener

        Signal the recv() receive buffer reader method that no new data will arrive by playing a
        None sigil in the receive buffer. This is in lieu of direclty terminating the Queue with
        Queue.shutdown(), which is a Python 3.13+ feature.

        Once the recv() method gets the None sigil, it will terminate the async generator, call
        Queue.task_done() for the final item in the receive buffer, and thus allow the receive
        buffer's join() method (which controls our join() method) to return.
        '''
        logger.debug("Stopping UDP listener...")
        self.transport.close()
        # Python 3.13
        #self._receiveBuffer.shutdown() # immediate=False, so get()s can continue
        self._receiveBuffer.put_nowait(None) # sigil to shut down queue

    async def join(self):
        '''Wait for the receive buffer Queue to be terminated by close()'''
        return await self._receiveBuffer.join()

    async def recv(self, maxcount=0):
        '''
        Async generator yielding recieved UDP packets as they arrive

        Will not terminate unless close() is called or maxcount (default 0, no limit) packets have
        been yielded.
        '''
        count = 0
        while True:
            if maxcount != 0 and count >= maxcount:
                break
            item = await self._receiveBuffer.get()
            if item is None:
                self._receiveBuffer.task_done()
                break
            yield item
            self._receiveBuffer.task_done()
            count += 1

class DiscoverClient:
    def __init__(self, proto, transport, timeoutSeconds):
        '''Private __init__ call await DiscoverClient.create() instead'''
        self.proto = proto
        self.transport = transport
        self.timeoutSeconds = timeoutSeconds
        self.timeout = asyncio.get_running_loop().call_later(
            self.timeoutSeconds,
            self.proto.close,
        )
    @classmethod
    async def create(cls, bind_address=BIND_ADDRESS, bind_port=BIND_PORT, timeoutSeconds=1):
        '''
        Factory classmethod to return a DiscoverClient
        '''

        loop = asyncio.get_running_loop()

        assert socket.has_dualstack_ipv6()

        proto = UdpProtocol()

        # manually configure dual stack socket
        sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0) # disable V6ONLY flag
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) # allow v4 broadcast
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 64)

        # listen for incoming UDP packets
        sock.bind((bind_address, bind_port, 0, 0))

        transport, _ = await loop.create_datagram_endpoint(
            lambda: proto,
            sock=sock,
        )

        return cls(
            proto,
            transport,
            timeoutSeconds,
        )

    async def join(self):
        '''Wait for the UDP listener to terminate'''
        return await self.proto.join()

    def send(self, data: bytes, host: str, port: int):
        '''
        Send bytes via UDP to the specified host and port

        `host` will be resolved with getaddrinfo(), so DNS lookups will be performed.

        `host` may also be an IPv4 or IPv6 literal. IPv4 literals will be converted to IPv6
        mapped-IPv4 literals in ::ffff:0000:0000/32 for compatiblity with the dual-stack UDP socket.

        Note that since we are broadcasting to discover HDHomeRun devices, packets will be sent to
        ALL ADDRESSES RETURNED BY GETADDRINFO. That is, if there are multiple A and/or AAAA records
        for the hostname provided, ALL of the IPv4 and IPv6 addresses returned will get discovery
        packets.
        '''
        # dual stack DNS lookup
        addrInfo = socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM, family=socket.AF_UNSPEC)

        # send to all v4 or v6 addresses found
        for family, type, proto, canonname, sockaddr in addrInfo:
            if family == socket.AF_INET:
                v4, port = sockaddr
                # create mapped ipv4 address for sending on dualstack socket
                sockaddr = (f"::ffff:{v4}", port, 0, 0)

            logger.debug(f"Sending packet to {sockaddr}")
            self.transport.sendto(data, sockaddr)

    async def recv(self, maxcount=0):
        '''
        Async generator yielding received UDP packets as they arrive

        Will not terminate unless the close() method is called from another task (e.g. from
        a loop.call_later()) or maxcount (default 0, no limit) packets have been yielded.
        '''
        async for data, addr in self.proto.recv(maxcount=maxcount):
            yield data, addr

    async def discoverReplies(self, maxcount=0):
        '''
        Async generator yielding received Discover Protocol replies as they arrive

        Will not terminate unless the close() method is called from another task (e.g. from
        a loop.call_later()) or maxcount (default 0, no limit) packets have been yielded.
        '''
        async for data, addr in self.recv(maxcount=maxcount):
            if data:
                logger.info(f"Received {len(data)} bytes from {addr}")
                logger.debug(data.hex())
                packet = hdhr.Packet.parse(data)

                logger.info(f"{packet.packetType.name} packet with {len(packet.payload.fields)} fields")
                logger.debug(packet)

                # n.b. we will also hear our own discover REQUESTS on broadcast or ff02::1
                if packet.packetType == hdhr.PacketType.DISCOVER_RPY:
                    yield processResponse(packet)


    def sendDiscover(self, host=None, port=TARGET_PORT):
        '''
        Send a standard HDHomeRun Discover packet

        If host argument is provided, the packet will be sent there.

        If host is falsy, discovery packets will be sent to the IPv4 broadcast address
        and all known IPv6 multicast discovery groups.
        '''
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

        packetBytes = packet.unparse()

        # TODO: Iterate across all network interfaces to send to IPv6 link-local multicast groups
        #       ff02::1 (all hosts) and ff02::176 (HDHR discovery link-local multicast group)
        #       Do the same if we receive a link-local unicast IPv6 target without a scope specified.

        logger.debug("Sending DISCOVER packets...")
        if not host:
            for addr in [
                IPV4_BROADCAST,
                DISCOVER_IPV6_SITELOCAL_MULTICAST,
                DISCOVER_IPV6_LINKLOCAL_MULTICAST,
                IPV6_LINKLOCAL_MULTICAST_ALL_HOSTS,
            ]:
                self.send(packetBytes, addr, port)
        else:
            self.send(packetBytes, host, port)

async def main(host, port):
    client = await DiscoverClient.create(timeoutSeconds=1)

    # Send standard DISCOVER packet
    # Seem sendDiscover() method implementation for how to use DiscoverClient.send() directly
    client.sendDiscover(host, port)

    replies = []
    # Iterate over all replies received as they arrive
    # Note that these should be consolidated to dedup multiple replies from the same device
    async for reply in client.discoverReplies():
        print(reply)

    await client.join()

    logger.info(f"{len(replies)} discover replies received.")

    return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    #logging.basicConfig(level=logging.DEBUG)

    host = os.environ.get('HOST')
    port = int(os.environ.get('PORT', TARGET_PORT))

    asyncio.run(main(host, port))
